"""GCC Preprocessor-based parser for AUTOSAR BSW analysis.

Uses `gcc -E` to fully preprocess C files, then parses the expanded
output with regex. This resolves ALL macros, #ifdef, and includes.

Advantages over regex-only:
- FUNC(), P2CONST(), VAR() macros fully expanded
- #ifdef COM_DEV_ERROR_DETECT correctly evaluated
- All #include files inlined
- Macro values (COM_MODULE_ID=50) expanded at usage sites

Advantages over libclang:
- Uses standard GCC (available on any build system)
- Preserves #line directives for source file tracking
- Works with cross-compiler flags (-mcpu, -mthumb, etc.)
"""

import os
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from .c_parser import (
    FunctionInfo, FunctionCall, MacroDefine, TypedefInfo,
    IncludeInfo, FunctionPointer, ParsedFile, IncludeGuard,
    _clean_return_type, _KEYWORDS,
)

# Regex for #line directives (gcc -E output)
_RE_LINE_DIRECTIVE = re.compile(
    r'^#\s+(\d+)\s+"([^"]+)"'
)

# Same function regex but applied to preprocessed code (cleaner)
_RE_FUNCTION_PP = re.compile(
    r'^([\w][\w\s*]*?)\s+'
    r'(\w+)\s*'
    r'\(([^)]*)\)\s*'
    r'([{;])',
    re.MULTILINE
)

_RE_FUNC_CALL_PP = re.compile(
    r'\b(\w+)\s*\(([^;{]*?)\)\s*;',
    re.MULTILINE
)

_RE_TYPEDEF_STRUCT_PP = re.compile(
    r'typedef\s+(struct|union|enum)\s*\w*\s*\{([^}]*)\}\s*(\w+)\s*;',
    re.DOTALL
)


@dataclass
class PreprocessResult:
    """Result of gcc -E preprocessing."""
    success: bool
    preprocessed_code: str = ""
    original_file: str = ""
    errors: list[str] = field(default_factory=list)
    # Map: line_number_in_pp -> (original_file, original_line)
    line_map: dict[int, tuple[str, int]] = field(default_factory=dict)


def gcc_preprocess(file_path: str,
                   include_paths: list[str] | None = None,
                   defines: dict[str, str] | None = None,
                   gcc_path: str = "gcc") -> PreprocessResult:
    """Run gcc -E on a C file and return preprocessed output.

    Args:
        file_path: Path to the .c file.
        include_paths: List of -I include directories.
        defines: Dict of -D macro definitions {name: value}.
        gcc_path: Path to gcc binary (can be cross-compiler like arm-none-eabi-gcc).
    """
    cmd = [gcc_path, "-E", "-P"]  # -P removes #line directives for clean output

    # Add include paths
    file_dir = os.path.dirname(os.path.abspath(file_path))
    cmd.append(f"-I{file_dir}")

    if include_paths:
        for p in include_paths:
            cmd.append(f"-I{p}")

    # Add defines
    if defines:
        for name, value in defines.items():
            if value:
                cmd.append(f"-D{name}={value}")
            else:
                cmd.append(f"-D{name}")

    # Standard AUTOSAR-friendly flags
    cmd.extend(["-std=c99", "-w"])  # -w suppresses warnings

    cmd.append(file_path)

    result = PreprocessResult(success=False, original_file=file_path)

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if proc.returncode == 0:
            result.success = True
            result.preprocessed_code = proc.stdout
        else:
            result.errors.append(proc.stderr.strip())
            # Try again without -P to get #line info for error tracking
            cmd_with_lines = [c for c in cmd if c != "-P"]
            proc2 = subprocess.run(
                cmd_with_lines, capture_output=True, text=True, timeout=30)
            if proc2.returncode == 0:
                result.success = True
                result.preprocessed_code = proc2.stdout
                result.line_map = _build_line_map(proc2.stdout)
            else:
                result.errors.append(proc2.stderr.strip())

    except FileNotFoundError:
        result.errors.append(f"gcc not found at '{gcc_path}'. Install GCC or specify path.")
    except subprocess.TimeoutExpired:
        result.errors.append("gcc -E timed out after 30 seconds")

    return result


