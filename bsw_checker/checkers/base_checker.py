"""Base checker class for all BSW verification checkers."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from ..parser.file_scanner import ScanResult
from ..spec.module_registry import ModuleRegistry


class Severity(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"
    INFO = "INFO"


@dataclass
class CheckResult:
    """Result of a single check."""
    severity: Severity
    checker_name: str
    module_name: str
    rule_id: str
    title: str
    description: str
    file_path: str = ""
    line_number: int = 0
    expected: str = ""
    actual: str = ""
    suggestion: str = ""
    autosar_ref: str = ""  # AUTOSAR SWS reference
    verified: Optional[bool] = None  # None=not verified, True=confirmed, False=rejected


@dataclass
class CheckerReport:
    """Collection of results from a checker."""
    checker_name: str
    results: list[CheckResult] = field(default_factory=list)

    @property
    def pass_count(self) -> int:
        return sum(1 for r in self.results if r.severity == Severity.PASS)

    @property
    def fail_count(self) -> int:
        return sum(1 for r in self.results if r.severity == Severity.FAIL)

    @property
    def warn_count(self) -> int:
        return sum(1 for r in self.results if r.severity == Severity.WARN)


class BaseChecker:
    """Abstract base class for all checkers."""

    name: str = "base"
    description: str = "Base checker"

    def __init__(self, registry: ModuleRegistry, version: str):
        self.registry = registry
        self.version = version
        self.report = CheckerReport(checker_name=self.name)

    def check(self, scan_result: ScanResult) -> CheckerReport:
        """Run all checks. Override in subclasses."""
        raise NotImplementedError

    def _add_result(self, severity: Severity, module: str, rule_id: str,
                    title: str, description: str, **kwargs):
        self.report.results.append(CheckResult(
            severity=severity,
            checker_name=self.name,
            module_name=module,
            rule_id=rule_id,
            title=title,
            description=description,
            **kwargs,
        ))

    def _pass(self, module: str, rule_id: str, title: str, desc: str = "", **kw):
        self._add_result(Severity.PASS, module, rule_id, title, desc, **kw)

    def _fail(self, module: str, rule_id: str, title: str, desc: str = "", **kw):
        self._add_result(Severity.FAIL, module, rule_id, title, desc, **kw)

    def _warn(self, module: str, rule_id: str, title: str, desc: str = "", **kw):
        self._add_result(Severity.WARN, module, rule_id, title, desc, **kw)

    def _info(self, module: str, rule_id: str, title: str, desc: str = "", **kw):
        self._add_result(Severity.INFO, module, rule_id, title, desc, **kw)
