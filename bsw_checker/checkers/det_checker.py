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
        self._check_sid_uniqueness(scan_result)
        self._check_sid_api_match(scan_result)

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
            mod_spec = self.registry.get_module_spec(self.get_version(mod_name), mod_name)
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
            mod_spec = self.registry.get_module_spec(self.get_version(mod_name), mod_name)
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
            mod_spec = self.registry.get_module_spec(self.get_version(mod_name), mod_name)
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

    def _check_sid_uniqueness(self, scan_result: ScanResult):
        """Check API Service ID (SID) uniqueness within each module."""
        sid_pattern = re.compile(
            r'#\s*define\s+(\w+_SID_\w+)\s+([\w()]+)'
        )

        for mod_name, mod_files in scan_result.modules.items():
            sids = {}  # name -> (value, file, line)
            for pf in mod_files.parsed_files:
                for m in sid_pattern.finditer(pf.raw_content):
                    name = m.group(1)
                    value = m.group(2).rstrip('uUlL')
                    line_no = pf.raw_content[:m.start()].count('\n') + 1
                    sids[name] = (value, pf.file_path, line_no)

            if not sids:
                continue

            # Check for duplicate values
            by_value = defaultdict(list)
            for name, (val, fpath, line) in sids.items():
                by_value[val].append((name, fpath, line))

            for val, entries in by_value.items():
                if len(entries) > 1:
                    names = [e[0] for e in entries]
                    self._fail(mod_name, "DET-006",
                               f"Duplicate SID value {val}: {', '.join(names)}",
                               f"Multiple API Service IDs in {mod_name} share value {val}: "
                               f"{', '.join(names)}. When Det_ReportError uses these SIDs, "
                               f"the DET log cannot distinguish which API triggered the error. "
                               f"Each API must have a unique SID per AUTOSAR SWS.",
                               file_path=entries[0][1],
                               line_number=entries[0][2],
                               suggestion="Assign unique SID values to each API")

            # Report total SIDs found as info
            self._info(mod_name, "DET-007",
                       f"{mod_name} has {len(sids)} API Service IDs defined",
                       f"Module {mod_name} defines {len(sids)} SID macros: "
                       f"{', '.join(sorted(sids.keys())[:8])}"
                       f"{'...' if len(sids) > 8 else ''}")

    def _check_sid_api_match(self, scan_result: ScanResult):
        """Check that Det_ReportError API_ID argument matches the calling function's SID."""
        # Pattern: Inside a function, Det_ReportError(MODULE_ID, INST, API_SID, ERROR)
        det_in_func = re.compile(
            r'Det_Report(?:Error|RuntimeError)\s*\(\s*\w+\s*,\s*\w+\s*,\s*(\w+)\s*,'
        )
        # SID define pattern
        sid_pattern = re.compile(
            r'#\s*define\s+(\w+)_SID_(\w+)\s+([\w()]+)'
        )

        for mod_name, mod_files in scan_result.modules.items():
            # Collect SID name -> function name mapping
            sid_to_func = {}  # SID macro name -> expected function name
            sid_values = {}   # SID macro name -> value

            for pf in mod_files.parsed_files:
                for m in sid_pattern.finditer(pf.raw_content):
                    prefix = m.group(1)
                    func_part = m.group(2)
                    value = m.group(3)
                    sid_name = f"{prefix}_SID_{func_part}"
                    # Derive expected function name: COM_SID_INIT -> Com_Init
                    expected_func = f"{mod_name}_{func_part.title().replace('_', '')}"
                    # Also try lowercase variant
                    sid_to_func[sid_name] = func_part
                    sid_values[sid_name] = value

            if not sid_to_func:
                continue

            # Check Det calls: is the SID arg in the right function?
            for pf in mod_files.parsed_files:
                if not pf.file_path.endswith('.c'):
                    continue

                for func in pf.functions:
                    if not func.is_definition:
                        continue

                    # Find Det calls near this function definition in source
                    func_start = pf.raw_content.find(f'{func.name}(')
                    if func_start < 0:
                        continue

                    # Approximate function body (~2000 chars)
                    func_section = pf.raw_content[func_start:func_start + 2000]

                    for m in det_in_func.finditer(func_section):
                        api_sid_arg = m.group(1).strip()

                        if api_sid_arg in sid_to_func:
                            expected_part = sid_to_func[api_sid_arg].upper()
                            actual_name = func.name.upper()
                            # Check if the SID corresponds to this function
                            if expected_part not in actual_name:
                                line_no = pf.raw_content[:func_start + m.start()].count('\n') + 1
                                self._warn(mod_name, "DET-008",
                                           f"SID mismatch: {api_sid_arg} in {func.name}()",
                                           f"Det_ReportError uses SID '{api_sid_arg}' "
                                           f"(for '{sid_to_func[api_sid_arg]}') inside "
                                           f"function {func.name}(). The SID should match "
                                           f"the calling function. Using wrong SIDs makes "
                                           f"DET error logs misleading.",
                                           file_path=pf.file_path,
                                           line_number=line_no,
                                           expected=f"SID for {func.name}",
                                           actual=api_sid_arg)
