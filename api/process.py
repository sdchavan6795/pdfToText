import os
from pdf2image import convert_from_path
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import pytesseract
from tqdm import tqdm  # For progress bar

# Paths
folder_path = "/home/sumit/Test"
pdf_file = os.path.join(folder_path, "Satara.pdf")
images_folder = os.path.join(folder_path, "images")
output_txt_file = os.path.join(folder_path, "output.txt")

# Configurable Options
OCR_LANG = "eng+mar"  # OCR language (English + Marathi)
OCR_PSM = 6  # OCR page segmentation mode
DEBUG_MODE = True  # Enable detailed error logs for debugging

# Create folders if they don't exist
os.makedirs(images_folder, exist_ok=True)

def extract_images_from_pdf():
    """Extract images from the PDF and save them to the images folder."""
    try:
        print("Extracting images from PDF...")
        images = convert_from_path(pdf_file, dpi=600)  # High DPI for better image quality
        for i, image in enumerate(images, start=1):
            image_path = os.path.join(images_folder, f"page_{i}.png")
            image.save(image_path)
            print(f"Saved image: {image_path}")
    except Exception as e:
        print(f"Error extracting images from PDF: {e}")

def ensure_image_mode(image):
    """Ensure the image is in a supported mode."""
    try:
        if image.mode not in ("RGB", "L"):
            if image.mode in ("RGBA", "P"):  # Handle transparency or indexed colors
                image = image.convert("RGB")
            else:
                image = image.convert("L")  # Convert to grayscale as a fallback
        return image
    except Exception as e:
        if DEBUG_MODE:
            print(f"Error ensuring image mode: {e}")
        return image

def enhance_image(image):
    """Preprocess and enhance the image for better OCR accuracy."""
    try:
        # Ensure correct mode
        image = ensure_image_mode(image)

        # Convert to grayscale if not already
        if image.mode != "L":
            image = image.convert("L")

        # Apply adaptive contrast
        image = ImageOps.autocontrast(image)

        # Apply a larger median filter to reduce dark dots
        image = image.filter(ImageFilter.MedianFilter(size=5))

        # Apply adaptive thresholding to remove noise and preserve text
        image = image.point(lambda p: 0 if p < 150 else 255, mode='1')

        # Dilation to make text more prominent
        image = image.filter(ImageFilter.MaxFilter(size=3))

        # Enhance sharpness for OCR readability
        image = image.filter(ImageFilter.SHARPEN)

        # Enhance contrast
        enhancer = ImageEnhance.Contrast(image)
        enhanced_image = enhancer.enhance(2.5)  # Adjust contrast level as needed

        return enhanced_image
    except Exception as e:
        if DEBUG_MODE:
            print(f"Error enhancing image: {e}")
        return image

def extract_text(image):
    """Extract text from the given image using Tesseract."""
    try:
        custom_config = f"--psm {OCR_PSM}"
        return pytesseract.image_to_string(image, lang=OCR_LANG, config=custom_config)
    except Exception as e:
        if DEBUG_MODE:
            print(f"Error extracting text: {e}")
        return ""

def save_text(image_number, section, text):
    """Save the extracted text to the output file."""
    try:
        with open(output_txt_file, "a", encoding="utf-8") as file:
            file.write(f"Image {image_number} - {section}:\n")
            file.write(text.strip() + "\n\n")
    except Exception as e:
        if DEBUG_MODE:
            print(f"Error saving text for image {image_number} ({section}): {e}")

def process_full_page(image_path, image_number):
    """Extract text from the full page of the image."""
    try:
        # Open the image and handle potential mode issues
        image = Image.open(image_path)
        image = ensure_image_mode(image)

        # Extract full page text
        full_text = extract_text(enhance_image(image))
        save_text(image_number, "Full Page", full_text)
    except Exception as e:
        if DEBUG_MODE:
            print(f"Error processing full page for image {image_path}: {e}")

def process_images():
    """Process all images in the folder and extract text sequentially."""
    try:
        image_files = sorted(
            [f for f in os.listdir(images_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff'))]
        )

        if not image_files:
            print(f"No images found in the folder: {images_folder}")
            return

        print("Starting text extraction from images...")
        with tqdm(total=len(image_files), desc="Processing Images") as pbar:
            for i, image_file in enumerate(image_files, start=1):
                image_path = os.path.join(images_folder, image_file)

                # Process only the full page
                process_full_page(image_path, i)

                pbar.update(1)

        print(f"Processing completed. Extracted text saved to {output_txt_file}")
    except Exception as e:
        print(f"Error processing images: {e}")

if __name__ == "__main__":
    # Clear previous output file
    if os.path.exists(output_txt_file):
        os.remove(output_txt_file)

    # Step 1: Extract images from the PDF
    extract_images_from_pdf()

    # Step 2: Process images to extract text
    process_images()
