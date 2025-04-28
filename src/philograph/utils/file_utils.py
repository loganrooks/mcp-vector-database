import os
import logging
from pathlib import Path
from typing import List, Optional, Generator
from typing import List, Generator

logger = logging.getLogger(__name__)

def check_file_exists(file_path: str | Path) -> bool:
    """Checks if a file exists at the given path."""
    return Path(file_path).is_file()

def check_directory_exists(dir_path: str | Path) -> bool:
    """Checks if a directory exists at the given path."""
    return Path(dir_path).is_dir()

def get_file_extension(file_path: str | Path) -> str:
    """Returns the file extension in lowercase (including the dot)."""
    return Path(file_path).suffix.lower()

def join_paths(*args: str | Path) -> Path:
    """Joins multiple path components."""
    return Path(os.path.join(*args))

def list_files_in_directory(
    dir_path: str | Path,
    allowed_extensions: Optional[List[str]] = None,
    recursive: bool = False
) -> Generator[Path, None, None]:
    """
    Lists files in a directory, optionally filtering by extension and recursing.

    Args:
        dir_path: The directory path to scan.
        allowed_extensions: A list of lowercase extensions (including dot, e.g., ['.pdf', '.txt'])
                            to include. If None, all files are included.
        recursive: If True, scan subdirectories recursively.

    Yields:
        Path objects for matching files.
    """
    base_path = Path(dir_path)
    if not base_path.is_dir():
        logger.warning(f"Directory not found or not a directory: {dir_path}")
        return

    logger.info(f"Scanning directory: {base_path} (Recursive: {recursive}, Extensions: {allowed_extensions})")

    if recursive:
        file_iterator = base_path.rglob('*') # Recursive glob
    else:
        file_iterator = base_path.glob('*') # Non-recursive glob

    for item in file_iterator:
        if item.is_file():
            if allowed_extensions:
                if item.suffix.lower() in allowed_extensions:
                    yield item
            else:
                yield item
        elif item.is_dir() and not recursive:
             # Skip directories if not recursive, rglob handles recursion internally
             pass

# Example Usage:
# if __name__ == "__main__":
#     from .. import config # Assuming config defines SOURCE_FILE_DIR_ABSOLUTE
#     pdf_files = list_files_in_directory(config.SOURCE_FILE_DIR_ABSOLUTE, allowed_extensions=['.pdf'], recursive=True)
#     print("PDF Files Found:")
#     for pdf_file in pdf_files:
#         print(pdf_file)