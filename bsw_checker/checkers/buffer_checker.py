"""Buffer & Pointer Safety Checker - Detects NULL pointer passing and buffer issues."""

import re
from collections import defaultdict

from ..parser.file_scanner import ScanResult
from .base_checker import BaseChecker, CheckerReport


# Pattern: function call with NULL_PTR or NULL as argument
_RE_NULL_ARG_CALL = re.compile(
    r'\b(\w+)\s*\(([^;]*?\bNULL(?:_PTR)?\b[^;]*?)\)\s*;'
)

# APIs that should NEVER receive NULL pointer for data buffers
_CRITICAL_DATA_APIS = {
    "PduR_ComTransmit": (1, "PduInfoPtr"),
    "PduR_DcmTransmit": (1, "PduInfoPtr"),
    "CanIf_Transmit": (1, "PduInfoPtr"),
    "Can_Write": (1, "PduInfo"),
    "Com_RxIndication": (1, "PduInfoPtr"),
    "Com_SendSignal": (1, "SignalDataPtr"),
    "Com_ReceiveSignal": (1, "SignalDataPtr"),
    "NvM_ReadBlock": (1, "NvM_DstPtr"),
    "NvM_WriteBlock": (1, "NvM_SrcPtr"),
    "Fee_Read": (2, "DataBufferPtr"),
    "Fee_Write": (1, "DataBufferPtr"),
    "Fls_Write": (1, "SourceAddressPtr"),
    "Fls_Read": (1, "TargetAddressPtr"),
    "Dcm_CopyRxData": (1, "info"),
    "Dcm_CopyTxData": (1, "info"),
}

# Pattern: PduInfoType variable with SduDataPtr = NULL_PTR
_RE_PDU_NULL_SDU = re.compile(
    r'(\w+)\.SduDataPtr\s*=\s*NULL(?:_PTR)?'
)

# Pattern: followed by function call using that variable
_RE_PDU_USAGE = re.compile(
    r'\b(\w+)\s*\([^;]*?&(\w+)[^;]*?\)\s*;'
)


