from dagster import ConfigurableResource, InitResourceContext
import pymupdf
import re

class DocumentParserClient:

    def parse(self, file_path: str) -> str:
        if file_path.endswith(".pdf"):
            doc = pymupdf.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text().replace('\u200b', '')
            # reduce 3+ \n \n \n ... to 2 \n
            text = re.sub(r'\n\s+\n', '\n', text)
            doc.close()
            return text
        else:
            raise ValueError("File is not a PDF")
        

class DocumentParser(ConfigurableResource):
    def create_resource(self, context: InitResourceContext):
        return DocumentParserClient()