import os
from pathlib import Path
from typing import List, Dict

from core.model.resource_ref import ResourceRef

# A simple map to get file extensions from mime types
MIME_TYPE_EXTENSIONS = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/gif": ".gif",
}

def export_assets(resources: List[ResourceRef], output_dir: str) -> Dict[str, str]:
    """
    Saves binary resources to disk, avoiding duplicates based on SHA256 hash.

    Args:
        resources: A list of ResourceRef objects to be exported.
        output_dir: The path to the directory where assets will be saved.

    Returns:
        A dictionary mapping resource IDs to their new relative file paths.
    """
    asset_map: Dict[str, str] = {}
    hashes_written: Dict[str, str] = {}  # {sha256: relative_path}

    # Ensure the output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    for resource in resources:
        if resource.sha256 in hashes_written:
            # This resource is a duplicate of one we've already saved.
            # Map its ID to the path of the existing file.
            asset_map[resource.id] = hashes_written[resource.sha256]
            continue

        # This is a new resource, so we save it.
        ext = MIME_TYPE_EXTENSIONS.get(resource.mime_type, "")
        filename = f"{resource.id}{ext}"
        relative_path = os.path.join(Path(output_dir).name, filename)
        absolute_path = Path(output_dir) / filename

        with open(absolute_path, "wb") as f:
            f.write(resource.content)

        # Store the mapping for this new file
        asset_map[resource.id] = relative_path
        hashes_written[resource.sha256] = relative_path

    return asset_map