class BufferChecker(BaseChecker):
    name = "buffer_checker"
    description = "Checks for NULL pointer passing and buffer safety issues"

    def check(self, scan_result: ScanResult) -> CheckerReport:
        self.report = CheckerReport(checker_name=self.name)

        self._check_null_ptr_arguments(scan_result)
        self._check_pdu_null_sdu(scan_result)
        self._check_init_guard_patterns(scan_result)

        return self.report

    def _check_null_ptr_arguments(self, scan_result: ScanResult):
        """Detect direct NULL_PTR passed to critical APIs."""
        for mod_name, mod_files in scan_result.modules.items():
            for pf in mod_files.parsed_files:
                if not pf.file_path.endswith('.c'):
                    continue
                for m in _RE_NULL_ARG_CALL.finditer(pf.raw_content):
                    func_name = m.group(1)
                    args_text = m.group(2)

                    if func_name not in _CRITICAL_DATA_APIS:
                        continue

                    param_idx, param_name = _CRITICAL_DATA_APIS[func_name]
                    # Split args and check if the critical one is NULL
                    args = [a.strip() for a in args_text.split(',')]
                    if param_idx < len(args):
                        arg_val = args[param_idx].strip()
                        if arg_val in ('NULL_PTR', 'NULL', '((void*)0)', '0'):
                            line_no = pf.raw_content[:m.start()].count('\n') + 1
                            self._fail(mod_name, "BUF-001",
                                       f"NULL passed to {func_name}() param '{param_name}'",
                                       f"Module {mod_name} calls {func_name}() with NULL "
                                       f"as the '{param_name}' parameter (argument #{param_idx+1}). "
                                       f"This API expects a valid data pointer. Passing NULL "
                                       f"will cause a null pointer dereference in the callee "
                                       f"module if it doesn't check, or E_NOT_OK if it does. "
                                       f"Either way, the intended data transfer fails silently.",
                                       file_path=pf.file_path,
                                       line_number=line_no,
                                       suggestion=f"Provide a valid buffer pointer to {func_name}()")

    def _check_pdu_null_sdu(self, scan_result: ScanResult):
        """Detect PduInfoType with SduDataPtr=NULL being passed to Transmit APIs."""
        for mod_name, mod_files in scan_result.modules.items():
            for pf in mod_files.parsed_files:
                if not pf.file_path.endswith('.c'):
                    continue
                content = pf.raw_content

                # Find all PduInfoType vars with NULL SduDataPtr
                null_pdu_vars = set()
                for m in _RE_PDU_NULL_SDU.finditer(content):
                    var_name = m.group(1)
                    null_pdu_vars.add(var_name)

                if not null_pdu_vars:
                    continue

                # Now check if those vars are passed to Transmit APIs
                transmit_apis = {
                    'PduR_ComTransmit', 'PduR_DcmTransmit',
                    'CanIf_Transmit', 'Can_Write',
                }
                for m in _RE_PDU_USAGE.finditer(content):
                    api_name = m.group(1)
                    var_ref = m.group(2)

                    if api_name in transmit_apis and var_ref in null_pdu_vars:
                        line_no = content[:m.start()].count('\n') + 1
                        self._warn(mod_name, "BUF-002",
                                   f"PduInfo with NULL SduDataPtr passed to {api_name}()",
                                   f"Variable '{var_ref}' has SduDataPtr=NULL_PTR but is "
                                   f"passed to {api_name}() via &{var_ref}. "
                                   f"The receiving module will get a PduInfoType whose "
                                   f"SduDataPtr is NULL, making the actual PDU data "
                                   f"inaccessible. This typically means the transmitted "
                                   f"CAN frame will contain garbage data or zeros.",
                                   file_path=pf.file_path,
                                   line_number=line_no,
                                   suggestion=f"Set {var_ref}.SduDataPtr to point to actual data buffer")

    def _check_init_guard_patterns(self, scan_result: ScanResult):
        """Check that modules guard API calls with init status checks."""
        # Find modules that have init status variable but some APIs don't check it
        init_guard_pattern = re.compile(
            r'if\s*\(\s*(\w+_InitStatus)\s*==\s*(?:FALSE|STD_OFF|0U?)\s*\)'
        )

        for mod_name, mod_files in scan_result.modules.items():
            mod_spec = self.registry.get_module_spec(self.get_version(mod_name), mod_name)
            if not mod_spec:
                continue

            for pf in mod_files.parsed_files:
                if not pf.file_path.endswith('.c'):
                    continue

                # Check if module uses init guard pattern
                guards = init_guard_pattern.findall(pf.raw_content)
                if not guards:
                    continue

                guard_var = guards[0]

                # Find functions that DON'T check init status
                for func in pf.functions:
                    if not func.is_definition:
                        continue
                    if func.name.endswith(('_Init', '_PreInit', '_DeInit')):
                        continue
                    if func.name.endswith(('_GetVersionInfo',)):
                        continue

                    # Check if this function body contains the init guard
                    # Simple heuristic: search for guard_var near the function
                    func_start = pf.raw_content.find(func.name + '(')
                    if func_start < 0:
                        continue

                    # Look ahead ~500 chars for the guard
                    func_section = pf.raw_content[func_start:func_start + 500]
                    if guard_var not in func_section:
                        # Only warn for mandatory APIs
                        if mod_spec.apis:
                            is_mandatory = any(
                                api.name == func.name and api.mandatory
                                for api in mod_spec.apis
                            )
                            if is_mandatory and not func.name.endswith('_MainFunction'):
                                self._info(mod_name, "BUF-003",
                                           f"{func.name}() may lack init guard",
                                           f"Function {func.name}() does not appear to check "
                                           f"'{guard_var}' near its entry. If called before "
                                           f"{mod_name}_Init(), it may access uninitialized "
                                           f"data. AUTOSAR SWS requires DET error reporting "
                                           f"for calls in uninitialized state.",
                                           file_path=pf.file_path,
                                           line_number=func.line_number)
