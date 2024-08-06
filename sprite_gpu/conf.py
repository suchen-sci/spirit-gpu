from typing import Any, Dict
import yaml


class Config:
    def __init__(self, **data: Dict[str, Any]):
        self.__dict__.update(data)


def load_config(filename: str) -> Config:
    with open(filename, "r") as f:
        data: Any = yaml.safe_load(f) or {}
    config = Config(**data)
    return config
