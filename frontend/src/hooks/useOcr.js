import { useState, useCallback } from 'react';
import { submitOcr } from '../services/api';

/**
 * Custom React hook for driving the OCR pipeline process state.
 * Returns { status, result, error, submit }
 * status: 'idle' | 'loading' | 'success' | 'error'
 */
export function useOcr() {
  const [state, setState] = useState({
    status: 'idle',
    result: null,
    error: null
  });

  const submit = useCallback(async (tag, file) => {
    setState({
      status: 'loading',
      result: null,
      error: null
    });

    try {
      const response = await submitOcr(tag, file);
      
      // Clean the markdown output by stripping potential enclosing triple-backtick code blocks
      if (response && response.markdown) {
        let cleaned = response.markdown.trim();
        cleaned = cleaned.replace(/^```markdown\s*/i, '');
        cleaned = cleaned.replace(/^```\s*/, '');
        cleaned = cleaned.replace(/\s*```$/, '');
        response.markdown = cleaned.trim();
      }

      setState({
        status: 'success',
        result: response,
        error: null
      });
    } catch (err) {
      setState({
        status: 'error',
        result: null,
        // err is structured: { message }
        error: err.message || 'An unknown error occurred during the OCR process.'
      });
    }
  }, []);

  return {
    status: state.status,
    result: state.result,
    error: state.error,
    submit
  };
}