def gcc_preprocess_with_line_tracking(file_path: str,
                                        include_paths: list[str] | None = None,
                                        defines: dict[str, str] | None = None,
                                        gcc_path: str = "gcc") -> PreprocessResult:
    """Run gcc -E WITH #line directives for source location tracking."""
    cmd = [gcc_path, "-E"]  # No -P: keep #line directives

    file_dir = os.path.dirname(os.path.abspath(file_path))
    cmd.append(f"-I{file_dir}")

    if include_paths:
        for p in include_paths:
            cmd.append(f"-I{p}")

    if defines:
        for name, value in defines.items():
            cmd.append(f"-D{name}={value}" if value else f"-D{name}")

    cmd.extend(["-std=c99", "-w", file_path])

    result = PreprocessResult(success=False, original_file=file_path)

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if proc.returncode == 0:
            result.success = True
            result.preprocessed_code = proc.stdout
            result.line_map = _build_line_map(proc.stdout)
        else:
            result.errors.append(proc.stderr.strip())
    except FileNotFoundError:
        result.errors.append(f"gcc not found at '{gcc_path}'")
    except subprocess.TimeoutExpired:
        result.errors.append("gcc -E timed out")

    return result


def _build_line_map(pp_output: str) -> dict[int, tuple[str, int]]:
    """Build mapping from preprocessed line numbers to original source locations."""
    line_map = {}
    current_file = ""
    current_orig_line = 1
    pp_line_no = 0

    for line in pp_output.split('\n'):
        pp_line_no += 1
        m = _RE_LINE_DIRECTIVE.match(line)
        if m:
            current_orig_line = int(m.group(1))
            current_file = m.group(2)
        else:
            line_map[pp_line_no] = (current_file, current_orig_line)
            current_orig_line += 1

    return line_map


def parse_preprocessed(pp_code: str, original_file: str,
                       line_map: dict | None = None) -> ParsedFile:
    """Parse gcc -E preprocessed output and extract all information.

    Since macros are already expanded, regex parsing is highly accurate.
    """
    result = ParsedFile(
        file_path=original_file,
        raw_content=pp_code,
    )

    # Remove empty lines and normalize
    clean = pp_code

    # Parse functions (much cleaner after preprocessing)
    for m in _RE_FUNCTION_PP.finditer(clean):
        ret_type = _clean_return_type(m.group(1).strip())
        func_name = m.group(2)
        params_raw = m.group(3).strip()
        end_char = m.group(4)

        if func_name in _KEYWORDS:
            continue

        params = []
        if params_raw and params_raw != 'void':
            params = [p.strip() for p in params_raw.split(',') if p.strip()]

        is_def = end_char == '{'
        pp_line = clean[:m.start()].count('\n') + 1

        # Map back to original source location
        orig_file = original_file
        orig_line = pp_line
        if line_map and pp_line in line_map:
            orig_file, orig_line = line_map[pp_line]

        result.functions.append(FunctionInfo(
            name=func_name,
            return_type=ret_type,
            params=params,
            file_path=orig_file,
            line_number=orig_line,
            is_definition=is_def,
        ))

    # Parse function calls
    for m in _RE_FUNC_CALL_PP.finditer(clean):
        callee = m.group(1)
        if callee in _KEYWORDS:
            continue
        args = m.group(2).strip()
        pp_line = clean[:m.start()].count('\n') + 1

        orig_file = original_file
        orig_line = pp_line
        if line_map and pp_line in line_map:
            orig_file, orig_line = line_map[pp_line]

        result.function_calls.append(FunctionCall(
            caller_func="",
            callee_func=callee,
            arguments=args,
            file_path=orig_file,
            line_number=orig_line,
        ))

    # Parse typedefs
    for m in _RE_TYPEDEF_STRUCT_PP.finditer(clean):
        kind = m.group(1)
        body = m.group(2)
        name = m.group(3)
        members = [line.strip().rstrip(';') for line in body.strip().split('\n')
                    if line.strip()]
        pp_line = clean[:m.start()].count('\n') + 1

        result.typedefs.append(TypedefInfo(
            name=name,
            kind=kind,
            members=members,
            file_path=original_file,
            line_number=pp_line,
        ))

    return result


def gcc_parse_file(file_path: str,
                   include_paths: list[str] | None = None,
                   defines: dict[str, str] | None = None,
                   gcc_path: str = "gcc") -> ParsedFile:
    """Convenience: preprocess with gcc -E, then parse the result."""
    pp = gcc_preprocess_with_line_tracking(
        file_path, include_paths, defines, gcc_path)

    if not pp.success:
        # Fallback to regex on original file
        from .c_parser import parse_file
        result = parse_file(file_path)
        result.raw_content += "\n/* gcc -E errors: " + "; ".join(pp.errors) + " */"
        return result

    return parse_preprocessed(pp.preprocessed_code, file_path, pp.line_map)


def check_gcc_available(gcc_path: str = "gcc") -> bool:
    """Check if gcc is available."""
    try:
        proc = subprocess.run([gcc_path, "--version"],
                              capture_output=True, timeout=5)
        return proc.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
