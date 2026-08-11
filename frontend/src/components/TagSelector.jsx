import React from 'react';
import { config } from '../config';
import { Tag } from 'lucide-react';

/**
 * TagSelector - A controlled dropdown component for selecting the document classification.
 * Configured dynamically from config.allowedTags.
 */
export default function TagSelector({ value, onChange }) {
  const tags = config.allowedTags || [];

  return (
    <div className="tag-selector-container">
      <label htmlFor="tag-select" className="input-label">
        <Tag size={16} className="label-icon" />
        Document Tag / Classification
      </label>
      <div className="select-wrapper">
        <select
          id="tag-select"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="custom-select"
        >
          <option value="">-- Select Document Category --</option>
          {tags.map((tag) => (
            <option key={tag} value={tag}>
              {tag.toUpperCase().replace(/_/g, ' ')}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
