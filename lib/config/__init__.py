"""Values stored on the Pico filesystem."""

import json
import os

_PATH = "/config.json"


class Config:
    def __init__(self, path=_PATH):
        self._path = path
        self._values = {}
        self._load()

    def get(self, key, default=None):
        if not isinstance(key, str):
            raise TypeError("key must be a string")
        return self._values.get(key, default)

    def set(self, key, value):
        if not isinstance(key, str):
            raise TypeError("key must be a string")
        self._values[key] = value
        self._save()

    def delete(self, key):
        if not isinstance(key, str):
            raise TypeError("key must be a string")
        if key not in self._values:
            return
        del self._values[key]
        self._save()

    def clear(self):
        self._values = {}
        try:
            os.remove(self._path)
        except OSError:
            pass
        temp = self._path + ".tmp"
        try:
            os.remove(temp)
        except OSError:
            pass

    def _load(self):
        try:
            with open(self._path) as handle:
                loaded = json.load(handle)
        except (OSError, ValueError):
            return
        if isinstance(loaded, dict):
            self._values = loaded

    def _save(self):
        temp = self._path + ".tmp"
        with open(temp, "w") as handle:
            json.dump(self._values, handle)
        try:
            os.remove(self._path)
        except OSError:
            pass
        os.rename(temp, self._path)
