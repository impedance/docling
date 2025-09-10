from slugify import slugify

def generate_chapter_filename(index: int, title: str, pattern: str = "{index:02d}-{slug}.md") -> str:
    """
    Generates a deterministic filename for a chapter.

    Args:
        index: The 1-based index of the chapter.
        title: The title of the chapter.
        pattern: The pattern for the filename.

    Returns:
        A safe, deterministic filename string.
    """
    # Extract the first line of the title in case it's multiline
    first_line_title = title.split('\n')[0]
    
    # Slugify the title
    slug = slugify(first_line_title, max_length=60, word_boundary=True)
    
    return pattern.format(index=index, slug=slug)

