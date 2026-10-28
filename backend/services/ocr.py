import os
import io
import re
from PIL import Image

def perform_image_ocr(image_bytes, mime_type='image/png'):
    """
    Perform OCR on image bytes (PNG, JPG, JPEG).
    Returns extracted text string.
    """
    extracted_text = ""
    
    # 1. Try Gemini Vision API if API Key present
    api_key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
    if api_key:
        prompt = (
            "Extract all visible text from this study document image accurately. "
            "Preserve headings, paragraphs, bullet points, questions, options, answers, tables, and readable formulas. "
            "Return ONLY the extracted text content. Do NOT add commentary."
        )
        try:
            import base64
            import requests
            b64 = base64.b64encode(image_bytes).decode('utf-8')
            model_name = os.environ.get('GEMINI_MODEL') or 'gemini-flash-lite-latest'
            payload = {
                'contents': [{
                    'parts': [
                        {'inlineData': {'mimeType': mime_type, 'data': b64}},
                        {'text': prompt}
                    ]
                }]
            }
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
            resp = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get('candidates', [])
                if candidates:
                    parts = candidates[0].get('content', {}).get('parts', [])
                    if parts and 'text' in parts[0]:
                        txt = parts[0]['text'].strip()
                        if len(txt) >= 10:
                            return txt
        except Exception as e:
            print(f"[OCR] Gemini REST vision OCR failed: {e}")

        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=api_key, http_options={'timeout': 15})
            model_name = os.environ.get('GEMINI_MODEL') or 'gemini-flash-lite-latest'
            response = client.models.generate_content(
                model=model_name,
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                    prompt
                ]
            )
            if response and response.text:
                extracted_text = response.text.strip()
                if len(extracted_text) >= 10:
                    return extracted_text
        except Exception as e:
            print(f"[OCR] Gemini SDK vision OCR failed: {e}")

    # 2. Try Grok Vision API if GROK_API_KEY present (OpenAI-compatible endpoint)
    grok_key = os.environ.get('GROK_API_KEY') or os.environ.get('XAI_API_KEY')
    if grok_key and not extracted_text:
        try:
            import base64
            from openai import OpenAI
            client = OpenAI(api_key=grok_key, base_url='https://api.x.ai/v1')
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            response = client.chat.completions.create(
                model=os.environ.get('GROK_MODEL', 'grok-2-latest'),
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Extract all text from this image exactly as written. Do not add intro or outro."},
                            {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}}
                        ]
                    }
                ]
            )
            text = response.choices[0].message.content
            if text and len(text.strip()) >= 10:
                return text.strip()
        except Exception as e:
            print(f"[OCR] Grok vision OCR failed or skipped: {e}")

    # 3. Try OpenAI Vision API if OPENAI_API_KEY present
    openai_key = os.environ.get('OPENAI_API_KEY')
    if openai_key and not extracted_text:
        try:
            import base64
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Extract all text from this image exactly as written. Do not add intro or outro."},
                            {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}}
                        ]
                    }
                ]
            )
            text = response.choices[0].message.content
            if text and len(text.strip()) >= 10:
                return text.strip()
        except Exception as e:
            print(f"[OCR] OpenAI vision OCR failed or skipped: {e}")

    # 4. Try pytesseract if installed
    try:
        import pytesseract
        image = Image.open(io.BytesIO(image_bytes))
        tess_text = pytesseract.image_to_string(image)
        if tess_text and len(tess_text.strip()) >= 10:
            return tess_text.strip()
    except Exception as e:
        print(f"[OCR] pytesseract unavailable or tesseract binary not found: {e}")

    # 5. Try EasyOCR if installed
    try:
        import easyocr
        reader = easyocr.Reader(['en'], gpu=False)
        results = reader.readtext(image_bytes, detail=0)
        if results:
            easy_text = "\n".join(results)
            if len(easy_text.strip()) >= 10:
                return easy_text.strip()
    except Exception as e:
        print(f"[OCR] easyocr unavailable: {e}")

    # 5. PIL image text metadata / chunk info fallback for image files
    try:
        image = Image.open(io.BytesIO(image_bytes))
        if hasattr(image, 'info') and image.info:
            for k, v in image.info.items():
                if isinstance(v, str) and len(v.strip()) >= 10:
                    return v.strip()
                elif isinstance(v, bytes):
                    try:
                        decoded = v.decode('utf-8', errors='ignore')
                        if len(decoded.strip()) >= 10:
                            return decoded.strip()
                    except Exception:
                        pass
    except Exception:
        pass

    return extracted_text.strip()
