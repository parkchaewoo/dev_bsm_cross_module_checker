"""Clang-based AST parser for AUTOSAR BSW module analysis.

Uses libclang to perform compiler-level analysis:
- Full preprocessor expansion (#ifdef, macro expansion)
- Accurate type information (typedef chain resolution)
- Precise function call graph
- Variable scope and pointer tracking
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

try:
    import clang.cindex as ci

    # Auto-detect libclang location
    _CLANG_LIB_PATHS = [
        '/usr/local/lib/python3.11/dist-packages/clang/native/libclang.so',
        '/usr/lib/llvm-18/lib/libclang.so',
        '/usr/lib/llvm-17/lib/libclang.so',
        '/usr/lib/llvm-16/lib/libclang.so',
        '/usr/lib/llvm-14/lib/libclang.so',
    ]
    for _path in _CLANG_LIB_PATHS:
        if os.path.exists(_path):
            ci.Config.set_library_file(_path)
            break

    CLANG_AVAILABLE = True
except (ImportError, Exception):
    CLANG_AVAILABLE = False


@dataclass
class ClangFunctionInfo:
    """Function information from Clang AST."""
    name: str
    return_type: str
    return_type_canonical: str  # resolved through typedefs
    params: list[dict]  # [{"name": "id", "type": "PduIdType", "canonical": "unsigned short"}]
    file_path: str
    line_number: int
    is_definition: bool
    is_static: bool = False


@dataclass
class ClangCallInfo:
    """Function call information from Clang AST."""
    caller_func: str
    callee_func: str
    callee_return_type: str
    arguments: list[dict]  # [{"expr": "0", "type": "PduIdType"}]
    file_path: str
    line_number: int
    return_value_used: bool = False  # True if result is assigned/checked


@dataclass
class ClangMacroInfo:
    """Macro definition from Clang."""
    name: str
    tokens: str
    file_path: str
    line_number: int


@dataclass
class ClangTypedefInfo:
    """Typedef information from Clang."""
    name: str
    underlying_type: str
    canonical_type: str  # fully resolved
    file_path: str
    line_number: int


@dataclass
class ClangStructInfo:
    """Struct/union information from Clang."""
    name: str
    kind: str  # "struct" or "union"
    members: list[dict]  # [{"name": "SduDataPtr", "type": "uint8 *"}]
    file_path: str
    line_number: int


@dataclass
class ClangVarAccess:
    """Variable access (assignment/read) information."""
    var_name: str
    member_name: str  # e.g., "SduDataPtr" for pdu.SduDataPtr
    access_type: str  # "write" or "read"
    value_expr: str   # e.g., "NULL" for pdu.SduDataPtr = NULL
    file_path: str
    line_number: int
    in_function: str


@dataclass
class ClangIncludeInfo:
    """Include directive from Clang."""
    header: str
    is_system: bool
    file_path: str
    line_number: int


@dataclass
class ClangParsedFile:
    """Complete Clang parse result for one or more C/H files."""
    file_path: str
    functions: list[ClangFunctionInfo] = field(default_factory=list)
    calls: list[ClangCallInfo] = field(default_factory=list)
    macros: list[ClangMacroInfo] = field(default_factory=list)
    typedefs: list[ClangTypedefInfo] = field(default_factory=list)
    structs: list[ClangStructInfo] = field(default_factory=list)
    var_accesses: list[ClangVarAccess] = field(default_factory=list)
    includes: list[ClangIncludeInfo] = field(default_factory=list)
    diagnostics: list[str] = field(default_factory=list)


def _get_file_str(node) -> str:
    if node.location.file:
        return str(node.location.file)
    return ""


def _is_in_target_file(node, target_files: set[str]) -> bool:
    """Check if a node belongs to one of our target files (not system headers)."""
    f = _get_file_str(node)
    if not f:
        return False
    return f in target_files or os.path.basename(f) in {os.path.basename(t) for t in target_files}


class ClangParser:
    """Clang-based C parser using libclang."""

    def __init__(self, extra_args: list[str] | None = None,
                 include_paths: list[str] | None = None):
        """Initialize Clang parser.

        Args:
            extra_args: Additional clang compiler flags.
            include_paths: Directories to add as -I include paths.
        """
        if not CLANG_AVAILABLE:
            raise RuntimeError("libclang is not available. Install: pip install libclang")

        self.index = ci.Index.create()
        self.args = ['-std=c99', '-fsyntax-only', '-DAUTOSAR_CHECKING=1']
        if extra_args:
            self.args.extend(extra_args)
        if include_paths:
            for p in include_paths:
                self.args.append(f'-I{p}')

    def parse_file(self, file_path: str, include_dir: str | None = None) -> ClangParsedFile:
        """Parse a single C/H file using Clang.

        Args:
            file_path: Path to the C or H file.
            include_dir: Directory to add as include path for this file's dependencies.
        """
        args = list(self.args)
        if include_dir:
            args.append(f'-I{include_dir}')

        # Also add the file's own directory as include path
        file_dir = os.path.dirname(os.path.abspath(file_path))
        args.append(f'-I{file_dir}')

        tu = self.index.parse(file_path, args=args)

        result = ClangParsedFile(file_path=file_path)

        # Collect diagnostics
        for diag in tu.diagnostics:
            if diag.severity >= ci.Diagnostic.Warning:
                result.diagnostics.append(f"L{diag.location.line}: {diag.spelling}")

        # Walk AST
        target_files = {os.path.abspath(file_path)}
        self._walk_ast(tu.cursor, result, target_files, current_func="")

        # Collect macros
        self._collect_macros(tu, result, target_files)

        # Collect includes
        self._collect_includes(tu, result, file_path)

        return result

    def parse_directory(self, dir_path: str) -> list[ClangParsedFile]:
        """Parse all C files in a directory."""
        results = []
        dir_path = os.path.abspath(dir_path)

        c_files = []
        for f in os.listdir(dir_path):
            if f.endswith('.c'):
                c_files.append(os.path.join(dir_path, f))

        for fpath in sorted(c_files):
            try:
                parsed = self.parse_file(fpath, include_dir=dir_path)
                results.append(parsed)
            except Exception as e:
                results.append(ClangParsedFile(
                    file_path=fpath,
                    diagnostics=[f"Parse error: {e}"]
                ))

        # Also parse .h files that don't have a corresponding .c
        h_files = []
        c_stems = {os.path.splitext(os.path.basename(f))[0] for f in c_files}
        for f in os.listdir(dir_path):
            if f.endswith('.h'):
                stem = os.path.splitext(f)[0]
                if stem not in c_stems:
                    h_files.append(os.path.join(dir_path, f))

        for fpath in sorted(h_files):
            try:
                parsed = self.parse_file(fpath, include_dir=dir_path)
                results.append(parsed)
            except Exception:
                pass

        return results

    def _walk_ast(self, cursor, result: ClangParsedFile,
                  target_files: set[str], current_func: str):
        """Recursively walk the AST and extract information."""
        for node in cursor.get_children():
            # Only process nodes from our target files
            if not _is_in_target_file(node, target_files):
                # But still walk into if it's a translation unit level
                if node.kind == ci.CursorKind.TRANSLATION_UNIT:
                    self._walk_ast(node, result, target_files, current_func)
                continue

            kind = node.kind

            # ── Functions ──
            if kind == ci.CursorKind.FUNCTION_DECL:
                func = ClangFunctionInfo(
                    name=node.spelling,
                    return_type=node.result_type.spelling,
                    return_type_canonical=node.result_type.get_canonical().spelling,
                    params=[],
                    file_path=_get_file_str(node),
                    line_number=node.location.line,
                    is_definition=node.is_definition(),
                    is_static=node.storage_class == ci.StorageClass.STATIC,
                )
                for child in node.get_children():
                    if child.kind == ci.CursorKind.PARM_DECL:
                        func.params.append({
                            "name": child.spelling,
                            "type": child.type.spelling,
                            "canonical": child.type.get_canonical().spelling,
                        })
                result.functions.append(func)

                # Walk into function body for calls
                if node.is_definition():
                    self._walk_ast(node, result, target_files, node.spelling)
                continue

            # ── Function Calls ──
            if kind == ci.CursorKind.CALL_EXPR:
                callee_name = node.spelling
                if callee_name:
                    call = ClangCallInfo(
                        caller_func=current_func,
                        callee_func=callee_name,
                        callee_return_type=node.type.spelling,
                        arguments=[],
                        file_path=_get_file_str(node),
                        line_number=node.location.line,
                        return_value_used=self._is_return_value_used(node),
                    )
                    # Extract arguments
                    for i, arg in enumerate(node.get_arguments()):
                        call.arguments.append({
                            "expr": self._get_source_text(arg),
                            "type": arg.type.spelling,
                        })
                    result.calls.append(call)

            # ── Typedefs ──
            elif kind == ci.CursorKind.TYPEDEF_DECL:
                underlying = node.underlying_typedef_type
                result.typedefs.append(ClangTypedefInfo(
                    name=node.spelling,
                    underlying_type=underlying.spelling,
                    canonical_type=underlying.get_canonical().spelling,
                    file_path=_get_file_str(node),
                    line_number=node.location.line,
                ))

            # ── Structs ──
            elif kind == ci.CursorKind.STRUCT_DECL:
                if node.spelling:  # Skip anonymous structs
                    members = []
                    for child in node.get_children():
                        if child.kind == ci.CursorKind.FIELD_DECL:
                            members.append({
                                "name": child.spelling,
                                "type": child.type.spelling,
                            })
                    result.structs.append(ClangStructInfo(
                        name=node.spelling,
                        kind="struct",
                        members=members,
                        file_path=_get_file_str(node),
                        line_number=node.location.line,
                    ))

            # ── Variable declarations ──
            elif kind == ci.CursorKind.VAR_DECL:
                pass  # Could track variable declarations if needed

            # ── Member access (e.g., pdu.SduDataPtr = NULL) ──
            elif kind == ci.CursorKind.MEMBER_REF_EXPR:
                if current_func:
                    # Check if it's an assignment (parent is binary operator =)
                    parent = node.semantic_parent
                    result.var_accesses.append(ClangVarAccess(
                        var_name="",
                        member_name=node.spelling,
                        access_type="access",
                        value_expr="",
                        file_path=_get_file_str(node),
                        line_number=node.location.line,
                        in_function=current_func,
                    ))

            # Recurse into children
            self._walk_ast(node, result, target_files, current_func)

    def _is_return_value_used(self, call_node) -> bool:
        """Check if the return value of a call is used (assigned or in expression)."""
        # Heuristic: if the parent is a compound statement, return value is discarded
        parent = call_node.semantic_parent
        if parent and parent.kind == ci.CursorKind.COMPOUND_STMT:
            return False
        return True

    def _get_source_text(self, node) -> str:
        """Get the source text of a node."""
        try:
            tokens = list(node.get_tokens())
            if tokens:
                return ' '.join(t.spelling for t in tokens[:10])
        except Exception:
            pass
        return node.spelling or ""

    def _collect_macros(self, tu, result: ClangParsedFile, target_files: set[str]):
        """Collect macro definitions from the translation unit."""
        for cursor in tu.cursor.get_children():
            if cursor.kind == ci.CursorKind.MACRO_DEFINITION:
                if _is_in_target_file(cursor, target_files):
                    tokens = list(cursor.get_tokens())
                    name = tokens[0].spelling if tokens else cursor.spelling
                    value = ' '.join(t.spelling for t in tokens[1:]) if len(tokens) > 1 else ""
                    result.macros.append(ClangMacroInfo(
                        name=name,
                        tokens=value,
                        file_path=_get_file_str(cursor),
                        line_number=cursor.location.line,
                    ))

    def _collect_includes(self, tu, result: ClangParsedFile, source_file: str):
        """Collect include directives."""
        for inc in tu.get_includes():
            if str(inc.source) == os.path.abspath(source_file):
                result.includes.append(ClangIncludeInfo(
                    header=os.path.basename(str(inc.include)),
                    is_system=False,  # libclang doesn't distinguish <> vs ""
                    file_path=str(inc.source),
                    line_number=inc.location.line,
                ))


def clang_parse_file(file_path: str, include_dir: str | None = None) -> ClangParsedFile:
    """Convenience function to parse a single file."""
    parser = ClangParser()
    return parser.parse_file(file_path, include_dir)


def clang_parse_directory(dir_path: str) -> list[ClangParsedFile]:
    """Convenience function to parse all files in a directory."""
    parser = ClangParser()
    return parser.parse_directory(dir_path)
