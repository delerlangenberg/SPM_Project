import ast
import inspect
from pathlib import Path
from unittest.mock import patch
import pytest

from core.system import mk4s_z_auto_approach as module

tree = ast.parse(
    Path(module.__file__).read_text(encoding="utf-8-sig")
)
names = [
    node.name for node in tree.body
    if isinstance(node, ast.FunctionDef)
    and any(
        isinstance(item, ast.Call) and (
            isinstance(item.func, ast.Name) and item.func.id == "Serial"
            or isinstance(item.func, ast.Attribute) and item.func.attr == "Serial"
        )
        for item in ast.walk(node)
    )
]
assert names, "No direct Z entry points discovered."


@pytest.mark.parametrize("name", names)
def test_execution_blocked_before_serial(name):
    function = getattr(module, name)
    args, kwargs = [], {}
    for parameter in inspect.signature(function).parameters.values():
        if parameter.name == "execute":
            value = True
        elif parameter.default is inspect.Parameter.empty:
            value = None
        else:
            continue
        if parameter.kind == inspect.Parameter.POSITIONAL_ONLY:
            args.append(value)
        elif parameter.kind in (
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        ):
            kwargs[parameter.name] = value

    with patch("serial.Serial") as serial_open:
        with pytest.raises(PermissionError, match="DIRECT_Z_INCIDENT_LOCK"):
            function(*args, **kwargs)
        serial_open.assert_not_called()
