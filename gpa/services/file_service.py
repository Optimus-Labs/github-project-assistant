import os
from pathlib import Path
from typing import Dict, List


class FileService:
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)

    def get_project_files(self, extensions: List[str] = None) -> Dict[str, str]:
        """Get all project files with specified extensions."""
        files = {}
        for root, _, filenames in os.walk(self.base_path):
            for filename in filenames:
                if extensions and not any(filename.endswith(ext) for ext in extensions):
                    continue
                file_path = Path(root) / filename
                if not any(
                    part.startswith(".") for part in file_path.parts
                ):  # Skip hidden directories
                    try:
                        files[str(file_path)] = file_path.read_text()
                    except Exception:
                        continue
        return files

    def get_python_files(self) -> Dict[str, str]:
        """Get all Python files in the project."""
        return self.get_project_files([".py"])

    def get_documentation_files(self) -> Dict[str, str]:
        """Get all documentation files."""
        return self.get_project_files([".md", ".rst", ".txt"])

    def save_file(self, path: str, content: str) -> bool:
        """Save content to file."""
        try:
            file_path = Path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            return True
        except Exception:
            return False
