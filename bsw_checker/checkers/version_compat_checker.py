"""Version Compatibility Checker - Detects API version mismatches between modules."""

from ..parser.file_scanner import ScanResult
from .base_checker import BaseChecker, CheckerReport


class VersionCompatChecker(BaseChecker):
    name = "version_compat_checker"
    description = "Detects AUTOSAR version incompatibilities between interacting modules"

    # API signature changes between versions
    VERSION_CHANGES = [
        {
            "from_ver": "4.0.3",
            "to_ver": "4.4.0",
            "module": "Com",
            "api": "Com_TxConfirmation",
            "old_params": 1,
            "new_params": 2,
            "desc": "Com_TxConfirmation added Std_ReturnType result parameter",
        },
        {
            "from_ver": "4.0.3",
            "to_ver": "4.4.0",
            "module": "CanIf",
            "api": "CanIf_TxConfirmation",
            "old_params": 1,
            "new_params": 2,
            "desc": "CanIf_TxConfirmation added Std_ReturnType result parameter",
        },
        {
            "from_ver": "4.0.3",
            "to_ver": "4.4.0",
            "module": "Det",
            "api": "Det_ReportRuntimeError",
            "old_params": 0,
            "new_params": 4,
            "desc": "Det_ReportRuntimeError is new in 4.4.0",
        },
        {
            "from_ver": "4.4.0",
            "to_ver": "4.9.0",
            "module": "Com",
            "api": "Com_GetStatus",
            "old_params": 0,
            "new_params": 0,
            "desc": "Com_GetStatus is new in 4.9.0",
        },
    ]

    # Modules that directly interact (caller -> callee module)
    INTERACTION_PAIRS = [
        ("Com", "PduR"),
        ("PduR", "CanIf"),
        ("PduR", "Com"),
        ("PduR", "CanTp"),
        ("PduR", "Dcm"),
        ("CanIf", "Can"),
        ("CanIf", "PduR"),
        ("CanIf", "CanSM"),
        ("CanIf", "CanTp"),
        ("CanSM", "CanIf"),
        ("CanSM", "ComM"),
        ("ComM", "CanSM"),
        ("ComM", "BswM"),
        ("CanTp", "CanIf"),
        ("CanTp", "PduR"),
        ("Dcm", "PduR"),
        ("Dcm", "Dem"),
        ("NvM", "Fee"),
        ("Fee", "Fls"),
        ("Dem", "NvM"),
        ("EcuM", "Com"),
        ("EcuM", "PduR"),
        ("EcuM", "CanIf"),
        ("EcuM", "Can"),
    ]

    def check(self, scan_result: ScanResult) -> CheckerReport:
        self.report = CheckerReport(checker_name=self.name)

        self._check_interacting_module_versions(scan_result)
        self._check_api_signature_compat(scan_result)

        return self.report

    def _check_interacting_module_versions(self, scan_result: ScanResult):
        """Check that directly interacting modules use compatible AUTOSAR versions."""
        present = set(scan_result.modules.keys())

        checked_pairs = set()
        for caller, callee in self.INTERACTION_PAIRS:
            if caller not in present or callee not in present:
                continue

            pair_key = (caller, callee)
            if pair_key in checked_pairs:
                continue
            checked_pairs.add(pair_key)

            caller_ver = self.get_version(caller)
            callee_ver = self.get_version(callee)

            if caller_ver == callee_ver:
                self._pass("System", "COMPAT-001",
                           f"{caller}({caller_ver}) <-> {callee}({callee_ver}) version match",
                           f"Interacting modules {caller} and {callee} both use "
                           f"AUTOSAR {caller_ver}. No version compatibility issues.")
            else:
                # Determine severity based on version distance
                ver_order = ["4.0.3", "4.4.0", "4.9.0", "20.0.0"]
                try:
                    idx1 = ver_order.index(caller_ver)
                    idx2 = ver_order.index(callee_ver)
                    distance = abs(idx1 - idx2)
                except ValueError:
                    distance = 1

                if distance >= 2:
                    self._fail("System", "COMPAT-001",
                               f"Version mismatch: {caller}({caller_ver}) <-> {callee}({callee_ver})",
                               f"Interacting modules {caller} ({caller_ver}) and {callee} "
                               f"({callee_ver}) use significantly different AUTOSAR versions "
                               f"(distance={distance}). API signatures, callback parameters, "
                               f"and behavior may have changed between these versions. "
                               f"This can cause compilation errors, runtime crashes, or "
                               f"silent data corruption at the module boundary.",
                               suggestion=f"Align {caller} and {callee} to the same AUTOSAR version")
                else:
                    self._warn("System", "COMPAT-001",
                               f"Version difference: {caller}({caller_ver}) <-> {callee}({callee_ver})",
                               f"Interacting modules {caller} ({caller_ver}) and {callee} "
                               f"({callee_ver}) use different AUTOSAR versions. "
                               f"Check if API changes between {caller_ver} and {callee_ver} "
                               f"affect the interface between these modules.",
                               suggestion="Review API changes between these versions")

    def _check_api_signature_compat(self, scan_result: ScanResult):
        """Check specific known API signature changes between versions."""
        present = set(scan_result.modules.keys())

        for change in self.VERSION_CHANGES:
            mod = change["module"]
            if mod not in present:
                continue

            mod_ver = self.get_version(mod)
            api_name = change["api"]

            # Find the function in parsed files
            for pf in scan_result.modules[mod].parsed_files:
                for func in pf.functions:
                    if func.name != api_name:
                        continue

                    param_count = len(func.params)

                    # Check if module version is >= to_ver but API has old param count
                    if mod_ver >= change["to_ver"] and param_count == change["old_params"]:
                        if change["old_params"] > 0:
                            self._fail(mod, "COMPAT-002",
                                       f"{api_name}() has {change['from_ver']} signature "
                                       f"but module set to {mod_ver}",
                                       f"{api_name}() has {param_count} parameter(s), which "
                                       f"matches AUTOSAR {change['from_ver']} signature. "
                                       f"But module {mod} is configured for AUTOSAR {mod_ver} "
                                       f"which requires {change['new_params']} parameter(s). "
                                       f"Change: {change['desc']}. "
                                       f"Calling modules expecting the new signature will "
                                       f"pass wrong arguments, causing undefined behavior.",
                                       file_path=pf.file_path,
                                       line_number=func.line_number,
                                       expected=f"{change['new_params']} params (AUTOSAR {change['to_ver']})",
                                       actual=f"{param_count} params (AUTOSAR {change['from_ver']})",
                                       autosar_ref=f"SWS_{mod}")
                    break
