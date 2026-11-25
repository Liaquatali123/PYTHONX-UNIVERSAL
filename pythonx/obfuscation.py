"""Conservative single-file Python source obfuscation.

This transforms source only; it never imports or executes uploaded code.
"""
import ast
from typing import Any

_BASE_PRESERVE_GLOBALS = {
    "__name__", "__file__", "__package__", "__doc__", "__all__",
    "__builtins__", "__annotations__", "__cached__", "__loader__",
    "__spec__", "__path__",
}

_DYNAMIC_GLOBAL_ACCESS = {"globals", "locals", "vars", "eval", "exec"}


def _literal_exports(tree: ast.Module) -> set[str]:
    exported: set[str] = set()
    for node in tree.body:
        value = None
        if isinstance(node, ast.Assign):
            if any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets):
                value = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == "__all__":
            value = node.value
        if isinstance(value, (ast.List, ast.Tuple, ast.Set)):
            for item in value.elts:
                if isinstance(item, ast.Constant) and isinstance(item.value, str):
                    exported.add(item.value)
    return exported


def _uses_dynamic_name_lookup(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in _DYNAMIC_GLOBAL_ACCESS:
                return True
        if isinstance(node, ast.Attribute) and node.attr == "__dict__":
            return True
    return False


def obfuscate_python(source: str, filename: str = "input.py") -> tuple[str, dict[str, Any]]:
    """Return minified/renamed source and transparent transformation metrics."""
    tree = ast.parse(source, filename=filename, mode="exec")
    dynamic_lookup = _uses_dynamic_name_lookup(tree)
    preserve = sorted(_BASE_PRESERVE_GLOBALS | _literal_exports(tree))
    import python_minifier

    output = python_minifier.minify(
        source,
        filename=filename,
        rename_locals=not dynamic_lookup,
        rename_globals=not dynamic_lookup,
        preserve_globals=preserve,
        remove_literal_statements=False,
        remove_asserts=False,
        remove_debug=False,
        remove_annotations=False,
    )
    # Parse the output again. This is validation only; uploaded code is not executed.
    output_tree = ast.parse(output, filename="protected.py", mode="exec")
    original_names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    output_names = {n.id for n in ast.walk(output_tree) if isinstance(n, ast.Name)}
    source_bytes = len(source.encode("utf-8"))
    output_bytes = len(output.encode("utf-8"))
    metrics = {
        "source_bytes": source_bytes,
        "output_bytes": output_bytes,
        "size_change_percent": round(((output_bytes - source_bytes) / source_bytes) * 100, 1) if source_bytes else 0,
        "global_renaming": "skipped_dynamic_lookup" if dynamic_lookup else "enabled",
        "local_renaming": "skipped_dynamic_lookup" if dynamic_lookup else "enabled",
        "identifier_names_changed": len(original_names.symmetric_difference(output_names)),
        "syntax_validated": True,
        "execution_tested": False,
    }
    return output, metrics
