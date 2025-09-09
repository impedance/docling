from pydantic import BaseModel

class ResourceRef(BaseModel):
    """
    Represents a reference to a binary resource extracted from the source document.
    """
    id: str  # Unique identifier within the document, e.g., "image1"
    mime_type: str
    content: bytes
    sha256: str  # SHA256 hash of the content for deduplication
