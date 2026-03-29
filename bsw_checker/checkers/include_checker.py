"""Include Checker - Verifies include guards, required includes, and multi-header references."""

from collections import defaultdict

from ..parser.file_scanner import ScanResult, ModuleFiles
from ..spec.module_registry import ModuleRegistry, ModuleSpec
from .base_checker import BaseChecker, CheckerReport


class IncludeChecker(BaseChecker):
    name = "include_checker"
    description = "Checks include guards, required includes, and multi-header references"

    def check(self, scan_result: ScanResult) -> CheckerReport:
        self.report = CheckerReport(checker_name=self.name)

        for mod_name, mod_files in scan_result.modules.items():
            mod_spec = self.registry.get_module_spec(self.version, mod_name)

            self._check_include_guards(mod_name, mod_files)
            if mod_spec:
                self._check_required_includes(mod_name, mod_files, mod_spec)
            self._check_multi_header_references(mod_name, mod_files, scan_result)

        self._check_circular_includes(scan_result)
        self._check_cross_module_includes(scan_result)

        return self.report

    def _check_include_guards(self, mod_name: str, mod_files: ModuleFiles):
        for pf in mod_files.parsed_files:
            if not pf.file_path.endswith('.h'):
                continue

            if pf.include_guard is None:
                self._fail(mod_name, "INC-001",
                           f"Missing include guard in {pf.file_path}",
                           f"Header file lacks #ifndef/#define include guard. "
                           f"This can cause multiple inclusion errors leading to "
                           f"'redefinition' compiler errors. "
                           f"AUTOSAR coding guidelines require include guards for all headers.",
                           file_path=pf.file_path,
                           suggestion=f"Add #ifndef {mod_name.upper()}_H / "
                                      f"#define {mod_name.upper()}_H / #endif")
            else:
                # Check guard naming convention
                expected_patterns = [
                    f"{mod_name.upper()}_H",
                    f"{mod_name.upper()}_H_",
                    f"_{mod_name.upper()}_H",
                    f"_{mod_name.upper()}_H_",
                ]
                import os
                stem = os.path.splitext(os.path.basename(pf.file_path))[0]
                expected_patterns.extend([
                    f"{stem.upper()}_H",
                    f"{stem.upper()}_H_",
                ])

                guard = pf.include_guard.ifndef_macro
                if guard not in expected_patterns and not guard.startswith(mod_name.upper()):
                    self._warn(mod_name, "INC-002",
                               f"Non-standard include guard: {guard}",
                               f"Include guard macro '{guard}' does not follow AUTOSAR "
                               f"naming convention. Expected pattern: "
                               f"'{mod_name.upper()}_H' or similar. "
                               f"Non-standard guards may cause confusion in large projects.",
                               file_path=pf.file_path,
                               expected=f"{mod_name.upper()}_H",
                               actual=guard)
                else:
                    # Check ifndef and define match
                    if pf.include_guard.ifndef_macro != pf.include_guard.define_macro:
                        self._fail(mod_name, "INC-003",
                                   f"Include guard mismatch",
                                   f"#ifndef uses '{pf.include_guard.ifndef_macro}' but "
                                   f"#define uses '{pf.include_guard.define_macro}'. "
                                   f"This will break the include guard protection completely.",
                                   file_path=pf.file_path)
                    else:
                        self._pass(mod_name, "INC-001",
                                   f"Include guard OK: {guard}",
                                   file_path=pf.file_path)

    def _check_required_includes(self, mod_name: str, mod_files: ModuleFiles,
                                  mod_spec: ModuleSpec):
        if not mod_spec.required_includes:
            return

        # Collect all includes across module files
        all_includes = set()
        for pf in mod_files.parsed_files:
            for inc in pf.includes:
                all_includes.add(inc.header)

        for req in mod_spec.required_includes:
            if req in all_includes:
                self._pass(mod_name, "INC-004",
                           f"Required include '{req}' found",
                           f"Module {mod_name} correctly includes {req} as required by AUTOSAR SWS.")
            else:
                self._fail(mod_name, "INC-004",
                           f"Missing required include '{req}'",
                           f"Module {mod_name} must include '{req}' according to AUTOSAR SWS. "
                           f"This header provides essential type definitions and macros "
                           f"needed for correct module operation. Missing it may cause "
                           f"compilation errors or type mismatches.",
                           suggestion=f"Add #include \"{req}\" to {mod_name}.h or {mod_name}.c",
                           autosar_ref=f"SWS_{mod_name}")

    def _check_multi_header_references(self, mod_name: str, mod_files: ModuleFiles,
                                        scan_result: ScanResult):
        """Detect cases where a module includes headers from multiple other modules."""
        for pf in mod_files.parsed_files:
            referenced_modules = defaultdict(list)
            for inc in pf.includes:
                header = inc.header
                # Determine which module the included header belongs to
                for other_mod in scan_result.modules:
                    if other_mod == mod_name:
                        continue
                    if (header.startswith(other_mod + '.') or
                        header.startswith(other_mod + '_') or
                        header == other_mod + '.h'):
                        referenced_modules[other_mod].append(inc)

            if len(referenced_modules) >= 3:
                mod_list = ', '.join(sorted(referenced_modules.keys()))
                self._info(mod_name, "INC-005",
                           f"{pf.file_path} references {len(referenced_modules)} modules",
                           f"File includes headers from multiple BSW modules: {mod_list}. "
                           f"High cross-module coupling may indicate architecture issues. "
                           f"Consider if all these dependencies are necessary. "
                           f"In AUTOSAR, each module should primarily interact with its "
                           f"immediate layer neighbors.",
                           file_path=pf.file_path)

            # Report each cross-module reference
            for other_mod, includes in referenced_modules.items():
                for inc in includes:
                    self._info(mod_name, "INC-006",
                               f"{mod_name} -> {other_mod}: includes {inc.header}",
                               f"Cross-module header reference detected: {mod_name} "
                               f"includes {inc.header} from module {other_mod}.",
                               file_path=pf.file_path,
                               line_number=inc.line_number)

    def _check_circular_includes(self, scan_result: ScanResult):
        """Detect potential circular include dependencies between modules."""
        # Build module dependency graph from includes
        deps = defaultdict(set)  # module -> set of modules it includes from

        for mod_name, mod_files in scan_result.modules.items():
            for pf in mod_files.parsed_files:
                for inc in pf.includes:
                    for other_mod in scan_result.modules:
                        if other_mod == mod_name:
                            continue
                        if (inc.header.startswith(other_mod + '.') or
                            inc.header.startswith(other_mod + '_')):
                            deps[mod_name].add(other_mod)

        # Check for direct circular dependencies (A->B and B->A)
        for mod_a, a_deps in deps.items():
            for mod_b in a_deps:
                if mod_a in deps.get(mod_b, set()):
                    self._warn(mod_a, "INC-007",
                               f"Circular include: {mod_a} <-> {mod_b}",
                               f"Modules {mod_a} and {mod_b} include each other's headers. "
                               f"This creates a circular dependency that may cause "
                               f"compilation order issues. In AUTOSAR layered architecture, "
                               f"dependencies should flow downward (upper -> lower layer). "
                               f"Use callback headers (_Cbk.h) for upward references.",
                               suggestion="Use forward declarations or callback headers "
                                          "to break the circular dependency")

    def _check_cross_module_includes(self, scan_result: ScanResult):
        """Check that cross-module includes follow AUTOSAR layering rules."""
        layer_order = {
            "services": 4,
            "com": 3,
            "ecual": 2,
            "mcal": 1,
            "diag": 3,
            "mem": 3,
        }

        for mod_name, mod_files in scan_result.modules.items():
            mod_spec = self.registry.get_module_spec(self.version, mod_name)
            if not mod_spec or not mod_spec.layer:
                continue
            mod_layer = layer_order.get(mod_spec.layer, 0)

            for pf in mod_files.parsed_files:
                for inc in pf.includes:
                    for other_mod in scan_result.modules:
                        if other_mod == mod_name:
                            continue
                        other_spec = self.registry.get_module_spec(self.version, other_mod)
                        if not other_spec or not other_spec.layer:
                            continue

                        if (inc.header.startswith(other_mod + '.') or
                            inc.header == other_mod + '.h'):
                            other_layer = layer_order.get(other_spec.layer, 0)
                            # Lower layer including upper layer directly is suspicious
                            if mod_layer < other_layer and '_Cbk' not in inc.header:
                                self._warn(mod_name, "INC-008",
                                           f"Layer violation: {mod_name}({mod_spec.layer}) "
                                           f"includes {other_mod}({other_spec.layer})",
                                           f"Lower layer module {mod_name} ({mod_spec.layer}, "
                                           f"level {mod_layer}) directly includes header from "
                                           f"upper layer module {other_mod} ({other_spec.layer}, "
                                           f"level {other_layer}). "
                                           f"In AUTOSAR, lower layers should not depend on "
                                           f"upper layers directly. Use callback headers "
                                           f"({other_mod}_Cbk.h) for upward notifications.",
                                           file_path=pf.file_path,
                                           line_number=inc.line_number)
