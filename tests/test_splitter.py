from core.model.internal_doc import InternalDoc, Heading, Paragraph, Text
from core.split.chapter_splitter import split_into_chapters, ChapterRules

def test_chapter_splitter():
    """
    Tests that the document is correctly split into chapters based on Heading levels.
    """
    # Arrange: Create a document with H1s and H2s
    doc = InternalDoc(blocks=[
        Heading(level=1, text="Chapter 1"),
        Paragraph(inlines=[Text(content="Content of chapter 1.")]),
        Heading(level=2, text="Subsection 1.1"),
        Paragraph(inlines=[Text(content="More content.")]),
        Heading(level=1, text="Chapter 2"),
        Paragraph(inlines=[Text(content="Content of chapter 2.")]),
    ])

    rules = ChapterRules(level=1)

    # Act
    chapters = split_into_chapters(doc, rules)

    # Assert
    assert len(chapters) == 2

    # Check Chapter 1
    chapter1 = chapters[0]
    assert len(chapter1.blocks) == 4
    assert isinstance(chapter1.blocks[0], Heading)
    assert chapter1.blocks[0].text == "Chapter 1"
    assert isinstance(chapter1.blocks[2], Heading)
    assert chapter1.blocks[2].level == 2

    # Check Chapter 2
    chapter2 = chapters[1]
    assert len(chapter2.blocks) == 2
    assert isinstance(chapter2.blocks[0], Heading)
    assert chapter2.blocks[0].text == "Chapter 2"

def test_splitter_with_no_matching_headings():
    """
    Tests that if no headings match the split level, the document is returned as a single chapter.
    """
    doc = InternalDoc(blocks=[
        Heading(level=2, text="Subsection"),
        Paragraph(inlines=[Text(content="Some content.")]),
    ])
    rules = ChapterRules(level=1)

    chapters = split_into_chapters(doc, rules)

    assert len(chapters) == 1
    assert len(chapters[0].blocks) == 2

def test_splitter_with_empty_document():
    """
    Tests that splitting an empty document results in an empty list of chapters.
    """
    doc = InternalDoc(blocks=[])
    rules = ChapterRules(level=1)

    chapters = split_into_chapters(doc, rules)

    assert len(chapters) == 0
