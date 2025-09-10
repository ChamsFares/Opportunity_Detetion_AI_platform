import csv
import re
from io import BytesIO, StringIO

import fitz  # PyMuPDF
import nltk
import pytesseract
from fastapi import UploadFile
from nltk.corpus import stopwords
from PIL import Image

# Download NLTK stopwords if not already present
try:
    stopwords.words("english")
except LookupError:
    nltk.download("stopwords")


def extract_text_from_csv(file: UploadFile) -> str:
    content = file.file.read().decode("utf-8")
    file.file.seek(0)
    reader = csv.reader(StringIO(content))

    lines = []
    for i, row in enumerate(reader):
        line = f"Row {i + 1}: " + " | ".join(row)
        lines.append(line)

    return "\n".join(lines)


def extract_text_from_image(image: Image.Image) -> str:
    """
    Extract text from a PIL image using OCR (Tesseract).
    """
    try:
        return pytesseract.image_to_string(image)
    except Exception as e:
        print(f"[OCR Error] Failed to extract text from image: {e}")
        return ""


def extract_text_from_pdf(file) -> str:
    file_bytes = file.file.read()
    pdf = fitz.open(stream=file_bytes, filetype="pdf")
    final_text = ""

    for page_index, page in enumerate(pdf):
        page_text = page.get_text()

        if page_text.strip():
            final_text += f"\n--- Page {page_index + 1} (Text) ---\n"
            final_text += page_text
        else:
            # OCR fallback for image-based page
            pix = page.get_pixmap(dpi=300)
            image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            ocr_text = pytesseract.image_to_string(image)

            final_text += f"\n--- Page {page_index + 1} (OCR) ---\n"
            final_text += ocr_text

    return final_text.strip()


# Load stopwords for English, French, Arabic
stop_words_en = set(stopwords.words("english"))
stop_words_fr = set(stopwords.words("french"))
stop_words_ar = set(stopwords.words("arabic"))

combined_stopwords = stop_words_en.union(stop_words_fr).union(stop_words_ar)


def extract_files_content(files):
    """
    Centralized extraction logic for PDF, image, and CSV files.
    Returns combined text from all files.
    """
    combined_doc_text = ""
    for index, file in enumerate(files or []):
        filename = file.filename.lower()
        file_ext = filename.split(".")[-1]
        log_prefix = f"[File {index + 1}: {filename}]"
        if file_ext == "pdf":
            print(f"{log_prefix} Detected as PDF. Extracting text...")
            extracted_text = extract_text_from_pdf(file)
            combined_doc_text += (
                f"\n--- PDF File {index + 1}: {file.filename} ---\n{extracted_text}\n"
            )
        elif file_ext in ["png", "jpg", "jpeg", "bmp", "tiff", "webp"]:
            print(f"{log_prefix} Detected as image. Using OCR...")
            image = Image.open(BytesIO(file.file.read()))
            file.file.seek(0)
            extracted_text = extract_text_from_image(image)
            combined_doc_text += (
                f"\n--- Image File {index + 1}: {file.filename} ---\n{extracted_text}\n"
            )
        elif file_ext == "csv":
            print(f"{log_prefix} Detected as CSV. Parsing rows...")
            extracted_text = extract_text_from_csv(file)
            combined_doc_text += (
                f"\n--- CSV File {index + 1}: {file.filename} ---\n{extracted_text}\n"
            )
        else:
            print(f"{log_prefix} Unsupported file type: {file_ext}. Skipping...")
            file.file.seek(0)
    return combined_doc_text


def clean_text(text: str) -> tuple[str, int]:
    print("Extracted infos are being cleaned...")
    # Lowercase
    text = text.lower()
    # Remove punctuation and special characters (keep Arabic + Latin letters, digits, and space)
    text = re.sub(r"[^a-z0-9\u0600-\u06FF\s]", " ", text)
    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text).strip()
    # Tokenize and filter stopwords
    words = text.split()
    filtered_words = [word for word in words if word not in combined_stopwords]
    cleaned_text = " ".join(filtered_words)
    word_count = len(filtered_words)
    return cleaned_text, word_count


def extract_text_from_uploaded_file(file: UploadFile) -> str:
    file_extension = file.filename.lower().split(".")[-1]
    supported_image_formats = ["jpg", "jpeg", "png", "bmp", "tiff", "webp"]

    try:
        if file_extension == "pdf":
            raw_text = extract_text_from_pdf(file)
        elif file_extension in supported_image_formats:
            image_bytes = file.file.read()
            image = Image.open(BytesIO(image_bytes)).convert("RGB")
            raw_text = extract_text_from_image(image)
        elif file_extension == "csv":
            raw_text = extract_text_from_csv(file)
        else:
            print(f"[Unsupported] File type not supported: {file.filename}")
            return ""

        cleaned_text, word_count = clean_text(raw_text)
        print(f"[Info] Cleaned word count: {word_count}")
        return cleaned_text

    except Exception as e:
        print(f"[Error] Extraction failed for {file.filename}: {e}")
        return ""
