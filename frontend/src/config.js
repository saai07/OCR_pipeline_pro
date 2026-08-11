// Config file resolving Vite environment variables with robust fallbacks
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const ALLOWED_TAGS_RAW = import.meta.env.VITE_ALLOWED_TAGS || 'BMR,COA,prescription,lab_report,discharge_summary,radiology_report';

export const config = {
  apiBaseUrl: API_BASE_URL.replace(/\/$/, ''), // Strip trailing slash if present
  allowedTags: ALLOWED_TAGS_RAW.split(',')
    .map(tag => tag.trim())
    .filter(tag => tag.length > 0)
};
