"""Cross-Module Checker - Verifies inter-module call chains and callback consistency."""

from collections import defaultdict

from ..parser.file_scanner import ScanResult, ModuleFiles
from ..parser.c_parser import FunctionCall, FunctionPointer
from ..spec.module_registry import ModuleRegistry, CallRelation
from .base_checker import BaseChecker, CheckerReport


class CrossModuleChecker(BaseChecker):
    name = "cross_module_checker"
    description = "Checks cross-module call chains, callbacks, and function pointer routing"

    def check(self, scan_result: ScanResult) -> CheckerReport:
        self.report = CheckerReport(checker_name=self.name)

        call_relations = self.registry.get_call_relations(self.version)

        self._check_call_chains(scan_result, call_relations)
        self._check_callback_definitions(scan_result)
        self._check_function_pointer_routing(scan_result)
        self._check_tx_path(scan_result)
        self._check_rx_path(scan_result)

        return self.report

    def _get_all_calls(self, scan_result: ScanResult) -> dict[str, list[FunctionCall]]:
        """Get all function calls grouped by caller module."""
        calls_by_module = defaultdict(list)
        for mod_name, mod_files in scan_result.modules.items():
            for pf in mod_files.parsed_files:
                for call in pf.function_calls:
                    calls_by_module[mod_name].append(call)
        return calls_by_module

    def _get_all_func_ptrs(self, scan_result: ScanResult) -> dict[str, list[FunctionPointer]]:
        """Get all function pointers grouped by module."""
        ptrs_by_module = defaultdict(list)
        for mod_name, mod_files in scan_result.modules.items():
            for pf in mod_files.parsed_files:
                for fp in pf.function_pointers:
                    ptrs_by_module[mod_name].append(fp)
        return ptrs_by_module

    def _get_all_functions(self, scan_result: ScanResult) -> dict[str, str]:
        """Get map of function_name -> module_name for all defined functions."""
        func_map = {}
        for mod_name, mod_files in scan_result.modules.items():
            for pf in mod_files.parsed_files:
                for f in pf.functions:
                    if f.is_definition:
                        func_map[f.name] = mod_name
        return func_map

    def _check_call_chains(self, scan_result: ScanResult, call_relations: list[CallRelation]):
        """Verify that expected cross-module call chains exist."""
        calls_by_module = self._get_all_calls(scan_result)
        ptrs_by_module = self._get_all_func_ptrs(scan_result)

        for relation in call_relations:
            caller_mod = relation.caller_module
            callee_api = relation.callee_api

            if caller_mod not in scan_result.modules:
                continue
            if relation.callee_module not in scan_result.modules:
                continue

            # Check direct calls
            direct_call_found = False
            for call in calls_by_module.get(caller_mod, []):
                if call.callee_func == callee_api:
                    direct_call_found = True
                    break

            # Check function pointer references
            fptr_call_found = False
            for fp in ptrs_by_module.get(caller_mod, []):
                if fp.assigned_func == callee_api:
                    fptr_call_found = True
                    break

            if direct_call_found:
                self._pass(caller_mod, "XMOD-001",
                           f"{caller_mod} -> {callee_api}() [direct call]",
                           f"Cross-module call from {caller_mod} to {callee_api}() "
                           f"confirmed via direct function call. "
                           f"Direction: {relation.direction}. "
                           f"{relation.description}")
            elif fptr_call_found:
                self._pass(caller_mod, "XMOD-001",
                           f"{caller_mod} -> {callee_api}() [via function pointer]",
                           f"Cross-module call from {caller_mod} to {callee_api}() "
                           f"confirmed via function pointer assignment. "
                           f"This is common in PduR routing tables. "
                           f"Direction: {relation.direction}. "
                           f"{relation.description}")
            else:
                # Check if callee_api is referenced anywhere in caller module source
                text_ref_found = False
                for pf in scan_result.modules[caller_mod].parsed_files:
                    if callee_api in pf.raw_content:
                        text_ref_found = True
                        break

                if text_ref_found:
                    self._pass(caller_mod, "XMOD-001",
                               f"{caller_mod} -> {callee_api}() [text reference]",
                               f"Reference to {callee_api}() found in {caller_mod} source "
                               f"(may be via macro, config table, or conditional compilation). "
                               f"{relation.description}")
                else:
                    self._fail(caller_mod, "XMOD-001",
                               f"{caller_mod} does not call {callee_api}()",
                               f"Expected {caller_mod} to call {callee_api}() "
                               f"({relation.description}) but no direct call, function "
                               f"pointer reference, or text reference was found. "
                               f"This breaks the {relation.direction.upper()} communication "
                               f"path: {relation.caller_api} -> {callee_api}. "
                               f"Possible causes: missing configuration, wrong routing "
                               f"table, or the call is conditionally compiled out.",
                               suggestion=f"Ensure {caller_mod} calls {callee_api}() "
                                          f"either directly or through function pointer "
                                          f"in routing/config tables")

    def _check_callback_definitions(self, scan_result: ScanResult):
        """Check that callback functions are defined in the correct modules."""
        callback_owners = {
            "Com_RxIndication": "Com",
            "Com_TxConfirmation": "Com",
            "Com_TriggerTransmit": "Com",
            "PduR_CanIfRxIndication": "PduR",
            "PduR_CanIfTxConfirmation": "PduR",
            "PduR_ComTransmit": "PduR",
            "CanIf_RxIndication": "CanIf",
            "CanIf_TxConfirmation": "CanIf",
            "CanIf_ControllerBusOff": "CanIf",
            "CanSM_ControllerBusOff": "CanSM",
            "CanSM_ControllerModeIndication": "CanSM",
        }

        func_map = self._get_all_functions(scan_result)

        for cb_name, expected_mod in callback_owners.items():
            if expected_mod not in scan_result.modules:
                continue

            if cb_name in func_map:
                actual_mod = func_map[cb_name]
                if actual_mod == expected_mod:
                    self._pass(expected_mod, "XMOD-002",
                               f"Callback {cb_name}() defined in {expected_mod}",
                               f"Callback function {cb_name}() is correctly defined in "
                               f"module {expected_mod} as required by AUTOSAR.")
                else:
                    self._warn(expected_mod, "XMOD-002",
                               f"Callback {cb_name}() in wrong module",
                               f"Callback {cb_name}() is defined in {actual_mod} but "
                               f"should be in {expected_mod} according to AUTOSAR SWS. "
                               f"The callback belongs to the upper layer module that "
                               f"receives the notification.",
                               expected=expected_mod,
                               actual=actual_mod)
            else:
                # Only warn if the expected module exists
                self._warn(expected_mod, "XMOD-002",
                           f"Callback {cb_name}() not found",
                           f"Callback function {cb_name}() is expected in module "
                           f"{expected_mod} but was not found. This callback is needed "
                           f"for the cross-module notification mechanism.",
                           suggestion=f"Define {cb_name}() in {expected_mod}.c")

    def _check_function_pointer_routing(self, scan_result: ScanResult):
        """Analyze function pointer tables for routing consistency."""
        ptrs_by_module = self._get_all_func_ptrs(scan_result)
        func_map = self._get_all_functions(scan_result)

        for mod_name, ptrs in ptrs_by_module.items():
            for fp in ptrs:
                if not fp.assigned_func:
                    continue

                # Check if the assigned function actually exists
                if fp.assigned_func in func_map:
                    target_mod = func_map[fp.assigned_func]
                    self._info(mod_name, "XMOD-003",
                               f"Function pointer: {fp.name} -> {fp.assigned_func}() [{target_mod}]",
                               f"In module {mod_name}, function pointer '{fp.name}' "
                               f"references {fp.assigned_func}() from module {target_mod}. "
                               f"This is a valid function pointer routing entry.",
                               file_path=fp.file_path,
                               line_number=fp.line_number)
                else:
                    if fp.assigned_func.startswith(('NULL', '0', '(')):
                        continue
                    self._warn(mod_name, "XMOD-003",
                               f"Function pointer: {fp.name} -> {fp.assigned_func}() [NOT FOUND]",
                               f"Function pointer '{fp.name}' in {mod_name} references "
                               f"{fp.assigned_func}() but this function was not found "
                               f"in any scanned module. It may be defined in an unscanned "
                               f"file, or this is a configuration error.",
                               file_path=fp.file_path,
                               line_number=fp.line_number,
                               suggestion=f"Verify that {fp.assigned_func}() is implemented")

    def _check_tx_path(self, scan_result: ScanResult):
        """Check complete TX communication path."""
        tx_chain = [
            ("Com", "PduR_ComTransmit"),
            ("PduR", "CanIf_Transmit"),
            ("CanIf", "Can_Write"),
        ]

        present_modules = set(scan_result.modules.keys())
        chain_modules = {"Com", "PduR", "CanIf", "Can"}

        if not chain_modules.issubset(present_modules):
            missing = chain_modules - present_modules
            self._info("System", "XMOD-004",
                       f"TX chain incomplete: missing modules {missing}",
                       f"Cannot verify full TX path (Com->PduR->CanIf->Can) "
                       f"because modules {missing} are not present in the scan.")
            return

        calls_by_module = self._get_all_calls(scan_result)
        chain_ok = True

        for caller_mod, callee_func in tx_chain:
            found = any(c.callee_func == callee_func
                        for c in calls_by_module.get(caller_mod, []))
            if not found:
                # Also check source text
                found = any(callee_func in pf.raw_content
                            for pf in scan_result.modules[caller_mod].parsed_files)

            if not found:
                chain_ok = False

        if chain_ok:
            self._pass("System", "XMOD-004",
                       "TX path: Com -> PduR -> CanIf -> Can complete",
                       "Full CAN transmission path verified: "
                       "Com calls PduR_ComTransmit, PduR calls CanIf_Transmit, "
                       "CanIf calls Can_Write. All links in the TX chain are present.")
        else:
            self._fail("System", "XMOD-004",
                       "TX path incomplete",
                       "The CAN transmission path (Com -> PduR -> CanIf -> Can) "
                       "has missing links. See individual XMOD-001 results for details.",
                       suggestion="Verify PduR routing table configuration and "
                                  "ensure all modules are properly configured")

    def _check_rx_path(self, scan_result: ScanResult):
        """Check complete RX communication path."""
        rx_chain = [
            ("CanIf", "PduR_CanIfRxIndication"),
            ("PduR", "Com_RxIndication"),
        ]

        present_modules = set(scan_result.modules.keys())
        needed = {"CanIf", "PduR", "Com"}

        if not needed.issubset(present_modules):
            missing = needed - present_modules
            self._info("System", "XMOD-005",
                       f"RX chain incomplete: missing modules {missing}",
                       f"Cannot verify full RX path because modules {missing} are not present.")
            return

        calls_by_module = self._get_all_calls(scan_result)
        chain_ok = True

        for caller_mod, callee_func in rx_chain:
            found = any(c.callee_func == callee_func
                        for c in calls_by_module.get(caller_mod, []))
            if not found:
                found = any(callee_func in pf.raw_content
                            for pf in scan_result.modules[caller_mod].parsed_files)
            if not found:
                chain_ok = False

        if chain_ok:
            self._pass("System", "XMOD-005",
                       "RX path: Can -> CanIf -> PduR -> Com complete",
                       "Full CAN reception path verified: "
                       "CanIf calls PduR_CanIfRxIndication, PduR calls Com_RxIndication. "
                       "All links in the RX callback chain are present.")
        else:
            self._fail("System", "XMOD-005",
                       "RX path incomplete",
                       "The CAN reception callback path has missing links. "
                       "See individual XMOD-001 results for details.",
                       suggestion="Verify callback configurations in PduR and CanIf")
