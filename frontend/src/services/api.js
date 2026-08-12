import { config } from '../config';

/**
 * Converts a file object into a Base64-encoded Data URL string.
 */
const fileToBase64 = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => resolve(reader.result);
    reader.onerror = (error) => reject(error);
  });
};

/**
 * Submits the PDF file and tag classification to the FastAPI backend OCR endpoint.
 * Throws a structured object containing a 'message' string on failure.
 */
export async function submitOcr(tag, pdfFile, engine = 'chandra') {
  try {
    if (!tag) {
      throw new Error('A document classification tag must be selected.');
    }
    if (!pdfFile) {
      throw new Error('A PDF file must be uploaded.');
    }

    // Convert file to base64
    const base64Data = await fileToBase64(pdfFile);

    const endpoint = engine === 'docling' ? 'ocr/docling' : 'ocr';
    const url = `${config.apiBaseUrl}/api/v1/${endpoint}`;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        tag: tag,
        pdf_base64: base64Data
      })
    });

    if (!response.ok) {
      let errorMessage = `Server error (${response.status})`;
      try {
        const errorJson = await response.json();
        if (errorJson && errorJson.detail) {
          if (typeof errorJson.detail === 'string') {
            errorMessage = errorJson.detail;
          } else if (Array.isArray(errorJson.detail)) {
            errorMessage = errorJson.detail.map(d => d.msg || JSON.stringify(d)).join(', ');
          } else {
            errorMessage = JSON.stringify(errorJson.detail);
          }
        } else if (errorJson && errorJson.message) {
          errorMessage = errorJson.message;
        }
      } catch (err) {
        try {
          const rawText = await response.text();
          if (rawText) errorMessage = rawText;
        } catch (textErr) {}
      }
      throw new Error(errorMessage);
    }

    const data = await response.json();
    return data; // returns OcrResponse: { tag, markdown, pages_processed, model_used, processing_time_ms }
  } catch (error) {
    // Return a structured error with a message property
    throw {
      message: error.message || 'An unexpected networking error occurred. Please verify the backend is running.'
    };
  }
}
