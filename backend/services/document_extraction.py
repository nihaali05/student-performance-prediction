import os
import io
import json
import re
import pypdf
from PIL import Image
from services.ocr import perform_image_ocr

ALLOWED_MIME_TYPES = {
    'application/pdf': 'pdf',
    'image/png': 'png',
    'image/jpeg': 'jpeg',
    'image/jpg': 'jpg'
}

MAX_FILE_SIZE = 16 * 1024 * 1024 # 16 MB

def clean_extracted_text(text):
    if not text:
        return ""
    # Normalize line breaks and remove zero-width or unprintable characters
    cleaned = re.sub(r'[\r\n]+', '\n', text)
    cleaned = re.sub(r'[ \t]+', ' ', cleaned)
    return cleaned.strip()

def is_meaningful_text(text, min_words=3):
    if not text:
        return False
    cleaned = clean_extracted_text(text)
    words = re.findall(r'\b[a-zA-Z0-9_]{2,}\b', cleaned)
    return len(words) >= min_words

def extract_pdf_content(file_bytes):
    """
    Extract text per page from PDF.
    Returns: (status, full_text, page_contents, error_msg)
    """
    try:
        pdf_file = io.BytesIO(file_bytes)
        reader = pypdf.PdfReader(pdf_file)
        
        page_contents = []
        full_text_parts = []
        
        for idx, page in enumerate(reader.pages):
            page_num = idx + 1
            text = page.extract_text() or ""
            text = clean_extracted_text(text)
            
            if text:
                page_contents.append({
                    "page": page_num,
                    "text": text
                })
                full_text_parts.append(f"[PAGE {page_num}]\n{text}")
                
        full_text = "\n\n".join(full_text_parts)
        
        # Check if text extraction was sufficient or if scanned PDF
        if not is_meaningful_text(full_text, min_words=5):
            print("[Extraction] Standard PDF text extraction insufficient. Triggering OCR pipeline...")
            ocr_page_contents = []
            ocr_text_parts = []
            
            for idx, page in enumerate(reader.pages):
                page_num = idx + 1
                page_text = ""
                # Attempt to extract images from page
                for img_idx, img in enumerate(page.images):
                    try:
                        img_bytes = img.data
                        ocr_res = perform_image_ocr(img_bytes, mime_type='image/png')
                        if ocr_res:
                            page_text += "\n" + ocr_res
                    except Exception as ie:
                        print(f"[OCR] Page image extraction error p{page_num}: {ie}")
                        
                page_text = clean_extracted_text(page_text)
                if page_text:
                    ocr_page_contents.append({
                        "page": page_num,
                        "text": page_text
                    })
                    ocr_text_parts.append(f"[PAGE {page_num}]\n{page_text}")
                    
            if ocr_text_parts:
                full_text = "\n\n".join(ocr_text_parts)
                page_contents = ocr_page_contents

        if not is_meaningful_text(full_text, min_words=3):
            return "FAILED", None, None, "Unable to read meaningful content from this study material. Please upload a clearer PDF or image."

        return "SUCCESS", full_text, page_contents, None

    except pypdf.errors.PdfReadError:
        return "FAILED", None, None, "The uploaded PDF file is corrupted or password-protected and cannot be read."
    except Exception as e:
        return "FAILED", None, None, f"Failed to process PDF document: {str(e)}"

def extract_image_content(file_bytes, mime_type):
    """
    Extract content from PNG/JPG/JPEG image.
    Returns: (status, full_text, page_contents, error_msg)
    """
    try:
        # Validate PIL readable
        img = Image.open(io.BytesIO(file_bytes))
        img.verify()
        
        extracted_text = perform_image_ocr(file_bytes, mime_type=mime_type)
        extracted_text = clean_extracted_text(extracted_text)
        
        if not is_meaningful_text(extracted_text, min_words=3):
            return "FAILED", None, None, "No readable study content was detected in this image. Please upload a clearer image containing text."

        page_contents = [{"page": 1, "text": extracted_text}]
        full_text = f"[PAGE 1]\n{extracted_text}"
        
        return "SUCCESS", full_text, page_contents, None

    except Exception as e:
        return "FAILED", None, None, f"Unable to process image file: {str(e)}"

def process_uploaded_document(file_bytes, filename, content_type=None):
    """
    Main pipeline entry for document upload & validation.
    Validates MIME type, file size, empty content.
    Returns dictionary with result.
    """
    if not file_bytes or len(file_bytes) == 0:
        return {
            "status": "FAILED",
            "error": "The uploaded file is empty."
        }

    if len(file_bytes) > MAX_FILE_SIZE:
        return {
            "status": "FAILED",
            "error": f"File size exceeds maximum allowed limit of {MAX_FILE_SIZE // (1024*1024)} MB."
        }

    ext = os.path.splitext(filename)[1].lower().replace('.', '')
    
    # MIME validation
    is_pdf = ext == 'pdf' or content_type == 'application/pdf' or file_bytes.startswith(b'%PDF')
    is_image = ext in ['png', 'jpg', 'jpeg'] or (content_type and content_type.startswith('image/')) or file_bytes[:4] in [b'\x89PNG', b'\xff\xd8\xff\xe0', b'\xff\xd8\xff\xe1']
    
    if not (is_pdf or is_image):
        return {
            "status": "FAILED",
            "error": "Unsupported file format. Please upload a PDF document or an image (PNG, JPG, JPEG)."
        }

    if is_pdf:
        mime = 'application/pdf'
        status, full_text, page_contents, error = extract_pdf_content(file_bytes)
    else:
        mime = f'image/{ext}' if ext in ['png', 'jpg', 'jpeg'] else 'image/png'
        status, full_text, page_contents, error = extract_image_content(file_bytes, mime)

    if status == "FAILED":
        return {
            "status": "FAILED",
            "mime_type": mime,
            "error": error
        }

    return {
        "status": "SUCCESS",
        "mime_type": mime,
        "extracted_text": full_text,
        "page_contents": page_contents,
        "character_count": len(full_text),
        "page_count": len(page_contents) if page_contents else 1
    }
