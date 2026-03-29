"""Function Pointer Checker - Analyzes function pointer usage for routing validation."""

from collections import defaultdict

from ..parser.file_scanner import ScanResult
from ..parser.c_parser import FunctionPointer
from .base_checker import BaseChecker, CheckerReport


class FunctionPointerChecker(BaseChecker):
    name = "func_ptr_checker"
    description = "Analyzes function pointer declarations, assignments, and routing tables"

    def check(self, scan_result: ScanResult) -> CheckerReport:
        self.report = CheckerReport(checker_name=self.name)

        self._analyze_routing_tables(scan_result)
        self._check_callback_pointers(scan_result)
        self._check_null_pointers(scan_result)
        self._build_call_graph_from_ptrs(scan_result)

        return self.report

    def _analyze_routing_tables(self, scan_result: ScanResult):
        """Analyze PduR/CanIf routing tables for function pointer entries."""
        routing_modules = {'PduR', 'CanIf', 'BswM', 'EcuM'}

        for mod_name in routing_modules:
            if mod_name not in scan_result.modules:
                continue

            mod_files = scan_result.modules[mod_name]
            for pf in mod_files.parsed_files:
                if not pf.function_pointers:
                    continue

                # Group function pointers by table
                tables = defaultdict(list)
                for fp in pf.function_pointers:
                    if 'entry' in fp.name or '[]' in fp.name:
                        table_name = fp.name.split('[')[0] if '[' in fp.name else fp.name
                        tables[table_name].append(fp)
                    else:
                        tables['_standalone'].append(fp)

                for table_name, ptrs in tables.items():
                    if table_name == '_standalone':
                        continue

                    assigned_funcs = [fp.assigned_func for fp in ptrs if fp.assigned_func]
                    if assigned_funcs:
                        self._info(mod_name, "FPTR-001",
                                   f"Routing table '{table_name}' has {len(assigned_funcs)} entries",
                                   f"Function pointer table '{table_name}' in {mod_name} "
                                   f"references: {', '.join(assigned_funcs[:10])}"
                                   f"{'...' if len(assigned_funcs) > 10 else ''}. "
                                   f"These are the target functions for PDU routing.",
                                   file_path=pf.file_path)

                        # Verify referenced functions exist
                        all_funcs = self._get_all_defined_functions(scan_result)
                        for func_name in assigned_funcs:
                            if func_name in all_funcs:
                                self._pass(mod_name, "FPTR-002",
                                           f"Routing target {func_name}() exists",
                                           f"Function pointer in table '{table_name}' "
                                           f"references {func_name}() which is defined in "
                                           f"module {all_funcs[func_name]}.",
                                           file_path=pf.file_path)
                            elif not func_name.startswith(('NULL', '0')):
                                self._fail(mod_name, "FPTR-002",
                                           f"Routing target {func_name}() not found",
                                           f"Function pointer in table '{table_name}' "
                                           f"references {func_name}() but this function "
                                           f"is not defined in any scanned module. "
                                           f"This will cause a linker error or runtime crash.",
                                           file_path=pf.file_path,
                                           suggestion=f"Ensure {func_name}() is implemented "
                                                      f"or remove the routing entry")

    def _check_callback_pointers(self, scan_result: ScanResult):
        """Check function pointers that serve as callbacks between modules."""
        callback_patterns = {
            'RxIndication': 'Reception callback',
            'TxConfirmation': 'Transmission confirmation callback',
            'TriggerTransmit': 'Trigger transmit callback',
            'StartOfReception': 'TP start of reception callback',
            'CopyRxData': 'TP copy Rx data callback',
            'CopyTxData': 'TP copy Tx data callback',
        }

        for mod_name, mod_files in scan_result.modules.items():
            for pf in mod_files.parsed_files:
                for fp in pf.function_pointers:
                    if not fp.assigned_func:
                        continue

                    for pattern, desc in callback_patterns.items():
                        if pattern in fp.assigned_func:
                            self._info(mod_name, "FPTR-003",
                                       f"Callback pointer: {fp.name} -> {fp.assigned_func}()",
                                       f"{desc}: Function pointer '{fp.name}' in {mod_name} "
                                       f"is assigned to callback {fp.assigned_func}(). "
                                       f"This establishes the inter-module notification path.",
                                       file_path=fp.file_path,
                                       line_number=fp.line_number)
                            break

    def _check_null_pointers(self, scan_result: ScanResult):
        """Detect potentially dangerous NULL function pointers in routing tables."""
        for mod_name, mod_files in scan_result.modules.items():
            for pf in mod_files.parsed_files:
                null_count = 0
                total_count = 0

                for fp in pf.function_pointers:
                    if 'entry' in fp.name or '[]' in fp.name:
                        total_count += 1
                        if fp.assigned_func in ('NULL', 'NULL_PTR', '0', '((void*)0)', ''):
                            null_count += 1

                if total_count > 0 and null_count > 0:
                    ratio = null_count / total_count * 100
                    if ratio > 50:
                        self._warn(mod_name, "FPTR-004",
                                   f"High NULL ratio in routing table: {null_count}/{total_count}",
                                   f"{null_count} out of {total_count} function pointer entries "
                                   f"({ratio:.0f}%) are NULL in {pf.file_path}. "
                                   f"Many NULL entries in a routing table may indicate "
                                   f"incomplete configuration. NULL pointers will cause "
                                   f"crashes if called at runtime without NULL checks.",
                                   file_path=pf.file_path,
                                   suggestion="Review routing table configuration for "
                                              "missing function pointer assignments")

    def _build_call_graph_from_ptrs(self, scan_result: ScanResult):
        """Build and report the cross-module call graph derived from function pointers."""
        all_funcs = self._get_all_defined_functions(scan_result)
        edges = []  # (from_module, to_module, via_func)

        for mod_name, mod_files in scan_result.modules.items():
            for pf in mod_files.parsed_files:
                for fp in pf.function_pointers:
                    if fp.assigned_func and fp.assigned_func in all_funcs:
                        target_mod = all_funcs[fp.assigned_func]
                        if target_mod != mod_name:
                            edges.append((mod_name, target_mod, fp.assigned_func))

        if edges:
            # Report unique edges
            seen = set()
            for from_mod, to_mod, func in edges:
                key = (from_mod, to_mod, func)
                if key not in seen:
                    seen.add(key)
                    self._info("System", "FPTR-005",
                               f"FPtr link: {from_mod} -> {to_mod} via {func}()",
                               f"Function pointer routing: {from_mod} references "
                               f"{func}() from {to_mod}. This establishes a "
                               f"runtime call path between these modules.")

            # Summary
            module_links = defaultdict(set)
            for from_mod, to_mod, _ in edges:
                module_links[from_mod].add(to_mod)

            summary_parts = []
            for from_mod, targets in sorted(module_links.items()):
                summary_parts.append(f"{from_mod} -> {', '.join(sorted(targets))}")

            self._info("System", "FPTR-006",
                       f"Function pointer call graph: {len(seen)} unique links",
                       f"Cross-module routing via function pointers:\n" +
                       "\n".join(f"  {s}" for s in summary_parts))

    def _get_all_defined_functions(self, scan_result: ScanResult) -> dict[str, str]:
        """Get map of function_name -> module_name."""
        func_map = {}
        for mod_name, mod_files in scan_result.modules.items():
            for pf in mod_files.parsed_files:
                for f in pf.functions:
                    if f.is_definition:
                        func_map[f.name] = mod_name
        return func_map
