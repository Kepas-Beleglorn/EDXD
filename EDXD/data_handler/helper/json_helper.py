import json


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

