from typing import Any, NamedTuple, Dict, Tuple, Callable, Optional


class Schema(NamedTuple):
    type: Any
    required: bool = False
    default: Any = None
    constraints: Optional[Callable[[Any], bool]] = None


def validate_and_set_default(
    data: Dict[str, Any], schema: Dict[str, Schema]
) -> Tuple[Dict[str, Any], str]:
    error = ""

    error += _check_unexpected_input(data, schema)
    data, err = _check_validate_and_set_default(data, schema)
    error += err
    return data, error


def _check_unexpected_input(data: Dict[str, Any], schema: Dict[str, Schema]) -> str:
    error = ""
    for key in data:
        if key not in schema:
            error += f"unexpected input {key}. "
    return error


def _check_validate_and_set_default(
    data: Dict[str, Any], schema: Dict[str, Schema]
) -> Tuple[Dict[str, Any], str]:

    error = ""
    for key, schema_item in schema.items():
        if key not in data:
            if schema_item.required:
                error += f"missing required input {key}. "
            else:
                data[key] = schema_item.default
        else:
            value, err = _check_value(key, data[key], schema_item)
            data[key] = value
            error += err
    return data, error


def _check_value(key: str, value: Any, schema: Schema) -> Tuple[Any, str]:
    err = ""
    if (schema.type is float) and (type(value) is int):
        value = float(value)

    if value is None:
        return value, err

    if not isinstance(value, schema.type):
        err += f"{key} should be {schema.type} type, not {type(value)}. "

    if schema.constraints is not None:
        if not schema.constraints(value):
            err += f"{key} constraints failed. "
    return value, err
