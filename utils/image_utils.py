from PIL import Image, ImageOps
import os

def process_and_crop_square(source_path: str, destination_path: str, size: int = 150) -> str:
    """Ajusta y recorta una imagen a un cuadrado perfecto centrado sin deformarla."""
    try:
        with Image.open(source_path) as img:
            # Convertir a RGBA/RGB
            img = img.convert("RGB")
            # Recorte centrado
            square_img = ImageOps.fit(img, (size, size), method=Image.Resampling.LANCZOS)
            square_img.save(destination_path, "JPEG", quality=90)
            return destination_path
    except Exception as e:
        print(f"Error procesando imagen: {e}")
        return source_path