"""C/H file parser for AUTOSAR BSW module analysis.

Extracts functions, macros, typedefs, includes, function pointers,
and function calls from C and H source files using regex patterns.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class FunctionInfo:
    """Parsed function declaration or definition."""
    name: str
    return_type: str
    params: list[str]
    file_path: str
    line_number: int
    is_definition: bool = False  # True if body exists, False if declaration only
    raw_text: str = ""


@dataclass
class MacroDefine:
    """Parsed #define macro."""
    name: str
    value: str
    file_path: str
    line_number: int
    raw_text: str = ""


@dataclass
class TypedefInfo:
    """Parsed typedef or struct."""
    name: str
    kind: str  # "typedef", "struct", "enum", "union"
    members: list[str] = field(default_factory=list)
    file_path: str = ""
    line_number: int = 0
    raw_text: str = ""


@dataclass
class IncludeInfo:
    """Parsed #include directive."""
    header: str
    is_system: bool  # True for <>, False for ""
    file_path: str = ""
    line_number: int = 0


@dataclass
class FunctionCall:
    """Parsed function call found in source."""
    caller_func: str  # function where the call is made
    callee_func: str  # function being called
    arguments: str    # raw argument text
    file_path: str = ""
    line_number: int = 0


@dataclass
class FunctionPointer:
    """Parsed function pointer declaration or assignment."""
    name: str
    return_type: str
    param_types: list[str]
    assigned_func: str  # the function assigned to the pointer, if detected
    file_path: str = ""
    line_number: int = 0
    raw_text: str = ""


@dataclass
class IncludeGuard:
    """Include guard info for a header file."""
    ifndef_macro: str
    define_macro: str
    file_path: str = ""


@dataclass
class ParsedFile:
    """Complete parse result for a single C/H file."""
    file_path: str
    module_name: str = ""
    functions: list[FunctionInfo] = field(default_factory=list)
    macros: list[MacroDefine] = field(default_factory=list)
    typedefs: list[TypedefInfo] = field(default_factory=list)
    includes: list[IncludeInfo] = field(default_factory=list)
    function_calls: list[FunctionCall] = field(default_factory=list)
    function_pointers: list[FunctionPointer] = field(default_factory=list)
    include_guard: Optional[IncludeGuard] = None
    raw_content: str = ""


# Regex patterns for C parsing
_RE_COMMENT_LINE = re.compile(r'//.*$', re.MULTILINE)
_RE_COMMENT_BLOCK = re.compile(r'/\*.*?\*/', re.DOTALL)

_RE_INCLUDE = re.compile(
    r'^\s*#\s*include\s+([<"])([^>"]+)[>"]',
    re.MULTILINE
)

_RE_DEFINE = re.compile(
    r'^\s*#\s*define\s+(\w+)\s*(.*?)(?:\s*\\$|\s*$)',
    re.MULTILINE
)

_RE_INCLUDE_GUARD_IFNDEF = re.compile(
    r'^\s*#\s*ifndef\s+(\w+_H\w*)\s*$',
    re.MULTILINE
)

_RE_INCLUDE_GUARD_DEFINE = re.compile(
    r'^\s*#\s*define\s+(\w+_H\w*)\s*$',
    re.MULTILINE
)

# Function declaration/definition pattern
# Matches: ReturnType FuncName(params) { or ;
_RE_FUNCTION = re.compile(
    r'^[ \t]*'
    r'((?:(?:FUNC|STATIC|extern|static|inline|const|volatile|unsigned|signed|long|short|void|struct|enum)\s+)*'
    r'(?:\w+(?:\s*\*\s*)?)+?)\s+'  # return type
    r'(\w+)\s*'                     # function name
    r'\(([^)]*)\)\s*'               # parameters
    r'([{;])',                       # body or declaration end
    re.MULTILINE
)

# Function call pattern
_RE_FUNC_CALL = re.compile(
    r'\b(\w+)\s*\(([^;{]*?)\)\s*;',
    re.MULTILINE
)

# Typedef struct pattern
_RE_TYPEDEF_STRUCT = re.compile(
    r'typedef\s+(struct|union|enum)\s*\w*\s*\{([^}]*)\}\s*(\w+)\s*;',
    re.DOTALL
)

