import asyncio
import httpx
from fastapi import HTTPException, status
from typing import Dict, List
from app.config import settings

class VLLMClient:
    """
    A singleton HTTP client wrapper for interfacing with the vLLM API server.
    Ensures connection pooling and reuse of the same AsyncClient instance.
    """
    def __init__(self):
        self.client: httpx.AsyncClient = None

    def init_client(self) -> None:
        """
        Initializes the shared httpx.AsyncClient with custom connection pooling and timeout settings.
        """
        # OCR requests with multiple pages may take longer. We set a generous 180s timeout.
        limits = httpx.Limits(max_keepalive_connections=10, max_connections=20)
        timeout = httpx.Timeout(180.0, connect=10.0, read=180.0)
        self.client = httpx.AsyncClient(limits=limits, timeout=timeout)

    async def close_client(self) -> None:
        """
        Closes the active httpx.AsyncClient session.
        """
        if self.client:
            await self.client.aclose()
            self.client = None

    async def run_inference(self, payload: Dict, base_url: str) -> str:
        """
        Sends the compiled payload to the OpenAI-compatible chat completions endpoint.
        """
        if self.client is None:
            raise RuntimeError("HTTP Client is not initialized. Ensure lifespan start handler runs.")

        url = f"{base_url.rstrip('/')}/chat/completions"

        headers = {}
        if settings.VLLM_API_KEY:
            headers["Authorization"] = f"Bearer {settings.VLLM_API_KEY}"

        try:
            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
        except httpx.TimeoutException as te:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=f"Connection/read timeout occurred while contacting the vLLM server: {str(te)}"
            )
        except httpx.HTTPStatusError as hse:
            # Try parsing JSON error response first
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            
            # Print error to terminal console for debugging
            print("\n" + "=" * 60)
            print(f"vLLM CLIENT ERROR (HTTP {hse.response.status_code}):")
            print(f"URL: {url}")
            print(f"Response Content: {error_body}")
            print("=" * 60 + "\n")

            raise HTTPException(
                status_code=hse.response.status_code,
                detail=f"vLLM server returned an error: {error_body}"
            )
        except httpx.RequestError as re:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to connect to the vLLM server: {str(re)}"
            )

        try:
            response_data = response.json()
            choices = response_data.get("choices", [])
            if not choices:
                raise ValueError("Response body does not contain choices field.")
            
            content = choices[0].get("message", {}).get("content")
            if content is None:
                raise ValueError("Response choices message content is null.")
                
            return content
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Invalid format returned from vLLM server: {str(e)}"
            )

    async def run_inference_page(self, payload: Dict, base_url: str, semaphore: asyncio.Semaphore) -> str:
        """
        Runs inference for a single page payload, bound by a semaphore to limit concurrency.
        """
        async with semaphore:
            return await self.run_inference(payload, base_url)

    async def run_inference_batch(self, payloads: List[Dict], base_url: str, max_concurrency: int = 4) -> List[str]:
        """
        Runs a list of inference payloads concurrently, ensuring a max concurrency level.
        Preserves the original order of the pages.
        """
        semaphore = asyncio.Semaphore(max_concurrency)
        tasks = [self.run_inference_page(p, base_url, semaphore) for p in payloads]
        # asyncio.gather preserves output list order matching tasks input order
        return list(await asyncio.gather(*tasks))

# Singleton instance for application usage
vllm_client = VLLMClient()
