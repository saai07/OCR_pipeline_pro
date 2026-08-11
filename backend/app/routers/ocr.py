import time
from fastapi import APIRouter, HTTPException, status
from app.models.schemas import OcrRequest, OcrResponse
from app.config import settings
from app.services.pdf_processor import pdf_to_images
from app.services.prompt_builder import build_chunk_payload
from app.services.vllm_client import vllm_client

router = APIRouter()

@router.post(
    "/ocr",
    response_model=OcrResponse,
    status_code=status.HTTP_200_OK,
    summary="Process PDF OCR",
    description="Decodes a base64 PDF, converts pages to images, builds the vision prompt, runs inference, and returns extraction markdown."
)
async def process_ocr(request: OcrRequest):
    # 1. Validate tag
    allowed_tags = settings.allowed_tags_list
    if request.tag not in allowed_tags:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tag '{request.tag}'. Allowed tags: {', '.join(allowed_tags)}"
        )

    # 2. Validate PDF base64 format and size
    if not request.pdf_base64.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PDF base64 content cannot be empty."
        )

    # Clean the base64 string if it contains commas
    base64_data = request.pdf_base64
    if "," in base64_data:
        base64_data = base64_data.split(",", 1)[1]

    # Base64 encoding represents approximately 3 bytes of data for every 4 characters.
    estimated_size_bytes = (len(base64_data) * 3) // 4
    max_size_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    if estimated_size_bytes > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"The uploaded PDF size (estimated {estimated_size_bytes / (1024*1024):.2f}MB) exceeds the maximum allowed upload limit of {settings.MAX_UPLOAD_SIZE_MB}MB."
        )

    # 3. Process PDF and call vLLM
    start_time = time.perf_counter()
    try:
        # Step A: Convert PDF to base64 images per page
        image_list = await pdf_to_images(
            pdf_base64=request.pdf_base64,
            dpi=settings.PDF_DPI,
            max_pages=settings.PDF_MAX_PAGES
        )

        pages_processed = len(image_list)
        if pages_processed == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="PDF did not yield any page images for processing. Ensure file is not corrupted."
            )

        # Step B: Chunk pages and build payloads
        chunk_size = settings.CHUNK_SIZE
        payloads = []
        for start_idx in range(0, pages_processed, chunk_size):
            chunk = image_list[start_idx : start_idx + chunk_size]
            start_page = start_idx + 1
            payload = await build_chunk_payload(
                tag=request.tag,
                image_b64_list=chunk,
                start_page=start_page,
                total_pages=pages_processed,
                model_name=settings.VLLM_MODEL_NAME,
                max_tokens=settings.VLLM_MAX_TOKENS,
                temperature=settings.VLLM_TEMPERATURE
            )
            payloads.append(payload)

        # Step C: Send payloads to vLLM Server concurrently (using CONCURRENCY_LIMIT)
        markdown_results = await vllm_client.run_inference_batch(
            payloads=payloads,
            base_url=settings.VLLM_BASE_URL,
            max_concurrency=settings.CONCURRENCY_LIMIT
        )

        # Combine results into a single markdown output separated by page dividers
        markdown_result = "\n\n---\n\n".join(markdown_results)

    except HTTPException as he:
        # Reraise FastAPI HTTPExceptions directly
        raise he
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation failed: {str(ve)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during OCR pipeline execution: {str(e)}"
        )

    end_time = time.perf_counter()
    processing_time_ms = (end_time - start_time) * 1000

    return OcrResponse(
        tag=request.tag,
        markdown=markdown_result,
        pages_processed=pages_processed,
        model_used=settings.VLLM_MODEL_NAME,
        processing_time_ms=round(processing_time_ms, 2)
    )
