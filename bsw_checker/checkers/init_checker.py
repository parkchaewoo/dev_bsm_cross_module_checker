"""Init Checker - Verifies initialization order and config structure consistency."""

import re
from collections import defaultdict

from ..parser.file_scanner import ScanResult
from ..spec.module_registry import ModuleRegistry
from .base_checker import BaseChecker, CheckerReport


class InitChecker(BaseChecker):
    name = "init_checker"
    description = "Checks BSW module initialization order and config structure"

    def check(self, scan_result: ScanResult) -> CheckerReport:
        self.report = CheckerReport(checker_name=self.name)

        self._check_init_calls_in_ecum(scan_result)
        self._check_init_order(scan_result)
        self._check_init_config_params(scan_result)
        self._check_init_dependencies(scan_result)
        self._check_double_init(scan_result)
        self._check_deinit_exists(scan_result)

        return self.report

    def _check_init_calls_in_ecum(self, scan_result: ScanResult):
        """Check that EcuM/BswM calls Init for all present modules."""
        init_callers = []
        for mod_name in ('EcuM', 'BswM'):
            if mod_name in scan_result.modules:
                init_callers.append(mod_name)

        if not init_callers:
            self._warn("System", "INIT-001",
                       "No EcuM or BswM module found",
                       "Neither EcuM nor BswM was found in the scanned modules. "
                       "Without a state manager module, BSW initialization order "
                       "cannot be verified. The ECU State Manager is responsible "
                       "for coordinating the initialization of all BSW modules.",
                       suggestion="Include EcuM or BswM source files in the scan path")
            return

        # Collect all Init calls from EcuM/BswM
        init_calls_found = set()
        init_call_locations = {}
        for caller_mod in init_callers:
            for pf in scan_result.modules[caller_mod].parsed_files:
                for call in pf.function_calls:
                    if call.callee_func.endswith('_Init') or call.callee_func.endswith('_PreInit'):
                        init_calls_found.add(call.callee_func)
                        init_call_locations[call.callee_func] = (pf.file_path, call.line_number)

                # Also search raw content for Init calls (may be in macros/conditions)
                init_pattern = re.compile(r'\b(\w+_(?:Init|PreInit))\s*\(')
                for m in init_pattern.finditer(pf.raw_content):
                    func_name = m.group(1)
                    if func_name not in init_calls_found:
                        init_calls_found.add(func_name)
                        line_no = pf.raw_content[:m.start()].count('\n') + 1
                        init_call_locations[func_name] = (pf.file_path, line_no)

        # Check each present module has its Init called
        for mod_name in scan_result.modules:
            if mod_name in init_callers:
                continue  # EcuM/BswM don't init themselves this way

            expected_init = f"{mod_name}_Init"
            if expected_init in init_calls_found:
                loc = init_call_locations[expected_init]
                self._pass(mod_name, "INIT-002",
                           f"{expected_init}() called by init manager",
                           f"{expected_init}() is called in {loc[0]}:{loc[1]}. "
                           f"Module initialization is properly managed.",
                           file_path=loc[0],
                           line_number=loc[1])
            else:
                # Check for PreInit
                pre_init = f"{mod_name}_PreInit"
                if pre_init in init_calls_found:
                    self._pass(mod_name, "INIT-002",
                               f"{pre_init}() called by init manager",
                               f"PreInit variant found for {mod_name}.")
                else:
                    self._warn(mod_name, "INIT-002",
                               f"{expected_init}() not found in EcuM/BswM",
                               f"Module {mod_name} is present but {expected_init}() "
                               f"was not found in EcuM or BswM initialization code. "
                               f"This module may not be initialized at startup, "
                               f"causing undefined behavior when its APIs are called.",
                               suggestion=f"Add {expected_init}() call to EcuM startup sequence")

    def _check_init_order(self, scan_result: ScanResult):
        """Check that initialization order follows AUTOSAR recommendations."""
        recommended_order = self.registry.get_init_order(self.default_version)
        if not recommended_order:
            return

        # Find actual init order from EcuM/BswM source
        actual_order = []
        for mod_name in ('EcuM', 'BswM'):
            if mod_name not in scan_result.modules:
                continue
            for pf in scan_result.modules[mod_name].parsed_files:
                if not pf.file_path.endswith('.c'):
                    continue
                # Extract Init calls in order from source
                init_pattern = re.compile(r'\b(\w+)_Init\s*\(')
                for m in init_pattern.finditer(pf.raw_content):
                    mod = m.group(1)
                    # Skip the init manager itself and function definitions
                    if mod in ('EcuM', 'BswM'):
                        continue
                    if mod not in actual_order and mod in set(scan_result.modules.keys()):
                        actual_order.append(mod)

        if len(actual_order) < 2:
            self._info("System", "INIT-003",
                       "Cannot determine init order",
                       "Found fewer than 2 Init calls in sequence. "
                       "Cannot verify initialization order.")
            return

        # Check order violations
        violations = []
        for i, mod_a in enumerate(actual_order):
            for j, mod_b in enumerate(actual_order):
                if j <= i:
                    continue
                # mod_a is initialized before mod_b in actual code
                # Check if this violates recommended order
                if mod_a in recommended_order and mod_b in recommended_order:
                    rec_a = recommended_order.index(mod_a)
                    rec_b = recommended_order.index(mod_b)
                    if rec_a > rec_b:
                        violations.append((mod_b, mod_a))

        if violations:
            for earlier, later in violations:
                self._fail("System", "INIT-003",
                           f"Init order violation: {later} before {earlier}",
                           f"Module {later} is initialized before {earlier}, but "
                           f"AUTOSAR recommends initializing {earlier} first. "
                           f"Initialization order matters because {later} may depend "
                           f"on services provided by {earlier}. Incorrect order can "
                           f"cause null pointer access, uninitialized data usage, "
                           f"or DET errors during startup.",
                           suggestion=f"Move {earlier}_Init() before {later}_Init() "
                                      f"in the EcuM startup sequence")
        else:
            self._pass("System", "INIT-003",
                       "Initialization order follows AUTOSAR recommendation",
                       f"Detected init order: {' -> '.join(actual_order)}. "
                       f"This follows the recommended layer-by-layer initialization.")

    def _check_init_config_params(self, scan_result: ScanResult):
        """Check that Init functions receive proper config pointers."""
        for mod_name, mod_files in scan_result.modules.items():
            mod_spec = self.registry.get_module_spec(self.get_version(mod_name), mod_name)
            if not mod_spec or not mod_spec.config_type:
                continue

            init_name = f"{mod_name}_Init"

            # Check in EcuM/BswM if Init is called with a config parameter
            for caller_mod in ('EcuM', 'BswM'):
                if caller_mod not in scan_result.modules:
                    continue
                for pf in scan_result.modules[caller_mod].parsed_files:
                    for call in pf.function_calls:
                        if call.callee_func == init_name:
                            if call.arguments.strip() in ('', 'NULL', 'NULL_PTR', '((void*)0)'):
                                self._warn(mod_name, "INIT-004",
                                           f"{init_name}() called with NULL config",
                                           f"{init_name}() is called with NULL/empty config "
                                           f"in {pf.file_path}:{call.line_number}. "
                                           f"Module {mod_name} expects a valid "
                                           f"'{mod_spec.config_type}*' pointer for "
                                           f"post-build configuration.",
                                           file_path=pf.file_path,
                                           line_number=call.line_number)
                            else:
                                self._pass(mod_name, "INIT-004",
                                           f"{init_name}() receives config: {call.arguments}",
                                           f"Config parameter passed correctly.",
                                           file_path=pf.file_path,
                                           line_number=call.line_number)

    def _check_init_dependencies(self, scan_result: ScanResult):
        """Check that module init dependencies are satisfied."""
        for mod_name in scan_result.modules:
            mod_spec = self.registry.get_module_spec(self.get_version(mod_name), mod_name)
            if not mod_spec:
                continue

            for dep in mod_spec.init_dependencies:
                if dep in scan_result.modules:
                    self._pass(mod_name, "INIT-005",
                               f"Dependency '{dep}' present",
                               f"Module {mod_name} depends on {dep} for initialization, "
                               f"and {dep} is present in the scanned modules.")
                else:
                    self._warn(mod_name, "INIT-005",
                               f"Dependency '{dep}' not found",
                               f"Module {mod_name} depends on {dep} being initialized first, "
                               f"but {dep} was not found in the scanned modules. "
                               f"This may cause initialization failures.",
                               suggestion=f"Ensure {dep} source files are included in the scan path")

    def _check_double_init(self, scan_result: ScanResult):
        """Detect if a module's Init is called more than once in EcuM/BswM."""
        init_counts = defaultdict(int)
        for caller_mod in ('EcuM', 'BswM'):
            if caller_mod not in scan_result.modules:
                continue
            for pf in scan_result.modules[caller_mod].parsed_files:
                if not pf.file_path.endswith('.c'):
                    continue
                init_pattern = re.compile(r'\b(\w+)_Init\s*\(')
                for m in init_pattern.finditer(pf.raw_content):
                    mod = m.group(1)
                    if mod not in ('EcuM', 'BswM'):
                        init_counts[mod] += 1

        for mod, count in init_counts.items():
            if count > 1:
                self._warn(mod, "INIT-006",
                           f"{mod}_Init() called {count} times",
                           f"Module {mod}_Init() is called {count} times in "
                           f"EcuM/BswM startup code. Double initialization can "
                           f"cause loss of runtime state, reset of communication "
                           f"buffers, or NvM data corruption. "
                           f"Each module should be initialized exactly once.",
                           suggestion=f"Remove duplicate {mod}_Init() call")

    def _check_deinit_exists(self, scan_result: ScanResult):
        """Check that modules with Init also have DeInit for proper shutdown."""
        important_modules = {'Com', 'PduR', 'CanIf', 'ComM', 'Dcm', 'Dem', 'NvM'}
        for mod_name, mod_files in scan_result.modules.items():
            if mod_name not in important_modules:
                continue
            has_init = False
            has_deinit = False
            for pf in mod_files.parsed_files:
                for func in pf.functions:
                    if func.name == f'{mod_name}_Init':
                        has_init = True
                    if func.name in (f'{mod_name}_DeInit', f'{mod_name}_Shutdown'):
                        has_deinit = True

            if has_init and not has_deinit:
                self._info(mod_name, "INIT-007",
                           f"{mod_name} has Init but no DeInit/Shutdown",
                           f"Module {mod_name} has {mod_name}_Init() but no "
                           f"{mod_name}_DeInit() or {mod_name}_Shutdown(). "
                           f"Without DeInit, the module cannot properly release "
                           f"resources during ECU shutdown or sleep transition.")
