import React, { useRef, useState } from 'react';
import { UploadCloud, FileText, CheckCircle2, AlertCircle } from 'lucide-react';

/**
 * PdfUploader - Handles drag-and-drop and manual file uploads for PDFs.
 * Validates document type (application/pdf) client-side.
 */
export default function PdfUploader({ file, setFile }) {
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  const validateAndSetFile = (selectedFile) => {
    setError(null);
    if (!selectedFile) return;

    if (selectedFile.type !== 'application/pdf' && !selectedFile.name.toLowerCase().endsWith('.pdf')) {
      setError('Only PDF documents are supported.');
      return;
    }

    setFile(selectedFile);
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const triggerBrowse = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = 2;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  };

  return (
    <div className="pdf-uploader-container">
      <div 
        className={`drop-zone ${dragActive ? 'drag-active' : ''} ${file ? 'has-file' : ''} ${error ? 'has-error' : ''}`}
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
      >
        <input 
          ref={fileInputRef}
          type="file" 
          className="file-input-hidden" 
          accept="application/pdf"
          onChange={handleFileChange}
        />
        
        <div className="drop-zone-content">
          {file ? (
            <div className="file-info-view">
              <CheckCircle2 size={36} className="icon-success" />
              <div className="file-details">
                <p className="file-name">{file.name}</p>
                <p className="file-size">{formatBytes(file.size)}</p>
              </div>
              <button 
                type="button" 
                onClick={(e) => {
                  e.stopPropagation();
                  setFile(null);
                }} 
                className="change-file-btn"
              >
                Clear
              </button>
            </div>
          ) : (
            <div className="prompt-view" onClick={triggerBrowse}>
              <UploadCloud size={40} className="icon-upload" />
              <p className="primary-text">
                Drag and drop your PDF here, or <span className="browse-text">browse files</span>
              </p>
              <p className="secondary-text">PDF format only</p>
            </div>
          )}
        </div>
      </div>
      
      {error && (
        <div className="uploader-error">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}
