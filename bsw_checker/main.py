"""Main entry point for BSW AUTOSAR Spec Verification Tool."""

import argparse
import sys
from pathlib import Path

from .parser.file_scanner import scan_directory
from .spec.module_registry import ModuleRegistry, SUPPORTED_VERSIONS
from .checkers.api_checker import ApiChecker
from .checkers.include_checker import IncludeChecker
from .checkers.type_checker import TypeChecker
from .checkers.cross_module_checker import CrossModuleChecker
from .checkers.pdu_checker import PduChecker
from .checkers.init_checker import InitChecker
from .checkers.det_checker import DetChecker
from .checkers.function_pointer_checker import FunctionPointerChecker
from .report.reporter import Reporter


ALL_CHECKERS = {
    "api": ApiChecker,
    "include": IncludeChecker,
    "type": TypeChecker,
    "cross": CrossModuleChecker,
    "pdu": PduChecker,
    "init": InitChecker,
    "det": DetChecker,
    "fptr": FunctionPointerChecker,
}


def run_checks(target_path: str, version: str = "4.4.0",
               modules: list[str] | None = None,
               checkers: list[str] | None = None) -> Reporter:
    """Run BSW verification checks and return a Reporter.

    Args:
        target_path: Path to directory containing BSW C/H files.
        version: AUTOSAR version to check against.
        modules: List of module names to check (None = all found).
        checkers: List of checker names to run (None = all).

    Returns:
        Reporter instance with all results.
    """
    registry = ModuleRegistry()

    # Scan directory
    scan_result = scan_directory(target_path)

    # Filter modules if specified
    if modules:
        filtered = {}
        for m in modules:
            if m in scan_result.modules:
                filtered[m] = scan_result.modules[m]
        scan_result.modules = filtered

    # Select checkers
    checker_names = checkers or list(ALL_CHECKERS.keys())
    checker_classes = [ALL_CHECKERS[name] for name in checker_names
                       if name in ALL_CHECKERS]

    # Run checkers
    reports = []
    for checker_cls in checker_classes:
        checker = checker_cls(registry, version)
        report = checker.check(scan_result)
        reports.append(report)

    return Reporter(
        results=reports,
        version=version,
        target_path=target_path,
        modules_checked=scan_result.module_names,
    )


def main():
    parser = argparse.ArgumentParser(
        description="BSW AUTOSAR Spec Verification Tool - "
                    "Check BSW modules against AUTOSAR specifications",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /path/to/bsw
  %(prog)s /path/to/bsw --version 4.4.0
  %(prog)s /path/to/bsw --modules Com,PduR,CanIf
  %(prog)s /path/to/bsw --check api,cross,pdu
  %(prog)s /path/to/bsw --format json --output report.json
  %(prog)s --gui
        """)

    parser.add_argument("path", nargs="?",
                        help="Path to BSW source directory")
    parser.add_argument("--version", "-v", default="4.4.0",
                        choices=SUPPORTED_VERSIONS,
                        help="AUTOSAR version to check against (default: 4.4.0)")
    parser.add_argument("--modules", "-m",
                        help="Comma-separated list of modules to check")
    parser.add_argument("--check", "-c",
                        help=f"Comma-separated checkers to run: "
                             f"{','.join(ALL_CHECKERS.keys())}")
    parser.add_argument("--format", "-f", default="console",
                        choices=["console", "json"],
                        help="Output format (default: console)")
    parser.add_argument("--output", "-o",
                        help="Output file path (default: stdout)")
    parser.add_argument("--show-pass", action="store_true",
                        help="Show passing checks in console output")
    parser.add_argument("--show-info", action="store_true",
                        help="Show info checks in console output")
    parser.add_argument("--gui", action="store_true",
                        help="Launch GUI mode")

    args = parser.parse_args()

    if args.gui:
        from .gui.app import launch_gui
        launch_gui()
        return

    if not args.path:
        parser.error("path is required unless --gui is specified")

    target_path = str(Path(args.path).resolve())
    if not Path(target_path).is_dir():
        print(f"Error: '{target_path}' is not a valid directory", file=sys.stderr)
        sys.exit(1)

    modules = args.modules.split(',') if args.modules else None
    checkers = args.check.split(',') if args.check else None

    reporter = run_checks(target_path, args.version, modules, checkers)

    if args.format == "json":
        output = reporter.format_json()
    else:
        output = reporter.format_console(
            show_pass=args.show_pass,
            show_info=args.show_info,
        )

    if args.output:
        Path(args.output).write_text(output, encoding='utf-8')
        print(f"Report written to {args.output}")
    else:
        print(output)

    # Exit with error code if any failures
    sys.exit(1 if reporter.total_fail > 0 else 0)


if __name__ == "__main__":
    main()
