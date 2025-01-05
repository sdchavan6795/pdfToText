import os
from pdf2image import convert_from_path
from PIL import Image, ImageEnhance, ImageOps
import pytesseract
from io import BytesIO
import json

# Configurable Options
OCR_LANG = "eng+mar"
OCR_PSM = 6

def ensure_image_mode(image):
    if image.mode not in ("RGB", "L"):
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        else:
            image = image.convert("L")
    return image

def enhance_image(image):
    image = ensure_image_mode(image)
    image = ImageOps.autocontrast(image)
    image = image.filter(ImageFilter.MedianFilter(size=5))
    image = image.point(lambda p: 0 if p < 150 else 255, mode='1')
    image = image.filter(ImageFilter.MaxFilter(size=3))
    image = image.filter(ImageFilter.SHARPEN)
    enhancer = ImageEnhance.Contrast(image)
    enhanced_image = enhancer.enhance(2.5)
    return enhanced_image

def extract_text(image):
    custom_config = f"--psm {OCR_PSM}"
    return pytesseract.image_to_string(image, lang=OCR_LANG, config=custom_config)

def handler(request):
    try:
        # Receive the PDF file (can be sent as multipart/form-data in POST request)
        file = request.files.get('file')  # Assuming you send the file as part of the request

        if not file:
            return json.dumps({"error": "No file provided"}), 400
        
        # Convert the uploaded PDF file to images
        images = convert_from_path(file, dpi=600)
        
        extracted_text = []
        for image in images:
            enhanced_image = enhance_image(image)
            text = extract_text(enhanced_image)
            extracted_text.append(text)

        return json.dumps({"texts": extracted_text}), 200

    except Exception as e:
        return json.dumps({"error": str(e)}), 500
