import re
import urllib.parse
from pathlib import Path
from PIL import Image
from backend.config import Config

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text.strip('-')

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def format_inr(amount: int) -> str:
    """Format numbers into Indian Rupee style, e.g. 32999 -> ₹32,999"""
    try:
        amount_str = str(int(amount))
        if len(amount_str) <= 3:
            return f"₹{amount_str}"
        last_three = amount_str[-3:]
        other_digits = amount_str[:-3]
        formatted_other = ""
        for i in range(len(other_digits) - 1, -1, -1):
            if (len(other_digits) - 1 - i) % 2 == 0 and i != len(other_digits) - 1:
                formatted_other = "," + formatted_other
            formatted_other = other_digits[i] + formatted_other
        return f"₹{formatted_other},{last_three}"
    except Exception:
        return f"₹{amount}"

def generate_whatsapp_message(product: dict) -> str:
    """Generate pre-filled enquiry message: Hi C2T MOBILES, I'm interested in the [Brand] [Model]. Please share the details and availability."""
    brand = product.get('brand', '').strip()
    model = product.get('model', '').strip()
    title = f"{brand} {model}".strip() if (brand and model) else (model or "smartphone")
    return f"Hi C2T MOBILES, I'm interested in the {title}. Please share the details and availability."

def build_whatsapp_link(phone_number: str, message: str) -> str:
    cleaned_phone = re.sub(r'\D', '', phone_number)
    encoded_text = urllib.parse.quote(message)
    return f"https://wa.me/{cleaned_phone}?text={encoded_text}"

def optimize_and_save_image(file_storage, target_path: Path, max_size=(1200, 1200), quality=85):
    """Resizes and compresses images to maintain high performance."""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.open(file_storage)
    
    # Convert RGBA to RGB if saving as JPEG
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
        
    image.thumbnail(max_size, Image.Resampling.LANCZOS)
    image.save(target_path, "JPEG", quality=quality, optimize=True)
