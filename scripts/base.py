"""
Classe de base pour tous les scripts CGF BRVMHalal ETF.
"""
import json
import os


class BaseScript:
    def __init__(self):
        self.scripts_dir = os.path.dirname(os.path.abspath(__file__))
        self.root_dir    = os.path.normpath(os.path.join(self.scripts_dir, ".."))
        self.data_dir    = os.path.join(self.root_dir, "data")

    def load_json(self, filename, default=None):
        path = os.path.join(self.data_dir, filename)
        if not os.path.exists(path):
            return default
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def save_json(self, filename, data, indent=2):
        path = os.path.join(self.data_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)

    def load_json_path(self, path, default=None):
        if not os.path.exists(path):
            return default
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def save_json_path(self, path, data, indent=2):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)

    def run(self):
        raise NotImplementedError("Implémenter run() dans la sous-classe.")
