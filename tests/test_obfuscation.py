import ast

from pythonx.obfuscation import obfuscate_python


def test_obfuscation_changes_global_and_local_identifiers():
    source = """
import math
BASE_VALUE = 9

def calculate_total(user_number):
    local_result = user_number + BASE_VALUE
    return math.sqrt(local_result)

if __name__ == "__main__":
    print(calculate_total(7))
"""
    output, metrics = obfuscate_python(source, "sample.py")

    ast.parse(output)
    assert output != source
    assert "BASE_VALUE" not in output
    assert "calculate_total" not in output
    assert "__name__" in output
    assert "__main__" in output
    assert metrics["global_renaming"] == "enabled"
    assert metrics["syntax_validated"] is True
    assert metrics["execution_tested"] is False


def test_dynamic_global_lookup_disables_global_renaming():
    source = """
SECRET_VALUE = "example"

def read_secret():
    return globals()["SECRET_VALUE"]
"""
    output, metrics = obfuscate_python(source, "dynamic.py")

    ast.parse(output)
    assert "SECRET_VALUE" in output
    assert metrics["global_renaming"] == "skipped_dynamic_lookup"


def test_literal_all_exports_are_preserved():
    source = """
__all__ = ["public_api"]

def public_api():
    return 42

def internal_helper():
    return public_api()
"""
    output, _ = obfuscate_python(source, "module.py")

    ast.parse(output)
    assert "public_api" in output
    assert "__all__" in output
