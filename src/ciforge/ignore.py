import os
import fnmatch

class IgnoreRules:
    def __init__(self):
        self.patterns = []
        self._load()

    def _load(self):
        if not os.path.exists('.ciforge-ignore'):
            return
        with open('.ciforge-ignore', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                self.patterns.append(line)

    def is_ignored_file(self, file_path: str) -> bool:
        for pattern in self.patterns:
            if fnmatch.fnmatch(file_path, pattern) or fnmatch.fnmatch(os.path.basename(file_path), pattern):
                return True
        return False
        
    def is_ignored_secret(self, text: str) -> bool:
        for pattern in self.patterns:
            if pattern in text:
                return True
        return False

rules = IgnoreRules()
