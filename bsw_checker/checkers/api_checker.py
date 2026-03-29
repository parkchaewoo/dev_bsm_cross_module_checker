"""API Checker - Verifies mandatory AUTOSAR API existence and signatures."""

from ..parser.file_scanner import ScanResult, ModuleFiles
from ..spec.module_registry import ModuleRegistry, ModuleSpec
from .base_checker import BaseChecker, CheckerReport


class ApiChecker(BaseChecker):
    name = "api_checker"
    description = "Checks mandatory AUTOSAR APIs exist with correct signatures"

    def check(self, scan_result: ScanResult) -> CheckerReport:
        self.report = CheckerReport(checker_name=self.name)

        for mod_name, mod_files in scan_result.modules.items():
            mod_spec = self.registry.get_module_spec(self.version, mod_name)
            if not mod_spec:
                self._info(mod_name, "API-000",
                           f"{mod_name} not in AUTOSAR spec registry",
                           f"Module {mod_name} was found but has no spec definition "
                           f"for AUTOSAR version {self.version}. "
                           f"This could mean it's a vendor-specific or custom module.")
                continue

            self._check_mandatory_apis(mod_name, mod_files, mod_spec)
            self._check_api_signatures(mod_name, mod_files, mod_spec)
            self._check_main_functions(mod_name, mod_files, mod_spec)
            self._check_init_function(mod_name, mod_files, mod_spec)

        return self.report

    def _get_all_functions(self, mod_files: ModuleFiles) -> dict:
        """Get all functions across all parsed files of a module."""
        funcs = {}
        for pf in mod_files.parsed_files:
            for f in pf.functions:
                funcs[f.name] = f
        return funcs

    def _check_mandatory_apis(self, mod_name: str, mod_files: ModuleFiles,
                               mod_spec: ModuleSpec):
        funcs = self._get_all_functions(mod_files)

        for api in mod_spec.apis:
            if not api.mandatory:
                continue
            # Check version applicability
            if api.since_version > self.version:
                continue

            if api.name in funcs:
                self._pass(mod_name, "API-001",
                           f"{api.name}() exists",
                           f"Mandatory API {api.name}() found in "
                           f"{funcs[api.name].file_path}:{funcs[api.name].line_number}. "
                           f"Description: {api.description}",
                           file_path=funcs[api.name].file_path,
                           line_number=funcs[api.name].line_number)
            else:
                self._fail(mod_name, "API-001",
                           f"{api.name}() missing",
                           f"Mandatory API {api.name}() is required by AUTOSAR {self.version} "
                           f"SWS but was not found in any {mod_name} source files. "
                           f"This API is essential: {api.description}. "
                           f"Check if the function is defined in {mod_name}.c or declared in {mod_name}.h.",
                           expected=f"{api.return_type} {api.name}({', '.join(api.params)})",
                           suggestion=f"Add {api.name}() implementation to {mod_name}.c "
                                      f"and declaration to {mod_name}.h",
                           autosar_ref=f"SWS_{mod_name}, API Service ID 0x{api.api_service_id:02X}")

    def _check_api_signatures(self, mod_name: str, mod_files: ModuleFiles,
                               mod_spec: ModuleSpec):
        funcs = self._get_all_functions(mod_files)

        for api in mod_spec.apis:
            if api.name not in funcs:
                continue
            func = funcs[api.name]

            # Check return type
            ret_ok = self._match_return_type(func.return_type, api.return_type)
            if not ret_ok:
                self._fail(mod_name, "API-002",
                           f"{api.name}() wrong return type",
                           f"Function {api.name}() has return type '{func.return_type}' "
                           f"but AUTOSAR SWS specifies '{api.return_type}'. "
                           f"This may cause type mismatch errors or undefined behavior "
                           f"when the return value is used by calling modules.",
                           file_path=func.file_path,
                           line_number=func.line_number,
                           expected=api.return_type,
                           actual=func.return_type,
                           suggestion=f"Change return type to {api.return_type}",
                           autosar_ref=f"SWS_{mod_name}")

            # Check parameter count
            expected_param_count = len(api.params)
            actual_param_count = len(func.params)
            if expected_param_count != actual_param_count:
                self._fail(mod_name, "API-003",
                           f"{api.name}() wrong parameter count",
                           f"Function {api.name}() has {actual_param_count} parameter(s) "
                           f"but AUTOSAR SWS specifies {expected_param_count}. "
                           f"Expected: ({', '.join(api.params)}). "
                           f"Actual: ({', '.join(func.params)}). "
                           f"Incorrect parameter count will cause compilation errors or "
                           f"runtime crashes in cross-module calls.",
                           file_path=func.file_path,
                           line_number=func.line_number,
                           expected=f"{expected_param_count} params: {', '.join(api.params)}",
                           actual=f"{actual_param_count} params: {', '.join(func.params)}",
                           autosar_ref=f"SWS_{mod_name}")

    def _check_main_functions(self, mod_name: str, mod_files: ModuleFiles,
                               mod_spec: ModuleSpec):
        if not mod_spec.has_main_function:
            return

        funcs = self._get_all_functions(mod_files)
        for mf_name in mod_spec.main_function_names:
            if mf_name in funcs:
                self._pass(mod_name, "API-004",
                           f"{mf_name}() exists",
                           f"Cyclic main function {mf_name}() found. "
                           f"This function must be called periodically by the SchM/OS.",
                           file_path=funcs[mf_name].file_path,
                           line_number=funcs[mf_name].line_number)
            else:
                self._fail(mod_name, "API-004",
                           f"{mf_name}() missing",
                           f"Cyclic main function {mf_name}() is required but not found. "
                           f"Without this function, the {mod_name} module cannot perform "
                           f"its periodic processing tasks. This will cause the module "
                           f"to malfunction at runtime.",
                           suggestion=f"Implement {mf_name}() in {mod_name}.c and "
                                      f"ensure it is scheduled by SchM/OS")

    def _check_init_function(self, mod_name: str, mod_files: ModuleFiles,
                              mod_spec: ModuleSpec):
        funcs = self._get_all_functions(mod_files)
        init_name = f"{mod_name}_Init"

        # Check if Init takes config parameter when required
        if mod_spec.config_type and init_name in funcs:
            func = funcs[init_name]
            has_config_param = any(mod_spec.config_type in p for p in func.params)
            if not has_config_param and mod_spec.config_type:
                self._warn(mod_name, "API-005",
                           f"{init_name}() missing config parameter",
                           f"{init_name}() should accept 'const {mod_spec.config_type}*' "
                           f"parameter for post-build configuration. "
                           f"Current params: ({', '.join(func.params)}). "
                           f"Without the config parameter, post-build configuration "
                           f"changes require recompilation.",
                           file_path=func.file_path,
                           line_number=func.line_number,
                           expected=f"const {mod_spec.config_type}*",
                           actual=', '.join(func.params) or 'void')

    @staticmethod
    def _match_return_type(actual: str, expected: str) -> bool:
        """Fuzzy match return types accounting for AUTOSAR type aliases."""
        actual_clean = actual.strip().replace('  ', ' ')
        expected_clean = expected.strip()

        if actual_clean == expected_clean:
            return True

        # Common type aliases
        aliases = {
            'uint8': ['Std_ReturnType', 'uint8'],
            'Std_ReturnType': ['uint8', 'Std_ReturnType'],
            'void': ['void'],
            'Can_ReturnType': ['Can_ReturnType', 'Std_ReturnType'],
        }
        expected_aliases = aliases.get(expected_clean, [expected_clean])
        return actual_clean in expected_aliases
