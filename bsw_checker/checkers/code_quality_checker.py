"""Code Quality Checker - Return value ignored, magic numbers, prototype mismatch, dead code."""

import re
from collections import defaultdict

from ..parser.file_scanner import ScanResult
from .base_checker import BaseChecker, CheckerReport


# Functions whose return value MUST be checked
_MUST_CHECK_RETURN = {
    'PduR_ComTransmit', 'PduR_DcmTransmit',
    'CanIf_Transmit', 'Can_Write',
    'NvM_ReadBlock', 'NvM_WriteBlock',
    'Fee_Read', 'Fee_Write',
    'Fls_Read', 'Fls_Write', 'Fls_Erase',
    'Com_SendSignal', 'Com_ReceiveSignal',
    'Dem_SetEventStatus',
    'CanSM_RequestComMode', 'ComM_RequestComMode',
    'Dcm_StartOfReception', 'Dcm_CopyRxData', 'Dcm_CopyTxData',
    'CanIf_SetControllerMode', 'CanIf_GetControllerMode',
    'Det_ReportError', 'Det_ReportRuntimeError',
}

# Pattern: function call as a statement (return value discarded)
_RE_DISCARDED_CALL = re.compile(
    r'^\s+(\w+)\s*\([^;]*\)\s*;',
    re.MULTILINE
)

# Pattern: magic number in function call argument (not 0, 1, NULL)
_RE_MAGIC_NUMBER = re.compile(
    r'\b(?:0x[0-9a-fA-F]{2,}|[2-9]\d{1,})\s*[,)]'
)


