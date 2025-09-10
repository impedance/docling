import os
from pathlib import Path

class Writer:
    """Handles file system operations for writing chapters and assets."""

    def ensure_dir(self, dir_path: Path) -> None:
        """
        Ensures that a directory exists. If it doesn't, it's created.
        """
        os.makedirs(dir_path, exist_ok=True)

    def write_text(self, file_path: Path, content: str) -> None:
        """
        Writes text content to a file.
        """
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    def write_binary(self, file_path: Path, content: bytes) -> None:
        """
        Writes binary content to a file.
        """
        with open(file_path, "wb") as f:
            f.write(content)
