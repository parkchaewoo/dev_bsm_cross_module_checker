"""Config Consistency Checker - Validates configuration structure patterns."""

import re
from collections import defaultdict

from ..parser.file_scanner import ScanResult
from .base_checker import BaseChecker, CheckerReport


class ConfigChecker(BaseChecker):
    name = "config_checker"
    description = "Checks BSW module configuration structure consistency"

    def check(self, scan_result: ScanResult) -> CheckerReport:
        self.report = CheckerReport(checker_name=self.name)

        self._check_cfg_h_exists(scan_result)
        self._check_pbcfg_pattern(scan_result)
        self._check_config_struct_not_empty(scan_result)
        self._check_dev_error_detect_define(scan_result)
        self._check_version_info_api_define(scan_result)

        return self.report

    def _check_cfg_h_exists(self, scan_result: ScanResult):
        """Check that modules have a _Cfg.h configuration header."""
        modules_needing_cfg = {
            'Com', 'PduR', 'CanIf', 'Can', 'CanTp', 'CanSM',
            'ComM', 'Dcm', 'Dem', 'NvM', 'Fee', 'Fls', 'BswM', 'EcuM',
        }
        for mod_name, mod_files in scan_result.modules.items():
            if mod_name not in modules_needing_cfg:
                continue
            has_cfg = any(f.endswith('_Cfg.h') for f in mod_files.config_files + mod_files.header_files)
            if has_cfg:
                self._pass(mod_name, "CFG-001",
                           f"{mod_name}_Cfg.h exists",
                           f"Configuration header found for {mod_name}.")
            else:
                self._warn(mod_name, "CFG-001",
                           f"{mod_name}_Cfg.h not found",
                           f"Module {mod_name} should have a {mod_name}_Cfg.h "
                           f"configuration header. This file defines compile-time "
                           f"configuration parameters like feature switches, buffer "
                           f"sizes, and pre-compile options. Without it, the module "
                           f"uses only default values.",
                           suggestion=f"Generate {mod_name}_Cfg.h from AUTOSAR configuration tool")

    def _check_pbcfg_pattern(self, scan_result: ScanResult):
        """Check for post-build configuration variable pattern."""
        pbcfg_pattern = re.compile(
            r'\bconst\s+(\w+_ConfigType)\s+(\w+)\s*='
        )
        for mod_name, mod_files in scan_result.modules.items():
            mod_spec = self.registry.get_module_spec(self.get_version(mod_name), mod_name)
            if not mod_spec or not mod_spec.config_type:
                continue

            found_pbcfg = False
            for pf in mod_files.parsed_files:
                if pbcfg_pattern.search(pf.raw_content):
                    found_pbcfg = True
                    break

            # Also check if Init is called with a config reference
            for other_mod, other_files in scan_result.modules.items():
                for pf in other_files.parsed_files:
                    init_call_pattern = re.compile(
                        rf'{mod_name}_Init\s*\(\s*&\s*(\w+)'
                    )
                    m = init_call_pattern.search(pf.raw_content)
                    if m:
                        found_pbcfg = True

            if found_pbcfg:
                self._pass(mod_name, "CFG-002",
                           f"{mod_name} has post-build config instance",
                           f"Module {mod_name} has a const {mod_spec.config_type} "
                           f"variable or is initialized with a config reference.")
            else:
                self._info(mod_name, "CFG-002",
                           f"{mod_name} post-build config instance not found",
                           f"No 'const {mod_spec.config_type}' variable or config "
                           f"reference found. If using post-build configuration, "
                           f"a {mod_name}_PBcfg.c file should define the config instance.")

    def _check_config_struct_not_empty(self, scan_result: ScanResult):
        """Warn about empty or dummy-only config structures."""
        for mod_name, mod_files in scan_result.modules.items():
            for pf in mod_files.parsed_files:
                for td in pf.typedefs:
                    if td.name.endswith('_ConfigType') and td.kind == 'struct':
                        real_members = [m for m in td.members
                                        if m and 'dummy' not in m.lower()
                                        and 'reserved' not in m.lower()]
                        if not real_members and td.members:
                            self._warn(mod_name, "CFG-003",
                                       f"{td.name} has only dummy members",
                                       f"Configuration type {td.name} in {pf.file_path} "
                                       f"contains only dummy/reserved fields. This suggests "
                                       f"the configuration was not properly generated. "
                                       f"A real config struct should contain actual "
                                       f"configuration parameters (buffer sizes, enable "
                                       f"flags, PDU counts, etc.).",
                                       file_path=pf.file_path,
                                       line_number=td.line_number,
                                       suggestion="Regenerate configuration from AUTOSAR tool")

    def _check_dev_error_detect_define(self, scan_result: ScanResult):
        """Check _DEV_ERROR_DETECT configuration presence."""
        for mod_name, mod_files in scan_result.modules.items():
            mod_spec = self.registry.get_module_spec(self.get_version(mod_name), mod_name)
            if not mod_spec or not mod_spec.det_errors:
                continue

            found = False
            value = ""
            for pf in mod_files.parsed_files:
                for macro in pf.macros:
                    if macro.name == f'{mod_name.upper()}_DEV_ERROR_DETECT':
                        found = True
                        value = macro.value
                        break

            if found:
                if 'OFF' in value.upper():
                    self._info(mod_name, "CFG-004",
                               f"{mod_name}_DEV_ERROR_DETECT = {value}",
                               f"Development error detection is disabled for {mod_name}. "
                               f"DET errors will not be reported. Enable for debugging.")
                else:
                    self._pass(mod_name, "CFG-004",
                               f"{mod_name}_DEV_ERROR_DETECT = {value}")
            else:
                self._info(mod_name, "CFG-004",
                           f"{mod_name}_DEV_ERROR_DETECT not found",
                           f"No DEV_ERROR_DETECT configuration macro found for {mod_name}.")

    def _check_version_info_api_define(self, scan_result: ScanResult):
        """Check _VERSION_INFO_API configuration presence."""
        for mod_name, mod_files in scan_result.modules.items():
            has_get_version_info = False
            for pf in mod_files.parsed_files:
                for f in pf.functions:
                    if f.name == f'{mod_name}_GetVersionInfo':
                        has_get_version_info = True
                        break

            if has_get_version_info:
                found_define = False
                for pf in mod_files.parsed_files:
                    for macro in pf.macros:
                        if macro.name == f'{mod_name.upper()}_VERSION_INFO_API':
                            found_define = True
                            break

                if not found_define:
                    self._info(mod_name, "CFG-005",
                               f"{mod_name}_GetVersionInfo exists but no VERSION_INFO_API define",
                               f"Module {mod_name} implements GetVersionInfo() but has no "
                               f"{mod_name.upper()}_VERSION_INFO_API configuration switch. "
                               f"This API is typically conditionally compiled.")
