# <<<./ Import Libraries
import io
from typing import Any
from PIL import Image

# <<<./ Load Image from UI
def load_image(uploaded_file: Any, max_size: int = 1024):
    try:
        image = Image.open(io.BytesIO(uploaded_file.read())).convert('RGB')
        if max(image.size) > max_size:
            image.thumbnail((max_size, max_size), Image.LANCZOS)
    except Exception as e:
        raise ValueError(f'Cannot open uploaded file as image: {e}') \
            from e

    return image


