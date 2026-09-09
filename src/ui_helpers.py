import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

_font_cache = {}

def get_font(size=18, bold=False):
    key = (size, bold)
    if key not in _font_cache:
        windir = os.environ.get("WINDIR", "C:\\Windows")
        fname = "segoeuib.ttf" if bold else "segoeui.ttf"
        fpath = os.path.join(windir, "Fonts", fname)
        if not os.path.exists(fpath):
            fname = "arialbd.ttf" if bold else "arial.ttf"
            fpath = os.path.join(windir, "Fonts", fname)
        try:
            _font_cache[key] = ImageFont.truetype(fpath, size)
        except Exception:
            _font_cache[key] = ImageFont.load_default()
    return _font_cache[key]

def draw_clean_text(img, text, pos, font_size=18, color=(255, 255, 255), bold=False, shadow=True):
    """
    Renders crystal-clear, anti-aliased modern typography onto OpenCV images.
    color is in BGR format (matching OpenCV standard).
    """
    x, y = pos
    font = get_font(font_size, bold)
    
    # Fast convert to PIL
    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    
    # Convert BGR to RGB for PIL
    b, g, r = color
    rgb_color = (r, g, b)
    
    # Optional soft drop-shadow for high contrast and readability on any background
    if shadow:
        draw.text((x + 1, y + 1), text, font=font, fill=(0, 0, 0))
        
    draw.text((x, y), text, font=font, fill=rgb_color)
    
    # Convert back to BGR numpy array
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
