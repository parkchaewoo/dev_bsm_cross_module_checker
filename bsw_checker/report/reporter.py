"""Report engine for BSW checker results with detailed explanations."""

import json
import os
from datetime import datetime
from typing import Optional

from ..checkers.base_checker import CheckerReport, CheckResult, Severity


class Reporter:
    """Generates formatted reports from checker results."""

    def __init__(self, results: list[CheckerReport], version: str,
                 target_path: str, modules_checked: list[str]):
        self.results = results
        self.version = version
        self.target_path = target_path
        self.modules_checked = modules_checked

    @property
    def all_checks(self) -> list[CheckResult]:
        checks = []
        for report in self.results:
            checks.extend(report.results)
        return checks

    @property
    def total_pass(self) -> int:
        return sum(1 for c in self.all_checks if c.severity == Severity.PASS)

    @property
    def total_fail(self) -> int:
        return sum(1 for c in self.all_checks if c.severity == Severity.FAIL)

    @property
    def total_warn(self) -> int:
        return sum(1 for c in self.all_checks if c.severity == Severity.WARN)

    @property
    def total_info(self) -> int:
        return sum(1 for c in self.all_checks if c.severity == Severity.INFO)

    def format_console(self, show_pass: bool = True, show_info: bool = False) -> str:
        """Format results for console output."""
        lines = []
        lines.append("=" * 70)
        lines.append("  BSW AUTOSAR Spec Verification Report")
        lines.append("=" * 70)
        lines.append(f"  Target:    {self.target_path}")
        lines.append(f"  Version:   AUTOSAR {self.version}")
        lines.append(f"  Modules:   {', '.join(self.modules_checked)}")
        lines.append(f"  Date:      {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 70)
        lines.append("")

        # Group by module then by checker
        by_module = {}
        for check in self.all_checks:
            mod = check.module_name
            if mod not in by_module:
                by_module[mod] = []
            by_module[mod].append(check)

        for mod in sorted(by_module.keys()):
            checks = by_module[mod]
            fails = [c for c in checks if c.severity == Severity.FAIL]
            warns = [c for c in checks if c.severity == Severity.WARN]
            passes = [c for c in checks if c.severity == Severity.PASS]

            mod_status = "FAIL" if fails else ("WARN" if warns else "PASS")
            status_icon = {"PASS": "[PASS]", "FAIL": "[FAIL]", "WARN": "[WARN]"}[mod_status]

            lines.append(f"--- {status_icon} {mod} ---")

            for check in checks:
                if check.severity == Severity.PASS and not show_pass:
                    continue
                if check.severity == Severity.INFO and not show_info:
                    continue

                icon = self._severity_icon(check.severity)
                lines.append(f"  {icon} [{check.rule_id}] {check.title}")

                if check.severity in (Severity.FAIL, Severity.WARN):
                    # Show detailed description for failures/warnings
                    desc_lines = check.description.split('\n')
                    for dl in desc_lines:
                        lines.append(f"      {dl}")

                    if check.file_path:
                        loc = check.file_path
                        if check.line_number:
                            loc += f":{check.line_number}"
                        lines.append(f"      Location: {loc}")

                    if check.expected:
                        lines.append(f"      Expected: {check.expected}")
                    if check.actual:
                        lines.append(f"      Actual:   {check.actual}")
                    if check.suggestion:
                        lines.append(f"      Fix: {check.suggestion}")
                    if check.autosar_ref:
                        lines.append(f"      Ref: {check.autosar_ref}")
                    lines.append("")

            lines.append("")

        # Summary
        total = len(self.all_checks)
        lines.append("=" * 70)
        lines.append(f"  Summary: {total} checks | "
                      f"{self.total_pass} PASS | "
                      f"{self.total_fail} FAIL | "
                      f"{self.total_warn} WARN | "
                      f"{self.total_info} INFO")
        lines.append("=" * 70)

        return "\n".join(lines)

    def format_json(self) -> str:
        """Format results as JSON."""
        data = {
            "report": {
                "tool": "BSW AUTOSAR Spec Verification Tool",
                "version": "1.0.0",
                "target_path": self.target_path,
                "autosar_version": self.version,
                "modules_checked": self.modules_checked,
                "timestamp": datetime.now().isoformat(),
            },
            "summary": {
                "total": len(self.all_checks),
                "pass": self.total_pass,
                "fail": self.total_fail,
                "warn": self.total_warn,
                "info": self.total_info,
            },
            "results": [],
        }

        for check in self.all_checks:
            entry = {
                "severity": check.severity.value,
                "checker": check.checker_name,
                "module": check.module_name,
                "rule_id": check.rule_id,
                "title": check.title,
                "description": check.description,
                "verified": check.verified,
            }
            if check.file_path:
                entry["file_path"] = check.file_path
            if check.line_number:
                entry["line_number"] = check.line_number
            if check.expected:
                entry["expected"] = check.expected
            if check.actual:
                entry["actual"] = check.actual
            if check.suggestion:
                entry["suggestion"] = check.suggestion
            if check.autosar_ref:
                entry["autosar_ref"] = check.autosar_ref

            data["results"].append(entry)

        return json.dumps(data, indent=2, ensure_ascii=False)

    def get_results_for_gui(self) -> list[dict]:
        """Get results in a format suitable for GUI display."""
        results = []
        for check in self.all_checks:
            results.append({
                "severity": check.severity.value,
                "checker": check.checker_name,
                "module": check.module_name,
                "rule_id": check.rule_id,
                "title": check.title,
                "description": check.description,
                "file_path": check.file_path,
                "line_number": check.line_number,
                "expected": check.expected,
                "actual": check.actual,
                "suggestion": check.suggestion,
                "autosar_ref": check.autosar_ref,
                "verified": check.verified,
            })
        return results

    @staticmethod
    def _severity_icon(severity: Severity) -> str:
        return {
            Severity.PASS: "OK ",
            Severity.FAIL: "NG ",
            Severity.WARN: "?? ",
            Severity.INFO: "-- ",
        }[severity]
