from io import BytesIO

from PyPDF2 import PdfReader
from docx import Document


ALLOWED_RESUME_EXTENSIONS = {".pdf", ".docx", ".txt"}


def extract_resume_text(uploaded_file):
    filename = (uploaded_file.filename or "").lower()
    suffix = "." + filename.rsplit(".", 1)[-1] if "." in filename else ""

    if suffix not in ALLOWED_RESUME_EXTENSIONS:
        raise ValueError("Upload a PDF, DOCX, or TXT resume.")

    file_bytes = uploaded_file.read()
    if not file_bytes:
        raise ValueError("Resume file is empty.")

    if suffix == ".pdf":
        return _extract_pdf_text(file_bytes)
    if suffix == ".docx":
        return _extract_docx_text(file_bytes)
    return file_bytes.decode("utf-8", errors="ignore").strip()


def _extract_pdf_text(file_bytes):
    reader = PdfReader(BytesIO(file_bytes))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    return _clean_text(text)


def _extract_docx_text(file_bytes):
    document = Document(BytesIO(file_bytes))
    text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    return _clean_text(text)


def _clean_text(text):
    clean_text = "\n".join(line.strip() for line in (text or "").splitlines() if line.strip())
    if len(clean_text) < 80:
        raise ValueError("Could not read enough text from the resume. Try uploading a text-based PDF, DOCX, or TXT file.")
    return clean_text[:12000]
