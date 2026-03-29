"""SchM Exclusive Area Checker - Validates SchM_Enter/Exit pairing and consistency."""

import re
from collections import defaultdict

from ..parser.file_scanner import ScanResult
from .base_checker import BaseChecker, CheckerReport


# Pattern: SchM_Enter_<Module>_<EA_NAME>() or SchM_Exit_<Module>_<EA_NAME>()
_RE_SCHM_CALL = re.compile(
    r'\b(SchM_(?:Enter|Exit))_(\w+?)_(\w+?)\s*\(\s*\)'
)

# Pattern: #define SchM_Enter_<Module>_<EA>() or macro definition
_RE_SCHM_DEFINE = re.compile(
    r'#\s*define\s+(SchM_(?:Enter|Exit)_(\w+?)_(\w+?))\s*\('
)


class SchmChecker(BaseChecker):
    name = "schm_checker"
    description = "Checks SchM exclusive area Enter/Exit pairing and consistency"

    def check(self, scan_result: ScanResult) -> CheckerReport:
        self.report = CheckerReport(checker_name=self.name)

        ea_usage = self._collect_ea_usage(scan_result)
        ea_defines = self._collect_ea_defines(scan_result)

        self._check_enter_exit_pairing(ea_usage)
        self._check_ea_defined(ea_usage, ea_defines)
        self._check_ea_naming_convention(ea_usage)
        self._check_cross_module_ea(ea_usage, scan_result)

        return self.report

    def _collect_ea_usage(self, scan_result: ScanResult) -> dict:
        """Collect all SchM_Enter/Exit calls grouped by module and EA name."""
        # ea_usage[module][ea_name] = {"enter": [(file, line)], "exit": [(file, line)]}
        ea_usage = defaultdict(lambda: defaultdict(lambda: {"enter": [], "exit": []}))

        for mod_name, mod_files in scan_result.modules.items():
            for pf in mod_files.parsed_files:
                for m in _RE_SCHM_CALL.finditer(pf.raw_content):
                    action = "enter" if "Enter" in m.group(1) else "exit"
                    target_module = m.group(2)
                    ea_name = m.group(3)
                    line_no = pf.raw_content[:m.start()].count('\n') + 1
                    ea_usage[target_module][ea_name][action].append(
                        (pf.file_path, line_no, mod_name)
                    )

        return ea_usage

    def _collect_ea_defines(self, scan_result: ScanResult) -> set:
        """Collect all SchM_Enter/Exit macro definitions."""
        defines = set()
        for mod_name, mod_files in scan_result.modules.items():
            for pf in mod_files.parsed_files:
                for m in _RE_SCHM_DEFINE.finditer(pf.raw_content):
                    defines.add(m.group(1))
        return defines

    def _check_enter_exit_pairing(self, ea_usage: dict):
        """Check that every SchM_Enter has a matching SchM_Exit in the same file."""
        for target_module, eas in ea_usage.items():
            for ea_name, actions in eas.items():
                enter_files = defaultdict(list)
                exit_files = defaultdict(list)

                for fpath, line, caller in actions["enter"]:
                    enter_files[fpath].append((line, caller))
                for fpath, line, caller in actions["exit"]:
                    exit_files[fpath].append((line, caller))

                # Check per file: enter count should equal exit count
                all_files = set(enter_files.keys()) | set(exit_files.keys())
                for fpath in all_files:
                    enter_count = len(enter_files.get(fpath, []))
                    exit_count = len(exit_files.get(fpath, []))

                    ea_full = f"SchM_{target_module}_{ea_name}"

                    if enter_count > 0 and exit_count == 0:
                        self._fail(target_module, "SCHM-001",
                                   f"Enter without Exit: {ea_full}",
                                   f"File has {enter_count} SchM_Enter_{target_module}_{ea_name}() "
                                   f"call(s) but no matching SchM_Exit_{target_module}_{ea_name}(). "
                                   f"This means the exclusive area is entered but never exited, "
                                   f"causing permanent interrupt lock or task blocking. "
                                   f"Every Enter MUST have a corresponding Exit on all code paths.",
                                   file_path=fpath,
                                   line_number=enter_files[fpath][0][0],
                                   suggestion=f"Add SchM_Exit_{target_module}_{ea_name}() "
                                              f"after the critical section")

                    elif exit_count > 0 and enter_count == 0:
                        self._fail(target_module, "SCHM-001",
                                   f"Exit without Enter: {ea_full}",
                                   f"File has {exit_count} SchM_Exit_{target_module}_{ea_name}() "
                                   f"call(s) but no matching SchM_Enter_{target_module}_{ea_name}(). "
                                   f"Exiting an exclusive area that was never entered causes "
                                   f"undefined OS behavior (double unlock).",
                                   file_path=fpath,
                                   line_number=exit_files[fpath][0][0])

                    elif enter_count != exit_count:
                        self._warn(target_module, "SCHM-002",
                                   f"Enter/Exit count mismatch: {ea_full} ({enter_count} vs {exit_count})",
                                   f"In {fpath}: {enter_count} Enter call(s) vs {exit_count} Exit call(s) "
                                   f"for {ea_full}. Mismatched counts may indicate a missing Exit "
                                   f"on an error return path, causing intermittent lock-ups. "
                                   f"Check all early return statements and error handling paths.",
                                   file_path=fpath,
                                   suggestion="Ensure every Enter has exactly one Exit on all code paths")

                    elif enter_count > 0:
                        self._pass(target_module, "SCHM-001",
                                   f"{ea_full}: {enter_count} Enter/{exit_count} Exit paired OK",
                                   file_path=fpath)

    def _check_ea_defined(self, ea_usage: dict, ea_defines: set):
        """Check that used exclusive areas are actually defined as macros."""
        for target_module, eas in ea_usage.items():
            for ea_name, actions in eas.items():
                enter_macro = f"SchM_Enter_{target_module}_{ea_name}"
                exit_macro = f"SchM_Exit_{target_module}_{ea_name}"

                if enter_macro not in ea_defines and actions["enter"]:
                    first = actions["enter"][0]
                    self._warn(target_module, "SCHM-003",
                               f"EA macro not defined: {enter_macro}",
                               f"SchM_Enter_{target_module}_{ea_name}() is called but "
                               f"not found as a #define macro in SchM.h or SchM_{target_module}.h. "
                               f"If this macro is not defined, the exclusive area call "
                               f"will expand to nothing, providing no protection. "
                               f"It could also cause a compilation error.",
                               file_path=first[0],
                               line_number=first[1],
                               suggestion=f"Define {enter_macro}() in SchM.h or SchM_{target_module}.h")

    def _check_ea_naming_convention(self, ea_usage: dict):
        """Check exclusive area naming follows AUTOSAR convention."""
        # AUTOSAR convention: SchM_Enter_<Module>_<MODULE>_EXCLUSIVE_AREA_<N>
        ea_name_pattern = re.compile(r'^[A-Z][A-Z0-9_]*EXCLUSIVE_AREA_\d+$')

        for target_module, eas in ea_usage.items():
            for ea_name in eas:
                if not ea_name_pattern.match(ea_name):
                    first_use = (eas[ea_name]["enter"] + eas[ea_name]["exit"])
                    if first_use:
                        self._info(target_module, "SCHM-004",
                                   f"Non-standard EA name: {ea_name}",
                                   f"Exclusive area '{ea_name}' does not follow the AUTOSAR "
                                   f"naming convention '<MODULE>_EXCLUSIVE_AREA_<N>'. "
                                   f"Expected pattern like '{target_module.upper()}_EXCLUSIVE_AREA_0'. "
                                   f"Non-standard names are allowed but may cause confusion.",
                                   file_path=first_use[0][0],
                                   line_number=first_use[0][1])
                else:
                    self._pass(target_module, "SCHM-004",
                               f"EA name OK: {ea_name}")

    def _check_cross_module_ea(self, ea_usage: dict, scan_result: ScanResult):
        """Detect modules using another module's exclusive areas."""
        for target_module, eas in ea_usage.items():
            for ea_name, actions in eas.items():
                all_callers = set()
                for _, _, caller_mod in actions["enter"] + actions["exit"]:
                    all_callers.add(caller_mod)

                for caller in all_callers:
                    if caller != target_module and target_module in scan_result.modules:
                        self._warn(caller, "SCHM-005",
                                   f"{caller} uses {target_module}'s exclusive area {ea_name}",
                                   f"Module {caller} calls SchM_Enter/Exit_{target_module}_{ea_name}(). "
                                   f"Using another module's exclusive area breaks encapsulation. "
                                   f"Each module should only use its own exclusive areas. "
                                   f"If cross-module protection is needed, use an API call instead.",
                                   suggestion=f"Refactor to use {caller}'s own exclusive area "
                                              f"or use {target_module}'s public API")
