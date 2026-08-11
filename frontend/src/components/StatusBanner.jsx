import React from 'react';
import { Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';

/**
 * StatusBanner - Informs the user of current OCR pipeline status.
 * Renders state-specific designs: loading animations, failure alerts, or run metadata.
 */
export default function StatusBanner({ status, error, result }) {
  if (status === 'idle') return null;

  if (status === 'loading') {
    return (
      <div className="status-banner loading">
        <div className="status-body">
          <Loader2 className="spinner" size={24} />
          <div className="status-text">
            <h4 className="status-title">Processing OCR...</h4>
            <p className="status-desc">Converting PDF pages, compiling vision inputs, and requesting model inference. This may take up to 2-3 minutes for multi-page documents.</p>
          </div>
        </div>
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="status-banner error">
        <div className="status-body">
          <AlertCircle className="icon-error" size={24} />
          <div className="status-text">
            <h4 className="status-title">Extraction Failed</h4>
            <p className="status-desc">{error || 'An unknown server error occurred.'}</p>
          </div>
        </div>
      </div>
    );
  }

  if (status === 'success' && result) {
    const { model_used, pages_processed, processing_time_ms } = result;
    return (
      <div className="status-banner success">
        <div className="status-body">
          <CheckCircle2 className="icon-success" size={24} />
          <div className="status-text">
            <h4 className="status-title">Extraction Complete!</h4>
            <p className="status-desc">Successfully converted document text into structured markdown format.</p>
          </div>
        </div>
        <div className="metadata-pills">
          <div className="meta-pill">
            <span className="pill-label">Pages</span>
            <span className="pill-val">{pages_processed}</span>
          </div>
          <div className="meta-pill">
            <span className="pill-label">Model</span>
            <span className="pill-val-model" title={model_used}>
              {model_used.split('/').pop()}
            </span>
          </div>
          <div className="meta-pill">
            <span className="pill-label">Latency</span>
            <span className="pill-val">{(processing_time_ms / 1000).toFixed(2)}s</span>
          </div>
        </div>
      </div>
    );
  }

  return null;
}
