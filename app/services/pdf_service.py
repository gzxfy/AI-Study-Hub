from pypdf import PdfReader
from app import db

def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    if not reader.pages:
        raise ValueError("The provided PDF is empty or cannot be read.")
    
    full_text = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            full_text.append(text)
    
    return "\n".join(full_text)