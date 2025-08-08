"""Test utilities for reading fixture documents.

The original tests relied on the optional ``pymupdf`` package to parse PDF
files.  Since that dependency may not be available in the execution
environment, this module now falls back to reading pre-extracted text files with
the same base name when ``pymupdf`` cannot be imported.
"""

try:  # pragma: no cover - only exercised indirectly in tests
    import pymupdf  # type: ignore
except ModuleNotFoundError:  # Provide a minimal stand-in when PyMuPDF isn't installed
    pymupdf = None  # type: ignore


class DocumentParser:
    def parse(self, file_path: str) -> str:
        if not file_path.endswith(".pdf"):
            raise ValueError("File is not a PDF")

        if pymupdf is not None:
            doc = pymupdf.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text().replace("\u200b", "")
            doc.close()
            return text

        # Fallback: read from a sibling .txt file when PyMuPDF is unavailable
        txt_path = file_path.replace(".pdf", ".txt")
        with open(txt_path, "r") as f:
            return f.read()


SYLLABUS = DocumentParser().parse("tests/files/syllabus.pdf")
GUIDELINES = DocumentParser().parse("tests/files/persuasive-guidelines.pdf")
