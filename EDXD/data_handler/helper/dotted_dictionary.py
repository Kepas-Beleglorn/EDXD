import json
import logging
import requests
import dataclasses
from pathlib import Path
from typing import get_type_hints

logger = logging.getLogger(__name__)

class DotDict(dict):
    """A dictionary that allows dot notation access and recursively converts nested dicts."""

    def __init__(self, *args, **kwargs):
        super(DotDict, self).__init__(*args, **kwargs)
        # Recursively convert nested dictionaries and lists
        for key, value in self.items():
            if isinstance(value, dict):
                self[key] = DotDict(value)
            elif isinstance(value, list):
                self[key] = [DotDict(item) if isinstance(item, dict) else item for item in value]

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        self[name] = value

def load_json_as_dotdict(file_path: str) -> DotDict | None:

    path = Path(file_path)
    if not path.exists():
        return None

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if isinstance(data, list):
        if len(data) == 0:
            return DotDict()
        # Convert the first item in the list to DotDict
        return DotDict(data[0]) if isinstance(data[0], dict) else data[0]

    return DotDict(data) if isinstance(data, dict) else data

def load_json_from_url_as_dotdict(url: str) -> DotDict:
    response = requests.get(url)
    data = response.json()

    if isinstance(data, list):
        if len(data) == 0:
            return DotDict()
        # Convert the first item in the list to DotDict
        return DotDict(data[0]) if isinstance(data[0], dict) else data[0]

    return DotDict(data) if isinstance(data, dict) else data

def create_dot_dict_from_string(data_string: str) -> DotDict:

    try:
        data = json.loads(data_string)

        def convert_to_dotdict(obj):
            if isinstance(obj, dict):
                return DotDict({k: convert_to_dotdict(v) for k, v in obj.items()})
            elif isinstance(obj, list):
                return [convert_to_dotdict(item) for item in obj]
            return obj

        return convert_to_dotdict(data)
    except Exception as e:
        logger.error("Failed to parse JSON string: %s. Error: %s", data_string, e)
        return None

def save_dotdict_to_json(dotdict: DotDict, file_path: str, indent: int = 2) -> None:
    """Save a DotDict (or any JSON-serializable object) to a JSON file."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(dotdict, f, indent=indent, ensure_ascii=False)

def from_dotdict(cls, d):
    """Recursively rebuild a dataclass instance from a (Dot)Dict."""
    if not dataclasses.is_dataclass(cls):
        return d
    hints = get_type_hints(cls)
    kwargs = {}
    for f in dataclasses.fields(cls):
        value = d[f.name]
        field_type = hints[f.name]
        if dataclasses.is_dataclass(field_type):
            kwargs[f.name] = from_dotdict(field_type, value)
        else:
            kwargs[f.name] = value
    return cls(**kwargs)