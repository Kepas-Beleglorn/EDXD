import json
from pathlib import Path
import requests

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


def load_json_as_dotdict(file_path: str) -> DotDict:

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

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

    data = json.loads(data_string)

    def convert_to_dotdict(obj):
        if isinstance(obj, dict):
            return DotDict({k: convert_to_dotdict(v) for k, v in obj.items()})
        elif isinstance(obj, list):
            return [convert_to_dotdict(item) for item in obj]
        return obj

    return convert_to_dotdict(data)