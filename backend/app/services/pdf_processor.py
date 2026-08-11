import pymupdf
import base64
import asyncio
from typing import List

def sync_pdf_to_images(pdf_bytes: bytes, dpi: int, max_pages: int) -> List[str]:
    """
    Synchronous function to convert PDF bytes to a list of base64-encoded JPEG strings using PyMuPDF.
    """
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    base64_strings = []
    
    # Process up to max_pages
    num_pages = min(len(doc), max_pages)
    for i in range(num_pages):
        page = doc.load_page(i)
        
        # Calculate scaling matrix for custom DPI
        # Default PDF resolution is 72 DPI. Matrix scales zoom accordingly.
        zoom = dpi / 72.0
        matrix = pymupdf.Matrix(zoom, zoom)
        
        # Render page to a pixmap (image)
        pix = page.get_pixmap(matrix=matrix)
        
        # Convert pixmap directly to JPEG bytes at 95% quality
        jpeg_bytes = pix.tobytes("jpeg", jpg_quality=95)
        
        # Encode to base64
        img_str = base64.b64encode(jpeg_bytes).decode("utf-8")
        base64_strings.append(img_str)
        
    doc.close()
    return base64_strings

async def pdf_to_images(pdf_base64: str, dpi: int, max_pages: int) -> List[str]:
    """
    Asynchronously decodes a base64 PDF, converts its pages to images using PyMuPDF in an executor,
    and returns a list of base64-encoded PNG image strings.
    """
    try:
        # Strip potential data URI prefix (e.g. 'data:application/pdf;base64,')
        if "," in pdf_base64:
            pdf_base64 = pdf_base64.split(",", 1)[1]
            
        # Clean whitespaces
        pdf_base64 = pdf_base64.strip()
        
        # Add missing base64 padding characters if necessary
        missing_padding = len(pdf_base64) % 4
        if missing_padding:
            pdf_base64 += "=" * (4 - missing_padding)
            
        pdf_bytes = base64.b64decode(pdf_base64)
    except Exception as e:
        raise ValueError(f"Failed to decode PDF base64 string: {str(e)}")

    if not pdf_bytes:
        raise ValueError("Decoded PDF byte stream is empty.")

    loop = asyncio.get_running_loop()

    try:
        # Run the CPU-bound PyMuPDF extraction in the default thread pool executor
        base64_images = await loop.run_in_executor(
            None,
            sync_pdf_to_images,
            pdf_bytes,
            dpi,
            max_pages
        )
        return base64_images
    except Exception as e:
        raise RuntimeError(f"Error occurred during PDF to image conversion: {str(e)}")
