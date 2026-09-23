import json
from pathlib import Path

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
    """
    Loads a JSON file and returns it as a DotDict object.

    Args:
        file_path: Path to the JSON file (e.g., 'self_loadout.json')

    Returns:
        DotDict: The parsed JSON data accessible via dot notation.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # If the root is a list (like your SLEF format), we wrap it or return the first item
    # Your SLEF format is a list containing one object: [ { "header":..., "data":... } ]
    if isinstance(data, list):
        if len(data) == 0:
            return DotDict()
        # Convert the first item in the list to DotDict
        return DotDict(data[0]) if isinstance(data[0], dict) else data[0]

    return DotDict(data) if isinstance(data, dict) else data