"""Det Checker - Verifies DET error reporting consistency."""

import re
from collections import defaultdict

from ..parser.file_scanner import ScanResult
from ..spec.module_registry import ModuleRegistry
from .base_checker import BaseChecker, CheckerReport


class DetChecker(BaseChecker):
    name = "det_checker"
    description = "Checks DET error reporting: Module ID, API ID, Error ID"

    def check(self, scan_result: ScanResult) -> CheckerReport:
        self.report = CheckerReport(checker_name=self.name)

        self._check_det_report_calls(scan_result)
        self._check_module_ids(scan_result)
        self._check_error_defines(scan_result)

        return self.report

    def _check_det_report_calls(self, scan_result: ScanResult):
        """Check that modules call Det_ReportError with correct parameters."""
        det_call_pattern = re.compile(
            r'Det_Report(?:Error|RuntimeError|TransientFault)\s*\(\s*'
            r'([^,]+)\s*,\s*'   # Module ID
            r'([^,]+)\s*,\s*'   # Instance ID / API Service ID
            r'([^,]+)\s*,\s*'   # API ID / Error ID
            r'([^)]+)\s*\)',    # Error ID / extra
            re.DOTALL
        )

        # Also handle 4-param variant
        det_call_pattern_4 = re.compile(
            r'Det_Report(?:Error|RuntimeError)\s*\(\s*'
            r'(\w+)\s*,\s*'
            r'(\w+)\s*,\s*'
            r'(\w+)\s*,\s*'
            r'(\w+)\s*\)',
        )

        for mod_name, mod_files in scan_result.modules.items():
            mod_spec = self.registry.get_module_spec(self.version, mod_name)
            det_calls_found = False

            for pf in mod_files.parsed_files:
                # Search in raw content for Det calls
                for m in det_call_pattern_4.finditer(pf.raw_content):
                    det_calls_found = True
                    module_id_arg = m.group(1)
                    instance_id_arg = m.group(2)
                    api_id_arg = m.group(3)
                    error_id_arg = m.group(4)

                    line_no = pf.raw_content[:m.start()].count('\n') + 1

                    # Check module ID matches expected
                    if mod_spec:
                        expected_id_name = f"{mod_name.upper()}_MODULE_ID"
                        alt_id_names = [
                            f"{mod_name.upper()}_MODULE_ID",
                            f"{mod_name}_MODULE_ID",
                            str(mod_spec.module_id),
                            f"0x{mod_spec.module_id:02X}",
                            f"0x{mod_spec.module_id:04X}",
                            f"{mod_spec.module_id}U",
                            f"({mod_spec.module_id}U)",
                        ]

                        if module_id_arg.strip() not in alt_id_names and \
                           not module_id_arg.strip().startswith(mod_name.upper()):
                            self._warn(mod_name, "DET-001",
                                       f"Unexpected Module ID in Det call: {module_id_arg}",
                                       f"Det_ReportError in {mod_name} uses Module ID "
                                       f"'{module_id_arg.strip()}' but expected "
                                       f"'{expected_id_name}' (value {mod_spec.module_id}). "
                                       f"Using wrong Module ID makes DET error logs "
                                       f"misleading and hard to trace.",
                                       file_path=pf.file_path,
                                       line_number=line_no,
                                       expected=expected_id_name,
                                       actual=module_id_arg.strip())
                        else:
                            self._pass(mod_name, "DET-001",
                                       f"Module ID correct in Det call",
                                       file_path=pf.file_path,
                                       line_number=line_no)

                    # Check error ID is a known error for this module
                    if mod_spec and mod_spec.det_errors:
                        known_errors = {e.name for e in mod_spec.det_errors}
                        error_arg = error_id_arg.strip()
                        if (error_arg not in known_errors and
                            not error_arg.startswith(mod_name.upper()) and
                            not error_arg.isdigit() and
                            not error_arg.startswith('0x')):
                            self._warn(mod_name, "DET-002",
                                       f"Unknown error ID: {error_arg}",
                                       f"Error ID '{error_arg}' used in Det_ReportError "
                                       f"is not in the known AUTOSAR error list for {mod_name}. "
                                       f"Known errors: {', '.join(sorted(known_errors))}. "
                                       f"This may be a vendor-specific error or a typo.",
                                       file_path=pf.file_path,
                                       line_number=line_no)

            # Check if Det is used at all when it should be
            if mod_spec and mod_spec.det_errors and not det_calls_found:
                # Check if module has DET_DEV_ERROR_DETECT enabled
                has_det_config = False
                for pf in mod_files.parsed_files:
                    if f'{mod_name.upper()}_DEV_ERROR_DETECT' in pf.raw_content:
                        has_det_config = True
                        break

                if has_det_config:
                    self._info(mod_name, "DET-003",
                               f"DET config present but no Det_ReportError calls found",
                               f"Module {mod_name} has {mod_name.upper()}_DEV_ERROR_DETECT "
                               f"configuration but no Det_ReportError() calls were found. "
                               f"DET may be disabled (STD_OFF) or calls may be "
                               f"conditionally compiled out.")
                else:
                    self._warn(mod_name, "DET-003",
                               f"No DET error reporting in {mod_name}",
                               f"Module {mod_name} has {len(mod_spec.det_errors)} defined "
                               f"DET errors in AUTOSAR SWS but no Det_ReportError() calls "
                               f"and no {mod_name.upper()}_DEV_ERROR_DETECT configuration. "
                               f"Development error detection is important for debugging.",
                               suggestion=f"Add {mod_name.upper()}_DEV_ERROR_DETECT "
                                          f"configuration and Det_ReportError() calls")

    def _check_module_ids(self, scan_result: ScanResult):
        """Check that MODULE_ID defines match AUTOSAR assigned values."""
        for mod_name, mod_files in scan_result.modules.items():
            mod_spec = self.registry.get_module_spec(self.version, mod_name)
            if not mod_spec:
                continue

            for pf in mod_files.parsed_files:
                for macro in pf.macros:
                    if macro.name in (f'{mod_name.upper()}_MODULE_ID',
                                      f'{mod_name}_MODULE_ID'):
                        try:
                            actual_id = int(macro.value.rstrip('uUlL'), 0)
                            if actual_id == mod_spec.module_id:
                                self._pass(mod_name, "DET-004",
                                           f"Module ID {actual_id} matches AUTOSAR spec",
                                           f"{macro.name} = {actual_id} matches the AUTOSAR "
                                           f"assigned Module ID for {mod_name}.",
                                           file_path=pf.file_path,
                                           line_number=macro.line_number)
                            else:
                                self._fail(mod_name, "DET-004",
                                           f"Module ID mismatch: {actual_id} != {mod_spec.module_id}",
                                           f"{macro.name} is defined as {actual_id} but "
                                           f"AUTOSAR assigns Module ID {mod_spec.module_id} "
                                           f"to {mod_name}. Wrong Module ID causes incorrect "
                                           f"DET error attribution.",
                                           file_path=pf.file_path,
                                           line_number=macro.line_number,
                                           expected=str(mod_spec.module_id),
                                           actual=str(actual_id))
                        except ValueError:
                            pass

    def _check_error_defines(self, scan_result: ScanResult):
        """Check that DET error macros are defined with correct values."""
        for mod_name, mod_files in scan_result.modules.items():
            mod_spec = self.registry.get_module_spec(self.version, mod_name)
            if not mod_spec or not mod_spec.det_errors:
                continue

            defined_errors = {}
            for pf in mod_files.parsed_files:
                for macro in pf.macros:
                    for det_err in mod_spec.det_errors:
                        if macro.name == det_err.name:
                            defined_errors[macro.name] = (macro, pf.file_path)

            for det_err in mod_spec.det_errors:
                if det_err.name in defined_errors:
                    macro, fpath = defined_errors[det_err.name]
                    try:
                        actual_val = int(macro.value.rstrip('uUlL'), 0)
                        if actual_val == det_err.value:
                            self._pass(mod_name, "DET-005",
                                       f"DET error {det_err.name} = 0x{det_err.value:02X} OK",
                                       file_path=fpath,
                                       line_number=macro.line_number)
                        else:
                            self._fail(mod_name, "DET-005",
                                       f"DET error {det_err.name} value mismatch",
                                       f"{det_err.name} is defined as 0x{actual_val:02X} "
                                       f"but AUTOSAR SWS specifies 0x{det_err.value:02X}. "
                                       f"{det_err.description}",
                                       file_path=fpath,
                                       line_number=macro.line_number,
                                       expected=f"0x{det_err.value:02X}",
                                       actual=f"0x{actual_val:02X}")
                    except ValueError:
                        pass
                else:
                    self._info(mod_name, "DET-005",
                               f"DET error {det_err.name} not defined",
                               f"AUTOSAR SWS defines {det_err.name} = 0x{det_err.value:02X} "
                               f"for {mod_name} but this macro was not found. "
                               f"{det_err.description}")
