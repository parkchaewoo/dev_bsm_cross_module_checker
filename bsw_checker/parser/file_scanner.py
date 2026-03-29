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

CONFIG_SUFFIXES = ['_Cfg', '_PBcfg', '_Lcfg']
TYPE_SUFFIXES = ['_Types']
CALLBACK_SUFFIXES = ['_Cbk']
INTERNAL_SUFFIXES = ['_Internal', '_Priv']


@dataclass
class ModuleFiles:
    """Collection of files belonging to a single BSW module."""
    module_name: str
    source_files: list[str] = field(default_factory=list)
    header_files: list[str] = field(default_factory=list)
    config_files: list[str] = field(default_factory=list)
    type_files: list[str] = field(default_factory=list)
    callback_files: list[str] = field(default_factory=list)
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
    """Classify a file into (module_name, file_type)."""
    stem = Path(file_path).stem
    ext = Path(file_path).suffix.lower()

    if ext not in ('.c', '.h'):
        return ("", "unknown")

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
                return (module, "source" if ext == '.c' else "header")

    if stem in KNOWN_BSW_MODULES:
        return (stem, "source" if ext == '.c' else "header")

    for module in sorted(KNOWN_BSW_MODULES, key=len, reverse=True):
        if stem.startswith(module + '_') or stem.startswith(module):
            return (module, "source" if ext == '.c' else "header")

    return ("", "unknown")


def scan_directory(root_path: str, parse_files: bool = True,
                   force_regex: bool = False,
                   include_paths: list[str] | None = None,
                   gcc_defines: dict[str, str] | None = None,
                   gcc_path: str = "gcc") -> ScanResult:
    """Scan a directory recursively for BSW C/H files.

    Parsing modes:
    - Default: gcc -E for .c files (macro expansion) + regex for .h files
    - force_regex=True: regex only (no gcc dependency)
    - Auto-fallback to regex if gcc is not available

    Args:
        root_path: Root directory to scan.
        parse_files: If True, parse each file immediately.
        force_regex: If True, skip gcc and use regex only.
        include_paths: Additional -I include directories for gcc.
        gcc_defines: -D preprocessor defines for gcc.
        gcc_path: Path to gcc binary.
    """
    result = ScanResult(root_path=root_path)

    # Step 1: discover and classify files
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

    if not parse_files:
        return result

    # Step 2: determine parser and parse files
    use_gcc = False
    if not force_regex:
        from .gcc_parser import check_gcc_available
        use_gcc = check_gcc_available(gcc_path)

    if use_gcc:
        _parse_with_gcc(root_path, result, include_paths, gcc_defines, gcc_path)
    else:
        _parse_with_regex(result)

    return result


def _parse_with_regex(result: ScanResult):
    """Parse all files using regex only."""
    for mod_name, mod_files in result.modules.items():
        for fp in mod_files.all_files:
            parsed = parse_file(fp)
            parsed.module_name = mod_name
            mod_files.parsed_files.append(parsed)


def _parse_with_gcc(root_path: str, result: ScanResult,
                    include_paths: list[str] | None = None,
                    gcc_defines: dict[str, str] | None = None,
                    gcc_path: str = "gcc"):
    """Parse files: .h with regex (for #define values), .c with gcc -E.

    This gives the best of both worlds:
    - .h files: regex extracts #define PDU_ID values, include guards, typedefs
    - .c files: gcc -E expands all macros then regex parses the clean output
    """
    from .gcc_parser import gcc_parse_file
    from .c_parser import parse_file as regex_parse_file

    stubs_dir = os.path.join(os.path.dirname(__file__), 'autosar_stubs')
    all_includes = [stubs_dir, os.path.abspath(root_path)]
    if include_paths:
        all_includes.extend(include_paths)

    for mod_name, mod_files in result.modules.items():
        # .h files: regex (preserves #define name=value pairs)
        for fp in (mod_files.header_files + mod_files.config_files +
                   mod_files.type_files + mod_files.callback_files):
            parsed = regex_parse_file(fp)
            parsed.module_name = mod_name
            mod_files.parsed_files.append(parsed)

        # .c files: gcc -E preprocessed + tree-dump type enrichment
        for fp in mod_files.source_files:
            parsed = gcc_parse_file(fp, all_includes, gcc_defines, gcc_path)
            parsed.module_name = mod_name
            try:
                parsed.raw_content = open(fp, encoding='utf-8', errors='replace').read()
            except Exception:
                pass
            mod_files.parsed_files.append(parsed)
