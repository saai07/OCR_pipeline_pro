from pydantic import BaseModel, Field

class OcrRequest(BaseModel):
    tag: str = Field(..., description="The classification tag/category of the document (e.g. BMR, COA)")
    pdf_base64: str = Field(..., description="Base64 encoded string of the PDF file")

class OcrResponse(BaseModel):
    tag: str = Field(..., description="The classification tag processed")
    markdown: str = Field(..., description="The extracted markdown contents of the document")
    pages_processed: int = Field(..., description="Number of pages converted and processed")
    model_used: str = Field(..., description="The name of the LLM model used for extraction")
    processing_time_ms: float = Field(..., description="Total time taken to process the request in milliseconds")