# Simple typedef pattern
_RE_TYPEDEF_SIMPLE = re.compile(
    r'typedef\s+(.+?)\s+(\w+)\s*;'
)

# Function pointer typedef: typedef RetType (*Name)(Params);
_RE_FUNC_PTR_TYPEDEF = re.compile(
    r'typedef\s+([\w\s*]+?)\s*\(\s*\*\s*(\w+)\s*\)\s*\(([^)]*)\)\s*;'
)

# Function pointer variable: RetType (*name)(Params) = FuncName;
_RE_FUNC_PTR_VAR = re.compile(
    r'([\w\s*]+?)\s*\(\s*\*\s*(\w+)\s*\)\s*\(([^)]*)\)\s*(?:=\s*(\w+))?\s*;'
)

# Function pointer assignment: name = FuncName;
_RE_FUNC_PTR_ASSIGN = re.compile(
    r'(\w+)\s*=\s*(?:&\s*)?(\w+)\s*;'
)

# AUTOSAR FUNC macro: FUNC(RetType, MemClass) FuncName(params)
_RE_AUTOSAR_FUNC = re.compile(
    r'^\s*FUNC\s*\(\s*(\w+)\s*,\s*(\w+)\s*\)\s+(\w+)\s*\(([^)]*)\)\s*([{;])',
    re.MULTILINE
)

# Keywords to exclude from function call detection
_KEYWORDS = {
    'if', 'else', 'while', 'for', 'switch', 'case', 'return', 'sizeof',
    'typeof', 'do', 'goto', 'break', 'continue', 'default',
    'typedef', 'struct', 'union', 'enum', 'static', 'extern',
    'const', 'volatile', 'register', 'inline',
}


_STORAGE_CLASS_SPECIFIERS = {'extern', 'static', 'inline', 'register'}


def _clean_return_type(ret_type: str) -> str:
    """Remove storage class specifiers from return type."""
    parts = ret_type.split()
    cleaned = [p for p in parts if p not in _STORAGE_CLASS_SPECIFIERS]
    return ' '.join(cleaned) if cleaned else ret_type


def _strip_comments(content: str) -> str:
    """Remove C-style comments from source code."""
    content = _RE_COMMENT_BLOCK.sub('', content)
    content = _RE_COMMENT_LINE.sub('', content)
    return content


def _strip_preprocessor_continuations(content: str) -> str:
    """Join lines continued with backslash for preprocessor directives."""
    return re.sub(r'\\\n', ' ', content)


def _detect_module_name(file_path: str) -> str:
    """Detect AUTOSAR module name from file path/name."""
    fname = Path(file_path).stem
    # Remove common suffixes like _Cfg, _PBcfg, _Lcfg, _Cbk, _Irq, _Types
    suffixes = ['_Cfg', '_PBcfg', '_Lcfg', '_Cbk', '_Irq', '_Types',
                '_MemMap', '_Version', '_Internal']
    for suffix in suffixes:
        if fname.endswith(suffix):
            return fname[:-len(suffix)]
    return fname


def parse_includes(content: str, file_path: str) -> list[IncludeInfo]:
    """Parse all #include directives."""
    includes = []
    for line_no, line in enumerate(content.split('\n'), 1):
        m = _RE_INCLUDE.match(line)
        if m:
            is_system = m.group(1) == '<'
            includes.append(IncludeInfo(
                header=m.group(2),
                is_system=is_system,
                file_path=file_path,
                line_number=line_no,
            ))
    return includes


def parse_macros(content: str, file_path: str) -> list[MacroDefine]:
    """Parse all #define macros."""
    macros = []
    clean = _strip_preprocessor_continuations(content)
    for m in _RE_DEFINE.finditer(clean):
        name = m.group(1)
        value = m.group(2).strip()
        line_no = content[:m.start()].count('\n') + 1
        macros.append(MacroDefine(
            name=name,
            value=value,
            file_path=file_path,
            line_number=line_no,
            raw_text=m.group(0).strip(),
        ))
    return macros


