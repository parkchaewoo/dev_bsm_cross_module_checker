"""Type Checker - Verifies AUTOSAR standard type usage."""

from ..parser.file_scanner import ScanResult, ModuleFiles
from ..spec.module_registry import ModuleRegistry, ModuleSpec
from .base_checker import BaseChecker, CheckerReport


# Standard AUTOSAR types that should be used
AUTOSAR_STANDARD_TYPES = {
    "Std_ReturnType": "Standard return type for API functions",
    "Std_VersionInfoType": "Standard version info structure",
    "PduIdType": "PDU identifier type for communication",
    "PduInfoType": "PDU information (data pointer + length)",
    "PduLengthType": "PDU data length type",
    "boolean": "AUTOSAR boolean type",
}

COMSTACK_TYPES = {
    "PduIdType", "PduInfoType", "PduLengthType",
    "BufReq_ReturnType", "RetryInfoType",
    "NetworkHandleType", "IcomConfigIdType",
}

# C standard types that should be replaced with AUTOSAR platform types
C_TYPE_REPLACEMENTS = {
    "unsigned char": "uint8",
    "unsigned short": "uint16",
    "unsigned int": "uint32",
    "unsigned long": "uint32",
    "signed char": "sint8",
    "signed short": "sint16",
    "signed int": "sint32",
    "char": "uint8 or sint8",
    "short": "sint16",
    "int": "sint32",
    "long": "sint32",
}


class TypeChecker(BaseChecker):
    name = "type_checker"
    description = "Checks AUTOSAR standard type usage and config type definitions"

    def check(self, scan_result: ScanResult) -> CheckerReport:
        self.report = CheckerReport(checker_name=self.name)

        for mod_name, mod_files in scan_result.modules.items():
            mod_spec = self.registry.get_module_spec(self.version, mod_name)

            self._check_config_type(mod_name, mod_files, mod_spec)
            self._check_standard_type_usage(mod_name, mod_files)
            self._check_c_type_usage(mod_name, mod_files)

        return self.report

    def _check_config_type(self, mod_name: str, mod_files: ModuleFiles,
                            mod_spec):
        if not mod_spec or not mod_spec.config_type:
            return

        expected_type = mod_spec.config_type
        all_typedefs = {}
        for pf in mod_files.parsed_files:
            for td in pf.typedefs:
                all_typedefs[td.name] = td

        if expected_type in all_typedefs:
            td = all_typedefs[expected_type]
            self._pass(mod_name, "TYPE-001",
                       f"Config type '{expected_type}' defined",
                       f"Configuration type {expected_type} found in "
                       f"{td.file_path}:{td.line_number}. "
                       f"This type is required for {mod_name}_Init() parameter.",
                       file_path=td.file_path,
                       line_number=td.line_number)

            # Check if it's a struct (should be for config types)
            if td.kind not in ('struct', 'typedef'):
                self._warn(mod_name, "TYPE-002",
                           f"Config type '{expected_type}' is not a struct",
                           f"Expected {expected_type} to be a typedef struct, "
                           f"but found kind='{td.kind}'. "
                           f"AUTOSAR config types are typically struct definitions.",
                           file_path=td.file_path,
                           line_number=td.line_number)
        else:
            self._fail(mod_name, "TYPE-001",
                       f"Config type '{expected_type}' not found",
                       f"Configuration type {expected_type} is required by AUTOSAR SWS "
                       f"for {mod_name}_Init() but was not found in any {mod_name} "
                       f"header files. This type should be defined in {mod_name}_Types.h "
                       f"or {mod_name}_Cfg.h.",
                       expected=f"typedef struct {{ ... }} {expected_type};",
                       suggestion=f"Define {expected_type} in {mod_name}_Types.h or {mod_name}_Cfg.h")

    def _check_standard_type_usage(self, mod_name: str, mod_files: ModuleFiles):
        """Check that module uses AUTOSAR standard types correctly."""
        for pf in mod_files.parsed_files:
            for func in pf.functions:
                # Check if Std_ReturnType is used where appropriate
                if func.return_type in ('uint8', 'unsigned char') and func.name.endswith(
                    ('Transmit', 'Read', 'Write', 'Request', 'SetControllerMode',
                     'GetControllerMode')):
                    self._warn(mod_name, "TYPE-003",
                               f"{func.name}() should return Std_ReturnType",
                               f"Function {func.name}() returns '{func.return_type}' but "
                               f"AUTOSAR convention uses 'Std_ReturnType' for APIs that "
                               f"return E_OK/E_NOT_OK. Using the standard type improves "
                               f"code readability and cross-module compatibility.",
                               file_path=func.file_path,
                               line_number=func.line_number,
                               expected="Std_ReturnType",
                               actual=func.return_type)

    def _check_c_type_usage(self, mod_name: str, mod_files: ModuleFiles):
        """Warn about C standard types that should be AUTOSAR platform types."""
        import re
        for pf in mod_files.parsed_files:
            for func in pf.functions:
                for param in func.params:
                    for c_type, autosar_type in C_TYPE_REPLACEMENTS.items():
                        # Use word boundary to avoid matching 'int' in 'uint8'
                        if re.search(r'\b' + re.escape(c_type) + r'\b', param) and autosar_type not in param:
                            self._warn(mod_name, "TYPE-004",
                                       f"C type '{c_type}' in {func.name}() parameter",
                                       f"Parameter '{param}' in {func.name}() uses C type "
                                       f"'{c_type}'. AUTOSAR requires platform-independent "
                                       f"types. Use '{autosar_type}' instead for portability "
                                       f"across different MCU architectures.",
                                       file_path=func.file_path,
                                       line_number=func.line_number,
                                       expected=autosar_type,
                                       actual=c_type)
                            break
