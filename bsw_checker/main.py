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
from .checkers.schm_checker import SchmChecker
from .checkers.dem_event_checker import DemEventChecker
from .checkers.buffer_checker import BufferChecker
from .checkers.callback_chain_checker import CallbackChainChecker
from .checkers.config_checker import ConfigChecker
from .checkers.naming_checker import NamingChecker
from .checkers.version_compat_checker import VersionCompatChecker
from .checkers.code_quality_checker import CodeQualityChecker
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
    "schm": SchmChecker,
    "dem_event": DemEventChecker,
    "buffer": BufferChecker,
    "chain": CallbackChainChecker,
    "config": ConfigChecker,
    "naming": NamingChecker,
    "compat": VersionCompatChecker,
    "quality": CodeQualityChecker,
}


def run_checks(target_path: str,
               version: str = "4.4.0",
               modules: list[str] | None = None,
               checkers: list[str] | None = None,
               version_map: dict[str, str] | None = None,
               use_clang: bool = False,
               include_paths: list[str] | None = None) -> Reporter:
    """Run BSW verification checks and return a Reporter.

    Args:
        target_path: Path to directory containing BSW C/H files.
        version: Default AUTOSAR version (used if module not in version_map).
        modules: List of module names to check (None = all found).
        checkers: List of checker names to run (None = all).
        version_map: Per-module AUTOSAR version override {module_name: version}.

    Returns:
        Reporter instance with all results.
    """
    registry = ModuleRegistry()

    # Scan directory
    scan_result = scan_directory(target_path, use_clang=use_clang,
                                 include_paths=include_paths)

    # Filter modules if specified
    if modules:
        filtered = {}
        for m in modules:
            if m in scan_result.modules:
                filtered[m] = scan_result.modules[m]
        scan_result.modules = filtered

    # Build version_map: per-module version assignment
    if version_map is None:
        version_map = {}
    # Fill defaults for modules not explicitly assigned
    for mod_name in scan_result.modules:
        if mod_name not in version_map:
            version_map[mod_name] = version

    # Select checkers
    checker_names = checkers or list(ALL_CHECKERS.keys())
    checker_classes = [ALL_CHECKERS[name] for name in checker_names
                       if name in ALL_CHECKERS]

    # Run checkers
    reports = []
    for checker_cls in checker_classes:
        checker = checker_cls(registry, version_map, version)
        report = checker.check(scan_result)
        reports.append(report)

    return Reporter(
        results=reports,
        version_map=version_map,
        default_version=version,
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
  %(prog)s /path/to/bsw --module-version Com:4.4.0,CanIf:4.0.3,PduR:4.9.0
  %(prog)s /path/to/bsw --format json --output report.json
  %(prog)s --gui
        """)

    parser.add_argument("path", nargs="?",
                        help="Path to BSW source directory")
    parser.add_argument("--version", "-v", default="4.4.0",
                        choices=SUPPORTED_VERSIONS,
                        help="Default AUTOSAR version (default: 4.4.0)")
    parser.add_argument("--modules", "-m",
                        help="Comma-separated list of modules to check")
    parser.add_argument("--module-version", dest="module_version",
                        help="Per-module version override: Com:4.4.0,CanIf:4.0.3")
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
    parser.add_argument("--clang", action="store_true",
                        help="Use libclang AST parser (hybrid: regex + clang overlay)")
    parser.add_argument("--include-path", "-I", action="append", default=[],
                        help="Additional include paths for clang parser (can repeat: -I /path1 -I /path2)")

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

    # Parse per-module version overrides
    version_map = None
    if args.module_version:
        version_map = {}
        for entry in args.module_version.split(','):
            if ':' in entry:
                mod, ver = entry.split(':', 1)
                if ver in SUPPORTED_VERSIONS:
                    version_map[mod.strip()] = ver.strip()
                else:
                    print(f"Warning: Unknown version '{ver}' for module '{mod}', "
                          f"using default", file=sys.stderr)

    reporter = run_checks(target_path, args.version, modules, checkers,
                          version_map, use_clang=args.clang,
                          include_paths=args.include_path or None)

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

    sys.exit(1 if reporter.total_fail > 0 else 0)


if __name__ == "__main__":
    main()