def parse_include_guard(content: str, file_path: str) -> Optional[IncludeGuard]:
    """Detect include guard pattern (#ifndef X / #define X)."""
    ifndef_match = _RE_INCLUDE_GUARD_IFNDEF.search(content)
    if not ifndef_match:
        return None
    define_match = _RE_INCLUDE_GUARD_DEFINE.search(content)
    if not define_match:
        return None
    return IncludeGuard(
        ifndef_macro=ifndef_match.group(1),
        define_macro=define_match.group(1),
        file_path=file_path,
    )


def parse_functions(content: str, file_path: str) -> list[FunctionInfo]:
    """Parse function declarations and definitions."""
    functions = []
    stripped = _strip_comments(content)

    # Parse AUTOSAR FUNC() macro style
    for m in _RE_AUTOSAR_FUNC.finditer(stripped):
        ret_type = m.group(1)
        func_name = m.group(3)
        params_raw = m.group(4).strip()
        params = [p.strip() for p in params_raw.split(',') if p.strip()] if params_raw and params_raw != 'void' else []
        is_def = m.group(5) == '{'
        line_no = stripped[:m.start()].count('\n') + 1
        functions.append(FunctionInfo(
            name=func_name,
            return_type=ret_type,
            params=params,
            file_path=file_path,
            line_number=line_no,
            is_definition=is_def,
            raw_text=m.group(0).strip(),
        ))

    # Parse standard C-style functions
    for m in _RE_FUNCTION.finditer(stripped):
        ret_type = _clean_return_type(m.group(1).strip())
        func_name = m.group(2)
        params_raw = m.group(3).strip()
        end_char = m.group(4)

        # Skip if already found via AUTOSAR macro or if it's a keyword
        if func_name in _KEYWORDS:
            continue
        if any(f.name == func_name and f.file_path == file_path for f in functions):
            continue

        params = [p.strip() for p in params_raw.split(',') if p.strip()] if params_raw and params_raw != 'void' else []
        is_def = end_char == '{'
        line_no = stripped[:m.start()].count('\n') + 1

        functions.append(FunctionInfo(
            name=func_name,
            return_type=ret_type,
            params=params,
            file_path=file_path,
            line_number=line_no,
            is_definition=is_def,
            raw_text=m.group(0).strip(),
        ))

    return functions


def parse_typedefs(content: str, file_path: str) -> list[TypedefInfo]:
    """Parse typedef declarations."""
    typedefs = []
    stripped = _strip_comments(content)

    # Typedef struct/union/enum
    for m in _RE_TYPEDEF_STRUCT.finditer(stripped):
        kind = m.group(1)
        body = m.group(2)
        name = m.group(3)
        members = [line.strip().rstrip(';') for line in body.strip().split('\n')
                    if line.strip() and not line.strip().startswith('/*')]
        line_no = stripped[:m.start()].count('\n') + 1
        typedefs.append(TypedefInfo(
            name=name,
            kind=kind,
            members=members,
            file_path=file_path,
            line_number=line_no,
            raw_text=m.group(0)[:200],
        ))

    # Function pointer typedefs
    for m in _RE_FUNC_PTR_TYPEDEF.finditer(stripped):
        name = m.group(2)
        if any(t.name == name for t in typedefs):
            continue
        line_no = stripped[:m.start()].count('\n') + 1
        typedefs.append(TypedefInfo(
            name=name,
            kind="func_ptr_typedef",
            file_path=file_path,
            line_number=line_no,
            raw_text=m.group(0).strip(),
        ))

    # Simple typedefs
    for m in _RE_TYPEDEF_SIMPLE.finditer(stripped):
        name = m.group(2)
        if any(t.name == name for t in typedefs):
            continue
        # Skip if it's part of a struct typedef already matched
        base = m.group(1).strip()
        if base.startswith(('struct', 'union', 'enum')):
            continue
        line_no = stripped[:m.start()].count('\n') + 1
        typedefs.append(TypedefInfo(
            name=name,
            kind="typedef",
            file_path=file_path,
            line_number=line_no,
            raw_text=m.group(0).strip(),
        ))

    return typedefs


