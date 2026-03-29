"""Dem Event Checker - Tracks DEM event ID usage and consistency across modules."""

import re
from collections import defaultdict

from ..parser.file_scanner import ScanResult
from .base_checker import BaseChecker, CheckerReport


# Pattern: Dem_SetEventStatus(EVENT_ID, STATUS) or Dem_ReportErrorStatus(EVENT_ID, STATUS)
_RE_DEM_CALL = re.compile(
    r'\b(Dem_(?:SetEventStatus|ReportErrorStatus))\s*\(\s*(\w+)\s*,'
)

# Pattern: #define DEM_EVENT_* or DemConf_DemEventParameter_*
_RE_DEM_EVENT_DEF = re.compile(
    r'#\s*define\s+((?:DEM_EVENT_|DemConf_DemEventParameter_)\w+)\s+([\w()]+)'
)


class DemEventChecker(BaseChecker):
    name = "dem_event_checker"
    description = "Tracks DEM event IDs across modules for consistency"

    def check(self, scan_result: ScanResult) -> CheckerReport:
        self.report = CheckerReport(checker_name=self.name)

        event_defs = self._collect_event_definitions(scan_result)
        event_usage = self._collect_event_usage(scan_result)

        self._check_undefined_events(event_defs, event_usage)
        self._check_duplicate_event_ids(event_defs)
        self._check_unused_events(event_defs, event_usage)
        self._check_event_reporting_modules(event_usage, scan_result)

        return self.report

    def _collect_event_definitions(self, scan_result: ScanResult) -> dict:
        """Collect all DEM_EVENT_* and DemConf_DemEventParameter_* definitions."""
        # name -> (value, file, line, module)
        defs = {}
        for mod_name, mod_files in scan_result.modules.items():
            for pf in mod_files.parsed_files:
                for m in _RE_DEM_EVENT_DEF.finditer(pf.raw_content):
                    name = m.group(1)
                    value = m.group(2).strip()
                    line_no = pf.raw_content[:m.start()].count('\n') + 1
                    defs[name] = {
                        "value": value,
                        "file": pf.file_path,
                        "line": line_no,
                        "module": mod_name,
                    }
        return defs

    def _collect_event_usage(self, scan_result: ScanResult) -> dict:
        """Collect all Dem_SetEventStatus/Dem_ReportErrorStatus calls."""
        # event_name -> [(caller_module, file, line, api_name)]
        usage = defaultdict(list)
        for mod_name, mod_files in scan_result.modules.items():
            for pf in mod_files.parsed_files:
                for m in _RE_DEM_CALL.finditer(pf.raw_content):
                    api_name = m.group(1)
                    event_arg = m.group(2).strip()
                    line_no = pf.raw_content[:m.start()].count('\n') + 1
                    # Skip numeric literals and expressions
                    if event_arg.isdigit() or event_arg.startswith('0x'):
                        usage[event_arg].append((mod_name, pf.file_path, line_no, api_name))
                    elif event_arg not in ('EventId', 'eventId', 'id'):
                        usage[event_arg].append((mod_name, pf.file_path, line_no, api_name))
        return usage

    def _check_undefined_events(self, event_defs: dict, event_usage: dict):
        """Check that all used event IDs are defined."""
        for event_name, usages in event_usage.items():
            if event_name in event_defs:
                for caller_mod, fpath, line, api in usages:
                    self._pass(caller_mod, "DEM_EVT-001",
                               f"{caller_mod} uses {event_name} (defined)",
                               f"Module {caller_mod} calls {api}({event_name}, ...) at "
                               f"{fpath}:{line}. Event ID is defined in "
                               f"{event_defs[event_name]['file']}.",
                               file_path=fpath, line_number=line)
            else:
                # Check if it's a numeric literal
                if event_name.isdigit() or event_name.startswith('0x'):
                    for caller_mod, fpath, line, api in usages:
                        self._warn(caller_mod, "DEM_EVT-002",
                                   f"Magic number event ID: {event_name}",
                                   f"{api}() in {caller_mod} uses numeric literal "
                                   f"'{event_name}' as event ID instead of a symbolic "
                                   f"DEM_EVENT_* constant. Magic numbers make code "
                                   f"harder to maintain and trace.",
                                   file_path=fpath, line_number=line,
                                   suggestion=f"Define a DEM_EVENT_* macro for value {event_name}")
                else:
                    for caller_mod, fpath, line, api in usages:
                        self._fail(caller_mod, "DEM_EVT-001",
                                   f"Undefined DEM event: {event_name}",
                                   f"Module {caller_mod} calls {api}({event_name}, ...) at "
                                   f"{fpath}:{line}, but '{event_name}' is not defined as a "
                                   f"#define DEM_EVENT_* or DemConf_DemEventParameter_* macro "
                                   f"in any scanned file. This will cause a compilation error "
                                   f"or, if defined elsewhere, the event may not be properly "
                                   f"configured in the Dem module.",
                                   file_path=fpath, line_number=line,
                                   expected=f"#define {event_name} <value> in Dem_Cfg.h or Dem.h",
                                   suggestion=f"Add {event_name} definition to Dem configuration")

    def _check_duplicate_event_ids(self, event_defs: dict):
        """Check for duplicate event ID values."""
        by_value = defaultdict(list)
        for name, info in event_defs.items():
            val = info["value"].rstrip('uUlL()')
            by_value[val].append((name, info))

        for val, entries in by_value.items():
            if len(entries) > 1:
                names = [e[0] for e in entries]
                details = [f"  {name} in {info['file']}:{info['line']}"
                           for name, info in entries]
                self._fail("Dem", "DEM_EVT-003",
                           f"Duplicate DEM event ID value: {val}",
                           f"Multiple DEM events share the same numeric value '{val}':\n"
                           + "\n".join(details) +
                           f"\n\nDuplicate event IDs cause the Dem module to confuse "
                           f"different fault conditions, leading to incorrect DTC "
                           f"mapping and wrong diagnostic responses.",
                           suggestion="Assign unique values to each DEM event")

    def _check_unused_events(self, event_defs: dict, event_usage: dict):
        """Check that all defined events are actually reported by some module."""
        used_names = set(event_usage.keys())
        for name, info in event_defs.items():
            if name not in used_names:
                self._warn("Dem", "DEM_EVT-004",
                           f"Unused DEM event: {name}",
                           f"DEM event '{name}' (value={info['value']}) is defined in "
                           f"{info['file']}:{info['line']} but no module calls "
                           f"Dem_SetEventStatus() or Dem_ReportErrorStatus() with this ID. "
                           f"This may indicate dead configuration or a missing error "
                           f"detection in the BSW modules.",
                           file_path=info["file"], line_number=info["line"])

    def _check_event_reporting_modules(self, event_usage: dict, scan_result: ScanResult):
        """Summarize which modules report which events."""
        event_reporters = defaultdict(set)
        for event_name, usages in event_usage.items():
            for caller_mod, _, _, _ in usages:
                event_reporters[event_name].add(caller_mod)

        for event_name, reporters in event_reporters.items():
            if len(reporters) > 1:
                self._info("Dem", "DEM_EVT-005",
                           f"Event {event_name} reported by {len(reporters)} modules: "
                           f"{', '.join(sorted(reporters))}",
                           f"DEM event '{event_name}' is reported by multiple modules: "
                           f"{', '.join(sorted(reporters))}. This is normal for shared "
                           f"fault conditions but verify all modules report the correct "
                           f"status (PASSED/FAILED).")
