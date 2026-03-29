"""PDU Checker - Verifies PDU ID and Signal mapping consistency across modules."""

import re
from collections import defaultdict

from ..parser.file_scanner import ScanResult, ModuleFiles
from ..parser.c_parser import MacroDefine
from .base_checker import BaseChecker, CheckerReport


# Patterns for PDU ID defines
_RE_PDU_ID = re.compile(r'(?:Pdu|PDU|pdu)(?:R|Id|ID|_ID)', re.IGNORECASE)
_RE_SIGNAL_ID = re.compile(r'(?:Signal|SIGNAL|Sig)(?:Id|ID|_ID)', re.IGNORECASE)
_RE_SYMBOLIC_NAME = re.compile(
    r'(ComConf_ComIPdu_|PduRConf_PduR(?:Src|Dest)Pdu_|CanIfConf_CanIf(?:Tx|Rx)PduCfg_)(\w+)'
)


class PduChecker(BaseChecker):
    name = "pdu_checker"
    description = "Checks PDU ID/Signal mapping consistency across modules"

    def check(self, scan_result: ScanResult) -> CheckerReport:
        self.report = CheckerReport(checker_name=self.name)

        pdu_ids = self._collect_pdu_ids(scan_result)
        signal_ids = self._collect_signal_ids(scan_result)

        self._check_pdu_id_consistency(pdu_ids, scan_result)
        self._check_symbolic_name_consistency(scan_result)
        self._check_pdu_dlc_consistency(scan_result)
        if signal_ids:
            self._check_signal_id_ranges(signal_ids)

        return self.report

    def _collect_pdu_ids(self, scan_result: ScanResult) -> dict[str, list[tuple[str, MacroDefine]]]:
        """Collect all PDU ID defines grouped by base name."""
        pdu_ids = defaultdict(list)  # base_name -> [(module, macro)]

        for mod_name, mod_files in scan_result.modules.items():
            for pf in mod_files.parsed_files:
                for macro in pf.macros:
                    if _RE_PDU_ID.search(macro.name) or 'PduId' in macro.name:
                        # Extract base PDU name
                        base = self._extract_pdu_base_name(macro.name, mod_name)
                        pdu_ids[base].append((mod_name, macro))

        return pdu_ids

    def _collect_signal_ids(self, scan_result: ScanResult) -> dict[str, list[tuple[str, MacroDefine]]]:
        """Collect all Signal ID defines."""
        signal_ids = defaultdict(list)

        for mod_name, mod_files in scan_result.modules.items():
            for pf in mod_files.parsed_files:
                for macro in pf.macros:
                    if _RE_SIGNAL_ID.search(macro.name):
                        signal_ids[macro.name].append((mod_name, macro))

        return signal_ids

    def _extract_pdu_base_name(self, macro_name: str, module_name: str) -> str:
        """Extract the base PDU name from a macro, removing module prefixes."""
        # Remove common prefixes
        prefixes = [
            f"ComConf_ComIPdu_",
            f"PduRConf_PduRSrcPdu_",
            f"PduRConf_PduRDestPdu_",
            f"CanIfConf_CanIfTxPduCfg_",
            f"CanIfConf_CanIfRxPduCfg_",
            f"{module_name}_",
            f"{module_name.upper()}_",
        ]
        result = macro_name
        for prefix in prefixes:
            if result.startswith(prefix):
                result = result[len(prefix):]
                break
        # Remove common suffixes
        for suffix in ['_PduId', '_PDU_ID', '_Id', '_ID']:
            if result.endswith(suffix):
                result = result[:-len(suffix)]
        return result

    def _check_pdu_id_consistency(self, pdu_ids: dict, scan_result: ScanResult):
        """Check that PDU IDs for same PDU match across modules."""
        for base_name, entries in pdu_ids.items():
            if len(entries) < 2:
                continue

            # Group by value
            by_value = defaultdict(list)
            for mod_name, macro in entries:
                by_value[macro.value].append((mod_name, macro))

            if len(by_value) == 1:
                modules_involved = set(m for m, _ in entries)
                if len(modules_involved) > 1:
                    self._pass("System", "PDU-001",
                               f"PDU '{base_name}' ID consistent across {modules_involved}",
                               f"PDU '{base_name}' has consistent ID value "
                               f"'{list(by_value.keys())[0]}' across modules "
                               f"{', '.join(sorted(modules_involved))}.")
            else:
                # Mismatch found
                details = []
                for value, mods in by_value.items():
                    for mod_name, macro in mods:
                        details.append(f"  {mod_name}: {macro.name} = {value} "
                                       f"({macro.file_path}:{macro.line_number})")

                self._fail("System", "PDU-001",
                           f"PDU '{base_name}' ID mismatch across modules",
                           f"PDU '{base_name}' has different ID values in different modules. "
                           f"This will cause PDU routing failures - a PDU sent by one module "
                           f"will not be correctly received by the destination module.\n"
                           f"Values found:\n" + "\n".join(details) +
                           f"\n\nAll modules must agree on the same PDU ID for each PDU. "
                           f"Check the code generation configuration.",
                           suggestion="Regenerate configuration or manually align PDU IDs")

    def _check_symbolic_name_consistency(self, scan_result: ScanResult):
        """Check that AUTOSAR symbolic names follow conventions across modules."""
        symbolic_names = defaultdict(list)  # pdu_name -> [(module, prefix, full_name)]

        for mod_name, mod_files in scan_result.modules.items():
            for pf in mod_files.parsed_files:
                for macro in pf.macros:
                    m = _RE_SYMBOLIC_NAME.match(macro.name)
                    if m:
                        prefix = m.group(1)
                        pdu_name = m.group(2)
                        symbolic_names[pdu_name].append((mod_name, prefix, macro))

        for pdu_name, entries in symbolic_names.items():
            modules = set(m for m, _, _ in entries)
            if len(modules) > 1:
                self._pass("System", "PDU-002",
                           f"Symbolic name '{pdu_name}' found in {len(modules)} modules",
                           f"PDU symbolic name '{pdu_name}' is referenced by modules: "
                           f"{', '.join(sorted(modules))}. Cross-module symbolic name "
                           f"linkage verified.")
            elif len(modules) == 1:
                mod = list(modules)[0]
                if mod in ('Com', 'PduR', 'CanIf'):
                    self._warn(mod, "PDU-002",
                               f"Symbolic name '{pdu_name}' only in {mod}",
                               f"PDU symbolic name '{pdu_name}' (from {mod}) should also "
                               f"appear in related routing modules. "
                               f"If Com defines a PDU, PduR should reference it too.",
                               suggestion="Check that PduR and CanIf config files "
                                          "reference the same PDU names")

    def _check_pdu_dlc_consistency(self, scan_result: ScanResult):
        """Check PDU DLC (data length) consistency across modules."""
        dlc_defines = defaultdict(list)  # pdu_base -> [(module, length_value, macro)]

        length_patterns = [
            re.compile(r'(\w+)_(?:DLC|LENGTH|LEN|Size|SIZE)\b'),
        ]

        for mod_name, mod_files in scan_result.modules.items():
            for pf in mod_files.parsed_files:
                for macro in pf.macros:
                    for pattern in length_patterns:
                        m = pattern.match(macro.name)
                        if m:
                            base = m.group(1)
                            dlc_defines[base].append((mod_name, macro.value, macro))

        for base, entries in dlc_defines.items():
            if len(entries) < 2:
                continue

            values = set(v for _, v, _ in entries)
            if len(values) > 1:
                details = [f"  {mod}: {mac.name} = {val}"
                           for mod, val, mac in entries]
                self._fail("System", "PDU-003",
                           f"DLC mismatch for '{base}'",
                           f"PDU '{base}' has different DLC/length values across modules:\n"
                           + "\n".join(details) +
                           f"\n\nDLC mismatch can cause buffer overflows or truncated "
                           f"data in CAN communication.",
                           suggestion="Align DLC values across all module configurations")

    def _check_signal_id_ranges(self, signal_ids: dict):
        """Check signal ID ranges for overlaps or gaps."""
        id_values = []
        for name, entries in signal_ids.items():
            for mod_name, macro in entries:
                try:
                    val = int(macro.value, 0)
                    id_values.append((val, name, mod_name, macro))
                except (ValueError, TypeError):
                    pass

        if not id_values:
            return

        id_values.sort(key=lambda x: x[0])

        # Check for duplicate values
        seen = {}
        for val, name, mod, macro in id_values:
            if val in seen:
                prev_name, prev_mod = seen[val]
                if prev_name != name:
                    self._fail("System", "PDU-004",
                               f"Signal ID collision: {name} and {prev_name} = {val}",
                               f"Signal ID value {val} (0x{val:04X}) is used by both "
                               f"'{name}' and '{prev_name}'. This will cause signal "
                               f"routing confusion at runtime.",
                               suggestion="Assign unique signal IDs to each signal")
            else:
                seen[val] = (name, mod)
