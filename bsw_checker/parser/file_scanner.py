"""File scanner for discovering and classifying BSW module files."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from .c_parser import ParsedFile, parse_file


# Known AUTOSAR BSW module names
KNOWN_BSW_MODULES = {
    # Communication Stack
    "Com", "PduR", "CanIf", "Can", "CanSM", "CanTp", "CanNm",
    "LinIf", "LinSM", "LinTp", "Lin",
    "FrIf", "FrSM", "FrTp", "FrNm", "Fr",
    "SoAd", "TcpIp", "EthIf", "EthSM", "Eth",
    "Nm", "ComM", "IpduM",
    # System Services
    "Os", "EcuM", "BswM", "Det", "Dem", "SchM", "Rte",
    "WdgM", "WdgIf", "Wdg",
    # Memory Stack
    "NvM", "MemIf", "Fee", "Fls", "Ea", "Eep",
    # Diagnostic
    "Dcm", "Dem", "FiM",
    # I/O
    "IoHwAb", "Adc", "Dio", "Pwm", "Icu", "Gpt", "Spi", "Port",
    # Crypto
    "Csm", "CryIf", "Cry",
}

# File suffixes that indicate configuration files
CONFIG_SUFFIXES = ['_Cfg', '_PBcfg', '_Lcfg']
TYPE_SUFFIXES = ['_Types']
CALLBACK_SUFFIXES = ['_Cbk']
INTERNAL_SUFFIXES = ['_Internal', '_Priv']


@dataclass
class ModuleFiles:
    """Collection of files belonging to a single BSW module."""
    module_name: str
    source_files: list[str] = field(default_factory=list)      # .c files
    header_files: list[str] = field(default_factory=list)      # .h files
    config_files: list[str] = field(default_factory=list)      # _Cfg.h, _Cfg.c
    type_files: list[str] = field(default_factory=list)        # _Types.h
    callback_files: list[str] = field(default_factory=list)    # _Cbk.h
    parsed_files: list[ParsedFile] = field(default_factory=list)

    @property
    def all_files(self) -> list[str]:
        return (self.source_files + self.header_files +
                self.config_files + self.type_files + self.callback_files)


@dataclass
class ScanResult:
    """Result of scanning a BSW directory."""
    root_path: str
    modules: dict[str, ModuleFiles] = field(default_factory=dict)
    unknown_files: list[str] = field(default_factory=list)
    total_files: int = 0

    @property
    def module_names(self) -> list[str]:
        return sorted(self.modules.keys())


def _classify_file(file_path: str) -> tuple[str, str]:
    """Classify a file into module name and file type.

    Returns:
        (module_name, file_type) where file_type is one of:
        'source', 'header', 'config', 'types', 'callback', 'unknown'
    """
    stem = Path(file_path).stem
    ext = Path(file_path).suffix.lower()

    if ext not in ('.c', '.h'):
        return ("", "unknown")

    # Check for known suffixes
    for suffix in CONFIG_SUFFIXES:
        if stem.endswith(suffix):
            module = stem[:-len(suffix)]
            if module in KNOWN_BSW_MODULES:
                return (module, "config")

    for suffix in TYPE_SUFFIXES:
        if stem.endswith(suffix):
            module = stem[:-len(suffix)]
            if module in KNOWN_BSW_MODULES:
                return (module, "types")

    for suffix in CALLBACK_SUFFIXES:
        if stem.endswith(suffix):
            module = stem[:-len(suffix)]
            if module in KNOWN_BSW_MODULES:
                return (module, "callback")

    for suffix in INTERNAL_SUFFIXES:
        if stem.endswith(suffix):
            module = stem[:-len(suffix)]
            if module in KNOWN_BSW_MODULES:
                file_type = "source" if ext == '.c' else "header"
                return (module, file_type)

    # Check if stem is a known module name directly
    if stem in KNOWN_BSW_MODULES:
        file_type = "source" if ext == '.c' else "header"
        return (stem, file_type)

    # Try prefix matching: e.g., PduR_Com.h -> PduR module
    for module in sorted(KNOWN_BSW_MODULES, key=len, reverse=True):
        if stem.startswith(module + '_') or stem.startswith(module):
            file_type = "source" if ext == '.c' else "header"
            return (module, file_type)

    return ("", "unknown")


def scan_directory(root_path: str, parse_files: bool = True,
                   use_clang: bool = False) -> ScanResult:
    """Scan a directory recursively for BSW C/H files.

    Args:
        root_path: Root directory to scan.
        parse_files: If True, parse each file immediately.
        use_clang: If True, use libclang AST parser instead of regex.

    Returns:
        ScanResult with classified modules and parsed files.
    """
    result = ScanResult(root_path=root_path)

    for dirpath, _, filenames in os.walk(root_path):
        for filename in filenames:
            ext = Path(filename).suffix.lower()
            if ext not in ('.c', '.h'):
                continue

            file_path = os.path.join(dirpath, filename)
            result.total_files += 1

            module_name, file_type = _classify_file(file_path)

            if not module_name or file_type == "unknown":
                result.unknown_files.append(file_path)
                continue

            if module_name not in result.modules:
                result.modules[module_name] = ModuleFiles(module_name=module_name)

            mod = result.modules[module_name]

            if file_type == "source":
                mod.source_files.append(file_path)
            elif file_type == "header":
                mod.header_files.append(file_path)
            elif file_type == "config":
                mod.config_files.append(file_path)
            elif file_type == "types":
                mod.type_files.append(file_path)
            elif file_type == "callback":
                mod.callback_files.append(file_path)

            if parse_files and not use_clang:
                parsed = parse_file(file_path)
                parsed.module_name = module_name
                mod.parsed_files.append(parsed)

    # Clang-based parsing (after all files classified)
    if parse_files and use_clang:
        try:
            from .clang_parser import ClangParser, CLANG_AVAILABLE
            if CLANG_AVAILABLE:
                _run_clang_parse(root_path, result)
            else:
                # Fallback to regex
                for mod_name, mod_files in result.modules.items():
                    for fp in mod_files.all_files:
                        parsed = parse_file(fp)
                        parsed.module_name = mod_name
                        mod_files.parsed_files.append(parsed)
        except ImportError:
            for mod_name, mod_files in result.modules.items():
                for fp in mod_files.all_files:
                    parsed = parse_file(fp)
                    parsed.module_name = mod_name
                    mod_files.parsed_files.append(parsed)

    return result


def _run_clang_parse(root_path: str, result: ScanResult):
    """Run clang parser and convert results to ParsedFile format."""
    from .clang_parser import ClangParser
    from .c_parser import (
        FunctionInfo, FunctionCall, MacroDefine, TypedefInfo,
        IncludeInfo, FunctionPointer, ParsedFile, IncludeGuard,
    )
    import os

    stubs_dir = os.path.join(os.path.dirname(__file__), 'autosar_stubs')
    parser = ClangParser(include_paths=[stubs_dir])

    # Parse all C files (they include their .h files)
    all_c_files = []
    file_to_module = {}
    for mod_name, mod_files in result.modules.items():
        for fp in mod_files.all_files:
            file_to_module[os.path.abspath(fp)] = mod_name
            if fp.endswith('.c'):
                all_c_files.append(fp)

    for c_file in all_c_files:
        mod_name = file_to_module.get(os.path.abspath(c_file), "")
        if not mod_name:
            continue

        try:
            clang_result = parser.parse_file(c_file, include_dir=root_path)
        except Exception:
            continue

        # Convert ClangParsedFile → ParsedFile
        parsed = ParsedFile(
            file_path=c_file,
            module_name=mod_name,
            raw_content=open(c_file, encoding='utf-8', errors='replace').read(),
        )

        for cf in clang_result.functions:
            parsed.functions.append(FunctionInfo(
                name=cf.name,
                return_type=cf.return_type,
                params=[f'{p["type"]} {p["name"]}' for p in cf.params],
                file_path=cf.file_path,
                line_number=cf.line_number,
                is_definition=cf.is_definition,
            ))

        for cc in clang_result.calls:
            parsed.function_calls.append(FunctionCall(
                caller_func=cc.caller_func,
                callee_func=cc.callee_func,
                arguments=', '.join(a['expr'] for a in cc.arguments),
                file_path=cc.file_path,
                line_number=cc.line_number,
            ))

        for cm in clang_result.macros:
            parsed.macros.append(MacroDefine(
                name=cm.name,
                value=cm.tokens,
                file_path=cm.file_path,
                line_number=cm.line_number,
            ))

        for ct in clang_result.typedefs:
            parsed.typedefs.append(TypedefInfo(
                name=ct.name,
                kind="typedef",
                file_path=ct.file_path,
                line_number=ct.line_number,
            ))

        for ci_inc in clang_result.includes:
            parsed.includes.append(IncludeInfo(
                header=ci_inc.header,
                is_system=ci_inc.is_system,
                file_path=ci_inc.file_path,
                line_number=ci_inc.line_number,
            ))

        result.modules[mod_name].parsed_files.append(parsed)

    # Parse .h-only modules (no .c file)
    for mod_name, mod_files in result.modules.items():
        if mod_files.parsed_files:
            continue
        for fp in mod_files.header_files + mod_files.config_files + mod_files.type_files:
            from .c_parser import parse_file as regex_parse_file
            parsed = regex_parse_file(fp)
            parsed.module_name = mod_name
            mod_files.parsed_files.append(parsed)
