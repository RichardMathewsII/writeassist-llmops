import pymupdf


class DocumentParser:

    def parse(self, file_path: str) -> str:
        if file_path.endswith(".pdf"):
            doc = pymupdf.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text().replace('\u200b', '')
            doc.close()
            return text
        else:
            raise ValueError("File is not a PDF")


SYLLABUS = DocumentParser().parse("tests/files/syllabus.pdf")
GUIDELINES = DocumentParser().parse("tests/files/persuasive-guidelines.pdf")