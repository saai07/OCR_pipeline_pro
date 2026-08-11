import React, { useState, useEffect } from 'react';
import { useOcr } from './hooks/useOcr';
import TagSelector from './components/TagSelector';
import PdfUploader from './components/PdfUploader';
import StatusBanner from './components/StatusBanner';
import SideBySideViewer from './components/SideBySideViewer';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Send, Eye, Copy, Check, X, FileText, Download } from 'lucide-react';

/**
 * App - Main root component of the React application.
 * Manages the form state, layout flow, and handles triggers to the useOcr hook.
 * Integrates a full-screen popup modal for side-by-side original PDF vs markdown comparison.
 */
export default function App() {
  const [tag, setTag] = useState('');
  const [file, setFile] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const { status, result, error, submit } = useOcr();

  // Disable body scroll when modal is open to prevent page scrolling behind the modal
  useEffect(() => {
    if (isModalOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isModalOpen]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (tag && file && status !== 'loading') {
      submit(tag, file);
    }
  };

  const handleCopy = () => {
    if (result && result.markdown) {
      navigator.clipboard.writeText(result.markdown);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownload = () => {
    if (result && result.markdown) {
      const element = document.createElement("a");
      const fileBlob = new Blob([result.markdown], { type: 'text/markdown' });
      element.href = URL.createObjectURL(fileBlob);
      const downloadName = file ? `${file.name.replace(/\.pdf$/i, '')}_extracted.md` : 'extracted_document.md';
      element.download = downloadName;
      document.body.appendChild(element);
      element.click();
      document.body.removeChild(element);
    }
  };

  const isSubmitDisabled = !tag || !file || status === 'loading';

  return (
    <div className="app-container">
      {/* Top Application Header */}
      <header className="app-header">
        <div className="header-brand">
          <h1>OCR Pipeline</h1>
        </div>
      </header>

      {/* Control Panel and Workspace Form */}
      <main className="app-main">
        <div className="control-panel">
          <form onSubmit={handleSubmit} className="ocr-form">
            <div className="inputs-row">
              <TagSelector value={tag} onChange={setTag} />
              <PdfUploader file={file} setFile={setFile} />
            </div>

            <button 
              type="submit" 
              disabled={isSubmitDisabled} 
              className={`submit-btn ${isSubmitDisabled ? 'btn-disabled' : 'btn-active'} ${status === 'loading' ? 'btn-loading' : ''}`}
            >
              {status === 'loading' ? (
                <>
                  <span className="spinner-border"></span>
                  <span>Invoking Model...</span>
                </>
              ) : (
                <>
                  <Send size={16} />
                  <span>Execute OCR Extraction</span>
                </>
              )}
            </button>
          </form>
        </div>

        {/* Real-time Status Banner */}
        <StatusBanner status={status} error={error} result={result} />

        {/* Extracted Markdown Result Card (Main Dashboard View) */}
        {result && result.markdown && (
          <div className="results-section">
            <div className="results-header">
              <div className="results-title-group">
                <FileText size={20} className="text-secondary" />
                <h2>Extracted Markdown</h2>
              </div>
              <div className="results-actions">
                <button onClick={handleCopy} className="action-btn copy-btn" title="Copy Markdown to Clipboard">
                  {copied ? (
                    <>
                      <Check size={14} className="icon-success" />
                      <span>Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy size={14} />
                      <span>Copy Markdown</span>
                    </>
                  )}
                </button>
                <button onClick={handleDownload} className="action-btn download-btn" title="Download as .md file">
                  <Download size={14} />
                  <span>Download .md</span>
                </button>
                <button onClick={() => setIsModalOpen(true)} className="action-btn compare-btn" title="View side by side with PDF">
                  <Eye size={14} />
                  <span>View Side-by-Side</span>
                </button>
              </div>
            </div>
            
            <div className="results-body markdown-body">
              {result.markdown.trim().startsWith('<') || result.markdown.trim().includes('</') ? (
                <div 
                  className="rendered-html-body"
                  dangerouslySetInnerHTML={{ __html: result.markdown }} 
                />
              ) : (
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {result.markdown}
                </ReactMarkdown>
              )}
            </div>
          </div>
        )}
      </main>

      {/* Side-by-Side Comparison Popup Modal */}
      {isModalOpen && (
        <div className="modal-overlay" onClick={() => setIsModalOpen(false)}>
          <div className="modal-content-container" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close-btn" onClick={() => setIsModalOpen(false)} title="Close Comparison View">
              <X size={18} />
            </button>
            <SideBySideViewer file={file} tag={tag} result={result} status={status} />
          </div>
        </div>
      )}

    </div>
  );
}