def parse_function_calls(content: str, file_path: str, functions: list[FunctionInfo]) -> list[FunctionCall]:
    """Parse function calls within function bodies."""
    calls = []
    stripped = _strip_comments(content)

    # Build a map of function body ranges
    func_bodies: list[tuple[str, int, int]] = []
    for func in functions:
        if func.is_definition and func.file_path == file_path:
            # Find function body start
            pattern = re.escape(func.name) + r'\s*\([^)]*\)\s*\{'
            m = re.search(pattern, stripped)
            if m:
                start = m.end()
                # Find matching closing brace
                depth = 1
                pos = start
                while pos < len(stripped) and depth > 0:
                    if stripped[pos] == '{':
                        depth += 1
                    elif stripped[pos] == '}':
                        depth -= 1
                    pos += 1
                func_bodies.append((func.name, start, pos))

    # Find calls within each function body
    for caller_name, body_start, body_end in func_bodies:
        body = stripped[body_start:body_end]
        for m in _RE_FUNC_CALL.finditer(body):
            callee = m.group(1)
            if callee in _KEYWORDS:
                continue
            args = m.group(2).strip()
            line_no = stripped[:body_start + m.start()].count('\n') + 1
            calls.append(FunctionCall(
                caller_func=caller_name,
                callee_func=callee,
                arguments=args,
                file_path=file_path,
                line_number=line_no,
            ))

    return calls


def parse_function_pointers(content: str, file_path: str) -> list[FunctionPointer]:
    """Parse function pointer declarations and assignments."""
    pointers = []
    stripped = _strip_comments(content)

    # Function pointer variables with optional assignment
    for m in _RE_FUNC_PTR_VAR.finditer(stripped):
        ret_type = m.group(1).strip()
        name = m.group(2)
        params_raw = m.group(3).strip()
        assigned = m.group(4) or ""
        param_types = [p.strip() for p in params_raw.split(',') if p.strip()]
        line_no = stripped[:m.start()].count('\n') + 1
        pointers.append(FunctionPointer(
            name=name,
            return_type=ret_type,
            param_types=param_types,
            assigned_func=assigned,
            file_path=file_path,
            line_number=line_no,
            raw_text=m.group(0).strip(),
        ))

    # Track assignments to known function pointers
    known_ptr_names = {fp.name for fp in pointers}
    for m in _RE_FUNC_PTR_ASSIGN.finditer(stripped):
        lhs = m.group(1)
        rhs = m.group(2)
        if lhs in known_ptr_names and rhs not in _KEYWORDS:
            for fp in pointers:
                if fp.name == lhs and not fp.assigned_func:
                    fp.assigned_func = rhs

    # Also look for function pointer fields in struct config tables
    # Pattern: { FuncName, ... } in array initializers
    config_table_pattern = re.compile(
        r'(\w+)\s*\[\s*\]\s*=\s*\{([^}]+)\}',
        re.DOTALL
    )
    for m in config_table_pattern.finditer(stripped):
        table_name = m.group(1)
        entries = m.group(2)
        # Find function names in entries (heuristic: capitalized identifiers)
        func_refs = re.findall(r'\b([A-Z]\w+_\w+)\b', entries)
        for func_ref in func_refs:
            if func_ref not in _KEYWORDS:
                line_no = stripped[:m.start()].count('\n') + 1
                pointers.append(FunctionPointer(
                    name=f"{table_name}[].entry",
                    return_type="unknown",
                    param_types=[],
                    assigned_func=func_ref,
                    file_path=file_path,
                    line_number=line_no,
                    raw_text=f"Table {table_name} references {func_ref}",
                ))

    return pointers


def parse_file(file_path: str) -> ParsedFile:
    """Parse a single C or H file and extract all relevant information."""
    path = Path(file_path)
    content = path.read_text(encoding='utf-8', errors='replace')

    module_name = _detect_module_name(file_path)

    includes = parse_includes(content, file_path)
    macros = parse_macros(content, file_path)
    include_guard = parse_include_guard(content, file_path) if path.suffix == '.h' else None
    functions = parse_functions(content, file_path)
    typedefs = parse_typedefs(content, file_path)
    function_calls = parse_function_calls(content, file_path, functions)
    function_pointers = parse_function_pointers(content, file_path)

    return ParsedFile(
        file_path=file_path,
        module_name=module_name,
        functions=functions,
        macros=macros,
        typedefs=typedefs,
        includes=includes,
        function_calls=function_calls,
        function_pointers=function_pointers,
        include_guard=include_guard,
        raw_content=content,
    )
