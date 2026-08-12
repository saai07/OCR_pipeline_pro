import React, { useMemo, useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { 
  Copy, 
  Check, 
  FileText, 
  Terminal, 
  Clock, 
  Layers,
  List
} from 'lucide-react';

export default function SideBySideViewer({ file, tag, result, status }) {
  const [copied, setCopied] = useState(false);
  const [isOutlineOpen, setIsOutlineOpen] = useState(true);
  const [activeSection, setActiveSection] = useState(null);
  const [highlightedSectionId, setHighlightedSectionId] = useState(null);

  // Generate original PDF URL object
  const fileUrl = useMemo(() => {
    if (!file) return null;
    return URL.createObjectURL(file);
  }, [file]);

  // Clean up object URL when component unmounts or file changes
  useEffect(() => {
    return () => {
      if (fileUrl) URL.revokeObjectURL(fileUrl);
    };
  }, [fileUrl]);

  // Handle copying of markdown text
  const handleCopy = () => {
    if (result && result.markdown) {
      navigator.clipboard.writeText(result.markdown);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleSectionClick = (idx) => {
    setActiveSection(idx);
    const sectionId = `section-${idx}`;
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
      setHighlightedSectionId(idx);
      setTimeout(() => {
        setHighlightedSectionId(null);
      }, 3000);
    }
  };

  const renderChildContent = (child) => {
    if (!child.content) return null;
    const isHtml = child.content.trim().startsWith('<') || child.content.trim().includes('</');
    
    if (child.type === 'Table' || isHtml) {
      return (
        <div 
          className="rendered-html-body"
          dangerouslySetInnerHTML={{ __html: child.content }} 
        />
      );
    }
    
    return (
      <ReactMarkdown remarkPlugins={[remarkGfm]}>
        {child.content}
      </ReactMarkdown>
    );
  };

  if (!file && !result) {
    return (
      <div className="viewer-placeholder">
        <FileText size={48} className="placeholder-icon" />
        <h3>No Document Loaded</h3>
        <p>Upload a PDF document and select a category classification tag to run OCR.</p>
      </div>
    );
  }

  return (
    <div className="viewer-grid">
      {/* Viewer Header */}
      <div className="viewer-header">
        <div className="header-doc-title">
          <FileText size={18} />
          <span>{file ? file.name : 'Processed Result'}</span>
          {tag && <span className="header-tag-badge">{tag.toUpperCase()}</span>}
          {result && result.sections && result.sections.length > 0 && (
            <button 
              onClick={() => setIsOutlineOpen(!isOutlineOpen)} 
              className="outline-toggle-btn"
              style={{ marginLeft: '16px' }}
              title="Toggle Document Outline Sidebar"
            >
              <List size={14} />
              <span>{isOutlineOpen ? 'Hide Outline' : 'Show Outline'}</span>
            </button>
          )}
        </div>
        
        {result && (
          <div className="header-stats">
            <div className="stat-item" title="Model Used">
              <Terminal size={14} />
              <span>{result.model_used.split('/').pop()}</span>
            </div>
            <div className="stat-item" title="Pages Processed">
              <Layers size={14} />
              <span>{result.pages_processed} page(s)</span>
            </div>
            <div className="stat-item" title="Processing Time">
              <Clock size={14} />
              <span>{(result.processing_time_ms / 1000).toFixed(2)}s</span>
            </div>
          </div>
        )}
      </div>

      {/* Main Panels with Outline Sidebar wrapper */}
      <div className="panels-container-with-outline">
        {/* Outline Sidebar */}
        {result && result.sections && result.sections.length > 0 && (
          <div className={`outline-sidebar ${isOutlineOpen ? '' : 'collapsed'}`}>
            <div className="outline-header">
              <span>Document Outline</span>
            </div>
            <ul className="outline-list">
              {result.sections.map((sec, idx) => (
                <li key={idx} style={{ marginBottom: '4px' }}>
                  <button
                    className={`outline-item ${activeSection === idx ? 'active' : ''}`}
                    onClick={() => handleSectionClick(idx)}
                    title={sec.section_title}
                  >
                    {sec.section_title}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="panels-container">
        
        {/* Left Panel: Original PDF Viewer (Native Browser PDF renderer) */}
        <div className="panel pdf-panel">
          <div className="panel-header">
            <h3>Original PDF</h3>
          </div>
          
          <div className="panel-body pdf-view-wrapper-native">
            {fileUrl ? (
              <iframe
                src={`${fileUrl}#toolbar=0&navpanes=0&view=FitH`}
                width="100%"
                height="100%"
                style={{ border: 'none', borderRadius: '4px' }}
                title="PDF Viewer"
              />
            ) : (
              <div className="pdf-empty-state">
                <p>No source PDF uploaded.</p>
              </div>
            )}
          </div>
        </div>

        {/* Right Panel: Extracted Markdown Viewer */}
        <div className="panel md-panel">
          <div className="panel-header">
            <h3>Extracted Markdown</h3>
            {result && (
              <button onClick={handleCopy} className="copy-btn" title="Copy Markdown to Clipboard">
                {copied ? (
                  <>
                    <Check size={16} className="icon-success" />
                    <span>Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy size={16} />
                    <span>Copy</span>
                  </>
                )}
              </button>
            )}
          </div>
          
          <div className="panel-body scrollable markdown-body">
            {status === 'loading' ? (
              <div className="markdown-loading-state">
                <div className="shimmer-lines">
                  <div className="shimmer-line header"></div>
                  <div className="shimmer-line text long"></div>
                  <div className="shimmer-line text med"></div>
                  <div className="shimmer-line text long"></div>
                  <div className="shimmer-line table"></div>
                </div>
                <p>Waiting for model transcription details...</p>
              </div>
            ) : result && result.sections && result.sections.length > 0 ? (
              <div className="sections-container">
                {result.sections.map((sec, idx) => (
                  <div 
                    key={idx} 
                    id={`section-${idx}`} 
                    className={`section-block ${highlightedSectionId === idx ? 'active-section-highlight' : ''}`}
                    style={{ 
                      marginBottom: '24px', 
                      padding: '16px', 
                      borderRadius: '6px',
                      borderLeft: activeSection === idx ? '3px solid var(--primary)' : '1px solid var(--border-color)',
                      borderTop: '1px solid var(--border-color)',
                      borderRight: '1px solid var(--border-color)',
                      borderBottom: '1px solid var(--border-color)',
                      background: 'var(--bg-surface)',
                      transition: 'all 0.3s ease'
                    }}
                  >
                    <h3 className="section-block-title" style={{ fontSize: '15px', fontWeight: '700', marginBottom: '16px', color: 'var(--text-primary)', borderBottom: '1px solid var(--border-color)', paddingBottom: '8px' }}>
                      {sec.section_title}
                    </h3>
                    <div className="section-block-children">
                      {sec.children.map((child, cIdx) => (
                        <div key={cIdx} className="child-block" style={{ marginBottom: '14px' }}>
                          {renderChildContent(child)}
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : result && result.markdown ? (
              result.markdown.trim().startsWith('<') || result.markdown.trim().includes('</') ? (
                <div 
                  className="rendered-html-body"
                  dangerouslySetInnerHTML={{ __html: result.markdown }} 
                />
              ) : (
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {result.markdown}
                </ReactMarkdown>
              )
            ) : (
              <div className="markdown-empty-state">
                <Terminal size={36} className="empty-icon" />
                <p>Output markdown text will render here once the OCR pipeline completes.</p>
              </div>
            )}
          </div>
        </div>

      </div>
      </div>
    </div>
  );
}
