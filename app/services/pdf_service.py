from pypdf import PdfReader

def extract_text_from_pdf(pdf_path: str) -> tuple[str, int]:
    reader = PdfReader(pdf_path)
    pages = reader.pages or []
    text_parts = [(p.extract_text() or "").strip() for p in pages]
    text = "\n".join([t for t in text_parts if t])
    return text, len(pages)