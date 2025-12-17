"""
OCR Module (Optical Character Recognition).
Extracts text from images using Tesseract.
"""

import sys
from loguru import logger
from colorama import Fore, Style
from core.engine import Profile

META = {
    'description': 'Extracts text from images (requires Tesseract)',
    'target_type': 'file, url',
    'requirements': 'tesseract-ocr'
}

def scan(target: str, profile: Profile) -> None:
    """Run OCR on target."""
    print(f"{Fore.CYAN}[+] Running OCR...{Style.RESET_ALL}")
    
    try:
        import pytesseract
        from PIL import Image
        import requests
        from io import BytesIO
    except ImportError:
        print(f"  {Fore.RED}└─ Failed: Missing dependencies (pytesseract, Pillow). Run 'pip install pytesseract Pillow'{Style.RESET_ALL}")
        return

    images_to_scan = []
    
    # 1. If target is a local file
    if target.endswith(('.png', '.jpg', '.jpeg', '.gif')):
        images_to_scan.append(target)
        
    # 2. Check profile for any discovered image URLs
    # (generic gathering from other modules)
    if 'images' in profile.raw_data:
        images_to_scan.extend(profile.raw_data['images'])
        
    if not images_to_scan:
        print(f"  {Fore.YELLOW}└─ No images found to scan.{Style.RESET_ALL}")
        return
        
    for img_path in images_to_scan:
        try:
            text = ""
            if img_path.startswith('http'):
                response = requests.get(img_path, timeout=5)
                img = Image.open(BytesIO(response.content))
                text = pytesseract.image_to_string(img)
            else:
                # Local file
                img = Image.open(img_path)
                text = pytesseract.image_to_string(img)
                
            if text.strip():
                print(f"  {Fore.GREEN}└─ Text found in {img_path}:{Style.RESET_ALL}")
                preview = text.replace('\n', ' ')[:50]
                print(f"     \"{preview}...\"")
                
                # Store in profile
                profile.raw_data.setdefault('ocr_results', []).append({
                    'source': img_path,
                    'text': text
                })
                
                # Scan extracted text for secrets?
                # Using the existing regex patterns from other modules could be cool here.
                
        except Exception as e:
            logger.error(f"OCR failed for {img_path}: {e}")
            print(f"  {Fore.RED}└─ Error reading {img_path}{Style.RESET_ALL}")
