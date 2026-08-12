import os
# Disable PyTorch Dynamo/Inductor JIT compilation to avoid compiler (cl.exe) requirements on Windows
os.environ["TORCH_COMPILE_DISABLE"] = "1"
os.environ["TORCHINDUCTOR_COMPILE_DISABLE"] = "1"
os.environ["TORCH_DYNAMO_DISABLE"] = "1"

# Limit CPU threads to prevent background multi-threading deadlocks in OpenMP/MKL on Windows
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import time
import base64
from typing import List, Dict, Tuple
from huggingface_hub import snapshot_download

from docling.datamodel.pipeline_options import PdfPipelineOptions, RapidOcrOptions
from docling.document_converter import DocumentConverter, InputFormat, PdfFormatOption

class DoclingProcessor:
    """
    Service to convert PDF documents locally using Docling and RapidOCR,
    and parse the DoclingDocument layout into a unified hierarchical sections structure.
    """
    def __init__(self):
        self.converter = None

    def initialize_converter(self):
        """
        Initializes the Docling DocumentConverter with RapidOCR options.
        Downloads ONNX weights from Hugging Face if not already present.
        """
        if self.converter is not None:
            return

        print("Downloading RapidOCR models from Hugging Face Hub...")
        # Download RapidOCR models from HF Hub
        download_path = snapshot_download(repo_id="SWHL/RapidOCR")

        # Set up RapidOcrOptions for OCR
        det_model_path = os.path.join(
            download_path, "PP-OCRv4", "en_PP-OCRv3_det_infer.onnx"
        )
        rec_model_path = os.path.join(
            download_path, "PP-OCRv4", "ch_PP-OCRv4_rec_server_infer.onnx"
        )
        cls_model_path = os.path.join(
            download_path, "PP-OCRv3", "ch_ppocr_mobile_v2.0_cls_train.onnx"
        )
        
        ocr_options = RapidOcrOptions(
            det_model_path=det_model_path,
            rec_model_path=rec_model_path,
            cls_model_path=cls_model_path,
        )

        pipeline_options = PdfPipelineOptions(
            ocr_options=ocr_options,
        )

        # Initialize the converter
        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pipeline_options,
                ),
            },
        )
        print("Docling DocumentConverter initialized successfully with RapidOCR.")

    def process_pdf(self, pdf_base64: str) -> Tuple[str, List[Dict]]:
        """
        Decodes a base64 PDF, converts it locally using Docling,
        and constructs the unified hierarchical sections tree.
        """
        # Ensure the converter is initialized
        print("📥 [Docling] Initializing local conversion engine...")
        self.initialize_converter()

        # Create temporary file to pass to Docling
        temp_dir = "temp"
        os.makedirs(temp_dir, exist_ok=True)
        temp_filepath = os.path.join(temp_dir, f"docling_temp_{int(time.time())}.pdf")
        
        try:
            # Decode and write PDF bytes
            print("📥 [Docling] Decoding PDF base64 payload...")
            pdf_bytes = base64.b64decode(pdf_base64)
            with open(temp_filepath, "wb") as f:
                f.write(pdf_bytes)
            
            # Verify file on disk
            if os.path.exists(temp_filepath):
                file_size = os.path.getsize(temp_filepath)
                print(f"📄 [Docling] Temp PDF written to: {temp_filepath} ({file_size} bytes)")
            else:
                print("❌ [Docling] Error: Temp PDF file was not created on disk!")

            # Count total pages using PyMuPDF for progress display
            import fitz
            temp_doc = fitz.open(temp_filepath)
            total_pages = temp_doc.page_count
            temp_doc.close()
            print(f"📄 [Docling] PDF has {total_pages} page(s). Processing on CPU...")

            # Set up a custom logging handler to capture Docling's internal per-page progress
            import logging
            import sys

            class DoclingProgressHandler(logging.Handler):
                """Captures Docling's internal log messages and prints page-level progress."""
                def __init__(self, total):
                    super().__init__()
                    self.total = total
                    self.pages_seen = set()
                
                def emit(self, record):
                    msg = record.getMessage()
                    # Docling logs page processing with "page" in the message
                    if "page" in msg.lower():
                        # Try to extract page numbers from various log formats
                        import re
                        nums = re.findall(r'page[_ ]?(\d+)', msg.lower())
                        for n in nums:
                            page_num = int(n)
                            if page_num not in self.pages_seen:
                                self.pages_seen.add(page_num)
                                print(f"  📄 [Docling] Processing page {len(self.pages_seen)}/{self.total}...", flush=True)

            progress_handler = DoclingProgressHandler(total_pages)
            progress_handler.setLevel(logging.DEBUG)
            
            # Attach handler to root logger and docling-specific loggers
            loggers_to_hook = [
                logging.getLogger("docling"),
                logging.getLogger("docling.pipeline"),
                logging.getLogger("docling.document_converter"),
            ]
            for lgr in loggers_to_hook:
                lgr.setLevel(logging.DEBUG)
                lgr.addHandler(progress_handler)

            # Perform local conversion
            print("⚙️  [Docling] Starting local layout and OCR conversion...", flush=True)
            start_conv = time.perf_counter()
            conversion_result = self.converter.convert(source=temp_filepath)
            doc = conversion_result.document
            end_conv = time.perf_counter()

            # Clean up progress handler
            for lgr in loggers_to_hook:
                lgr.removeHandler(progress_handler)

            print(f"✅ [Docling] Document conversion completed in {end_conv - start_conv:.2f} seconds ({total_pages} pages).")
            
            # Export flat markdown
            print("📝 [Docling] Exporting raw Markdown document...")
            markdown_result = doc.export_to_markdown()

            # Build structured section tree
            print("🌱 [Docling] Analyzing layout tree and segments...")
            sections = []
            current_section = None
            
            sections_count = 0
            texts_count = 0
            tables_count = 0

            for element, level in doc.iterate_items():
                # Extract clean element label/type
                label = str(element.label).split('.')[-1].lower()
                
                # Retrieve bounding box coordinates
                bbox_str = ""
                if hasattr(element, 'prov') and element.prov and len(element.prov) > 0:
                    try:
                        bbox = element.prov[0].bbox
                        bbox_str = f"{int(bbox.l)} {int(bbox.t)} {int(bbox.r)} {int(bbox.b)}"
                    except Exception:
                        pass
                
                # Resolve block content
                content = ""
                if label == 'table':
                    if hasattr(element, 'export_to_html'):
                        try:
                            content = element.export_to_html()
                        except Exception:
                            content = "<table><tr><td>Table Content</td></tr></table>"
                    else:
                        content = "<table><tr><td>Table Content</td></tr></table>"
                else:
                    content = getattr(element, 'text', '')

                # Skip empty paragraphs or texts
                if not content and label != 'table':
                    continue

                # Parse headings as section boundaries
                if label in ('heading', 'section_header', 'title'):
                    sections_count += 1
                    current_section = {
                        "section_title": content.strip(),
                        "bbox": bbox_str,
                        "children": []
                    }
                    sections.append(current_section)
                else:
                    # Fallback section folder if document doesn't start with a heading
                    if not current_section:
                        sections_count += 1
                        current_section = {
                            "section_title": "Document Overview",
                            "bbox": "",
                            "children": []
                        }
                        sections.append(current_section)
                    
                    # Set child content type
                    child_type = "Table" if label == 'table' else ("Image" if label == 'picture' else "Text")
                    
                    if child_type == "Table":
                        tables_count += 1
                    else:
                        texts_count += 1

                    # Ensure table HTML is wrapped inside standard layout div for style matching
                    if child_type == "Table" and not content.startswith("<div"):
                        content = f'<div data-bbox="{bbox_str}" data-label="Table">{content}</div>'

                    current_section["children"].append({
                        "type": child_type,
                        "bbox": bbox_str,
                        "content": content
                    })

            print(f"📊 [Docling] Analysis complete! Found {sections_count} sections, {texts_count} paragraphs, and {tables_count} tables.")
            return markdown_result, sections

        finally:
            # Clean up temp file
            if os.path.exists(temp_filepath):
                try:
                    os.remove(temp_filepath)
                except Exception as clean_err:
                    print(f"Warning: Failed to delete temp docling file: {clean_err}")

docling_processor = DoclingProcessor()
