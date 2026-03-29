"""Naming Convention Checker - Validates AUTOSAR naming conventions."""

import re

from ..parser.file_scanner import ScanResult
from .base_checker import BaseChecker, CheckerReport


class NamingChecker(BaseChecker):
    name = "naming_checker"
    description = "Checks AUTOSAR naming conventions for functions, macros, and types"

    def check(self, scan_result: ScanResult) -> CheckerReport:
        self.report = CheckerReport(checker_name=self.name)

        self._check_function_naming(scan_result)
        self._check_macro_prefix(scan_result)
        self._check_type_naming(scan_result)

        return self.report

    def _check_function_naming(self, scan_result: ScanResult):
        """Check that function names follow <Module>_<FunctionName> pattern."""
        for mod_name, mod_files in scan_result.modules.items():
            for pf in mod_files.parsed_files:
                for func in pf.functions:
                    if not func.is_definition:
                        continue
                    # AUTOSAR convention: functions start with ModuleName_
                    # Exceptions: static/internal functions, SchM macros
                    name = func.name
                    if name.startswith('static '):
                        continue

                    # Check if function belongs to this module
                    expected_prefix = f"{mod_name}_"
                    alt_prefixes = [
                        f"{mod_name}_",
                        f"{mod_name.lower()}_",
                    ]

                    has_valid_prefix = any(name.startswith(p) for p in alt_prefixes)

                    # Some functions are callbacks named after other modules
                    # e.g., PduR has PduR_CanIfRxIndication (prefix is PduR_)
                    if not has_valid_prefix:
                        # Check if it's a known cross-module pattern
                        is_cross = False
                        for other_mod in scan_result.modules:
                            if name.startswith(f"{other_mod}_"):
                                is_cross = True
                                break

                        if not is_cross and not name.startswith(('main', 'ISR', 'Os_')):
                            self._warn(mod_name, "NAME-001",
                                       f"Function '{name}' in {mod_name} has non-standard prefix",
                                       f"Function '{name}' defined in module {mod_name} does "
                                       f"not start with '{expected_prefix}'. AUTOSAR SWS "
                                       f"requires public functions to use <Module>_<Name> "
                                       f"naming convention. This ensures no name collisions "
                                       f"between modules.",
                                       file_path=pf.file_path,
                                       line_number=func.line_number,
                                       expected=f"{expected_prefix}<FunctionName>",
                                       actual=name)

    def _check_macro_prefix(self, scan_result: ScanResult):
        """Check that public macros follow <MODULE>_ prefix convention."""
        # Only check _Cfg.h and main header macros
        for mod_name, mod_files in scan_result.modules.items():
            upper_prefix = mod_name.upper() + '_'
            conf_prefix = f"{mod_name}Conf_"
            alt_prefixes = [upper_prefix, conf_prefix, f"{mod_name}_"]

            for pf in mod_files.parsed_files:
                if not pf.file_path.endswith('.h'):
                    continue

                for macro in pf.macros:
                    name = macro.name
                    # Skip common system macros
                    if name.startswith(('STD_', 'NULL', 'E_', 'TRUE', 'FALSE',
                                       'BUFREQ_', 'SchM_')):
                        continue
                    # Skip include guards
                    if name.endswith(('_H', '_H_')):
                        continue

                    has_prefix = any(name.startswith(p) for p in alt_prefixes)
                    if not has_prefix and len(name) > 3:
                        # Check if it references this module somehow
                        mod_in_name = mod_name.upper() in name.upper()
                        if not mod_in_name:
                            self._info(mod_name, "NAME-002",
                                       f"Macro '{name}' lacks module prefix",
                                       f"Macro '{name}' in {pf.file_path} does not start "
                                       f"with '{upper_prefix}' or '{conf_prefix}'. "
                                       f"AUTOSAR naming convention requires module-prefixed "
                                       f"macros to prevent global namespace collisions.",
                                       file_path=pf.file_path,
                                       line_number=macro.line_number)

    def _check_type_naming(self, scan_result: ScanResult):
        """Check typedef naming conventions."""
        for mod_name, mod_files in scan_result.modules.items():
            for pf in mod_files.parsed_files:
                for td in pf.typedefs:
                    name = td.name
                    # Skip standard AUTOSAR types
                    if name.startswith(('Std_', 'Pdu', 'Com_', 'Can_',
                                       'boolean', 'uint', 'sint', 'float')):
                        continue

                    # Config types should end with _ConfigType
                    if 'Config' in name and not name.endswith('ConfigType'):
                        self._warn(mod_name, "NAME-003",
                                   f"Config type '{name}' should end with 'ConfigType'",
                                   f"Type '{name}' appears to be a configuration type "
                                   f"but does not follow the AUTOSAR naming convention "
                                   f"'<Module>_ConfigType'.",
                                   file_path=pf.file_path,
                                   line_number=td.line_number)

                    # Types should start with Module name
                    expected_prefix = f"{mod_name}_"
                    if not name.startswith(expected_prefix):
                        # Check common patterns (CanIf_ControllerModeType etc.)
                        for other_mod in scan_result.modules:
                            if name.startswith(f"{other_mod}_"):
                                break
                        else:
                            if td.kind in ('struct', 'enum') and len(name) > 5:
                                self._info(mod_name, "NAME-003",
                                           f"Type '{name}' lacks '{expected_prefix}' prefix",
                                           f"Type '{name}' in {mod_name} does not follow "
                                           f"<Module>_<TypeName> convention.",
                                           file_path=pf.file_path,
                                           line_number=td.line_number)