class CodeQualityChecker(BaseChecker):
    name = "quality_checker"
    description = "Checks return value handling, magic numbers, prototype consistency, dead code"

    def check(self, scan_result: ScanResult) -> CheckerReport:
        self.report = CheckerReport(checker_name=self.name)

        self._check_return_value_ignored(scan_result)
        self._check_prototype_mismatch(scan_result)
        self._check_dead_functions(scan_result)
        self._check_magic_numbers_in_calls(scan_result)
        self._check_multiple_return_no_cleanup(scan_result)

        return self.report

    def _check_return_value_ignored(self, scan_result: ScanResult):
        """Detect calls to Std_ReturnType APIs where result is not checked."""
        for mod_name, mod_files in scan_result.modules.items():
            for pf in mod_files.parsed_files:
                if not pf.file_path.endswith('.c'):
                    continue

                for m in _RE_DISCARDED_CALL.finditer(pf.raw_content):
                    func_name = m.group(1)
                    if func_name not in _MUST_CHECK_RETURN:
                        continue

                    # Check if it's actually a discarded return (not assigned)
                    line_start = pf.raw_content.rfind('\n', 0, m.start()) + 1
                    line_text = pf.raw_content[line_start:m.end()].strip()

                    # If line starts with the function name (no assignment)
                    if line_text.startswith(func_name):
                        line_no = pf.raw_content[:m.start()].count('\n') + 1
                        self._warn(mod_name, "QUAL-001",
                                   f"Return value of {func_name}() ignored",
                                   f"Module {mod_name} calls {func_name}() but discards "
                                   f"the return value (Std_ReturnType). If the call fails "
                                   f"(returns E_NOT_OK), the error goes undetected. "
                                   f"This can cause silent data loss, undelivered messages, "
                                   f"or corrupted NvM blocks.",
                                   file_path=pf.file_path,
                                   line_number=line_no,
                                   suggestion=f"Check the return value: "
                                              f"if ({func_name}(...) != E_OK) {{ /* handle error */ }}")

    def _check_prototype_mismatch(self, scan_result: ScanResult):
        """Detect functions whose .h declaration differs from .c definition."""
        for mod_name, mod_files in scan_result.modules.items():
            # Collect declarations from .h and definitions from .c
            declarations = {}  # func_name -> FunctionInfo (from .h)
            definitions = {}   # func_name -> FunctionInfo (from .c)

            for pf in mod_files.parsed_files:
                for func in pf.functions:
                    if func.is_definition:
                        definitions[func.name] = func
                    elif pf.file_path.endswith('.h'):
                        declarations[func.name] = func

            # Compare
            for name, decl in declarations.items():
                if name not in definitions:
                    continue
                defn = definitions[name]

                # Check return type mismatch
                if decl.return_type != defn.return_type:
                    self._fail(mod_name, "QUAL-002",
                               f"{name}() return type mismatch: .h vs .c",
                               f"Function {name}() is declared with return type "
                               f"'{decl.return_type}' in {decl.file_path}:{decl.line_number} "
                               f"but defined with '{defn.return_type}' in "
                               f"{defn.file_path}:{defn.line_number}. "
                               f"This can cause undefined behavior due to implicit "
                               f"type conversion or calling convention mismatch.",
                               file_path=defn.file_path,
                               line_number=defn.line_number,
                               expected=decl.return_type,
                               actual=defn.return_type)

                # Check param count mismatch
                if len(decl.params) != len(defn.params):
                    self._fail(mod_name, "QUAL-003",
                               f"{name}() param count mismatch: .h({len(decl.params)}) vs .c({len(defn.params)})",
                               f"Function {name}() is declared with {len(decl.params)} "
                               f"parameter(s) in header but defined with {len(defn.params)} "
                               f"in source. The compiler may not catch this if the "
                               f"header is not included in the .c file.",
                               file_path=defn.file_path,
                               line_number=defn.line_number,
                               expected=f"{len(decl.params)} params",
                               actual=f"{len(defn.params)} params")

    def _check_dead_functions(self, scan_result: ScanResult):
        """Detect functions defined in .c but never referenced anywhere else."""
        # Collect all defined functions and all references
        defined = {}  # func_name -> (module, file, line)
        referenced = set()

        for mod_name, mod_files in scan_result.modules.items():
            for pf in mod_files.parsed_files:
                for func in pf.functions:
                    if func.is_definition:
                        defined[func.name] = (mod_name, pf.file_path, func.line_number)

                # Collect all references (calls + function pointer assignments)
                for call in pf.function_calls:
                    referenced.add(call.callee_func)
                for fptr in pf.function_pointers:
                    if fptr.assigned_func:
                        referenced.add(fptr.assigned_func)

        # Also scan raw content for references (catches macros, etc.)
        for mod_name, mod_files in scan_result.modules.items():
            for pf in mod_files.parsed_files:
                for func_name in defined:
                    if func_name in pf.raw_content:
                        referenced.add(func_name)

        # Functions that are only self-referenced (defined but count=1 in raw)
        for func_name, (mod, fpath, line) in defined.items():
            # Skip Init, MainFunction, ISR (externally called by OS/SchM)
            if any(func_name.endswith(s) for s in
                   ('_Init', '_DeInit', '_MainFunction', '_MainFunctionRx',
                    '_MainFunctionTx', '_MainFunction_Write', '_MainFunction_Read',
                    '_MainFunction_BusOff', '_MainFunction_Mode',
                    '_GetVersionInfo', '_RxIndication', '_TxConfirmation',
                    '_TriggerTransmit', '_ControllerBusOff',
                    '_ControllerModeIndication', '_BusSM_ModeIndication',
                    '_StartOfReception', '_CopyRxData', '_CopyTxData',
                    '_TpRxIndication', '_TpTxConfirmation',
                    '_Shutdown', '_PreInit', '_StartupTwo',
                    '_RequestRUN', '_ReleaseRUN', '_SetWakeupEvent',
                    '_Start', '_ReadAll', '_WriteAll',
                    '_RequestComMode', '_GetCurrentComMode',
                    '_CommunicationAllowed', '_RequestMode',
                    '_ComM_CurrentMode',
                    '_EraseImmediateBlock',
                    )):
                continue

            # Count references across ALL files (excluding definition itself)
            ref_count = 0
            for other_mod, other_files in scan_result.modules.items():
                for pf in other_files.parsed_files:
                    if pf.file_path == fpath:
                        # In same file, check if referenced beyond definition
                        occurrences = pf.raw_content.count(func_name)
                        if occurrences <= 2:  # definition + possibly prototype
                            continue
                        else:
                            ref_count += 1
                    else:
                        if func_name in pf.raw_content:
                            ref_count += 1

            if ref_count == 0:
                self._info(mod, "QUAL-004",
                           f"Potentially unused function: {func_name}()",
                           f"Function {func_name}() is defined in {fpath}:{line} "
                           f"but not referenced in any other file. "
                           f"It may be dead code. If it's an internal helper, "
                           f"consider making it static.",
                           file_path=fpath,
                           line_number=line)

    def _check_magic_numbers_in_calls(self, scan_result: ScanResult):
        """Detect hardcoded numeric values in cross-module API calls."""
        cross_apis = {
            'PduR_ComTransmit', 'PduR_DcmTransmit',
            'CanIf_Transmit', 'Can_Write',
            'Com_RxIndication', 'Com_TxConfirmation',
            'PduR_CanIfRxIndication', 'PduR_CanIfTxConfirmation',
            'Det_ReportError', 'Det_ReportRuntimeError',
            'Dem_SetEventStatus', 'Dem_ReportErrorStatus',
            'NvM_ReadBlock', 'NvM_WriteBlock',
            'CanIf_SetControllerMode',
        }

        magic_pattern = re.compile(
            r'\b(\w+)\s*\(\s*((?:0x[0-9a-fA-F]{3,}|\d{3,})[uUlL]*)\s*[,)]'
        )

        for mod_name, mod_files in scan_result.modules.items():
            for pf in mod_files.parsed_files:
                if not pf.file_path.endswith('.c'):
                    continue
                for m in magic_pattern.finditer(pf.raw_content):
                    func_name = m.group(1)
                    magic_val = m.group(2)
                    if func_name not in cross_apis:
                        continue
                    line_no = pf.raw_content[:m.start()].count('\n') + 1
                    self._warn(mod_name, "QUAL-005",
                               f"Magic number '{magic_val}' in {func_name}() call",
                               f"Hardcoded value '{magic_val}' used in {func_name}() "
                               f"call at {pf.file_path}:{line_no}. "
                               f"Use a symbolic #define constant instead for "
                               f"readability and maintainability. If this is a PDU ID, "
                               f"use ComConf_ComIPdu_* or PduRConf_* symbolic names.",
                               file_path=pf.file_path,
                               line_number=line_no,
                               suggestion=f"Replace {magic_val} with a symbolic #define")

    def _check_multiple_return_no_cleanup(self, scan_result: ScanResult):
        """Detect functions with SchM_Enter that have early returns (risk of missing Exit)."""
        enter_pattern = re.compile(r'SchM_Enter_\w+\s*\(\s*\)')
        return_pattern = re.compile(r'\breturn\b')

        for mod_name, mod_files in scan_result.modules.items():
            for pf in mod_files.parsed_files:
                if not pf.file_path.endswith('.c'):
                    continue

                for func in pf.functions:
                    if not func.is_definition:
                        continue

                    # Get approximate function body
                    start = pf.raw_content.find(func.name + '(', func.line_number - 2 if func.line_number > 2 else 0)
                    if start < 0:
                        continue
                    body = pf.raw_content[start:start + 3000]

                    enters = enter_pattern.findall(body)
                    returns = return_pattern.findall(body)

                    if enters and len(returns) > 1:
                        self._info(mod_name, "QUAL-006",
                                   f"{func.name}() has SchM_Enter + {len(returns)} returns",
                                   f"Function {func.name}() uses SchM exclusive area "
                                   f"protection and has {len(returns)} return statements. "
                                   f"Each return path must call SchM_Exit before returning. "
                                   f"Multiple returns with exclusive area protection is a "
                                   f"common source of lock-up bugs.",
                                   file_path=pf.file_path,
                                   line_number=func.line_number,
                                   suggestion="Consider single-exit pattern or ensure "
                                              "SchM_Exit is called on all return paths")
