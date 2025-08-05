import pytest
from src.ingestion.document_loader import DocumentLoader
from src.ingestion.text_splitter import TextSplitter

def test_document_loader(tmp_path):
    # Create a sample text file
    with open(tmp_path / "test.txt", "w", encoding="utf-8") as f:
        f.write("This is a test document.")
    loader = DocumentLoader(tmp_path)
    documents = loader.load_documents()
    assert len(documents) == 1
    assert documents[0][0] == "test.txt"
    assert documents[0][1] == "This is a test document."

def test_text_splitter():
    documents = [("test.txt", "This is a test document with more than 500 characters..." * 10, 0)]
    splitter = TextSplitter(chunk_size=50, chunk_overlap=10)
    chunks = splitter.split_text(documents)
    assert len(chunks) > 1
    assert len(chunks[0][1]) <= 50