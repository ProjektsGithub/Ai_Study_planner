/**
 * Error formatting utilities
 * Safely extracts user-friendly string error messages from API responses,
 * preventing React rendering crashes when errors contain objects or arrays
 * (e.g. FastAPI/Pydantic validation error details).
 */

/**
 * Safely extracts a user-readable string error message from an API error response or Error object.
 *
 * @param {any} err - The error caught from an API call
 * @param {string} [fallback='Une erreur est survenue.'] - Default fallback message
 * @returns {string} Safe string message to display in UI components
 */
export const formatApiError = (err, fallback = 'Une erreur est survenue.') => {
  if (!err) return fallback;

  // Direct string error
  if (typeof err === 'string') return err;

  const detail = err.response?.data?.detail ?? err.detail ?? err.response?.data?.message ?? err.message;

  // Pydantic 422 validation errors: array of { loc, msg, type, input, ctx }
  if (Array.isArray(detail)) {
    const formatted = detail
      .map((e) => {
        if (typeof e === 'string') return e;
        if (e && typeof e === 'object') {
          // Format field location e.g. ["body", "cursus"] -> "cursus"
          let field = '';
          if (Array.isArray(e.loc)) {
            field = e.loc.filter((l) => l !== 'body').join('.');
          }
          const msg = e.msg || e.message || JSON.stringify(e);
          return field ? `${field}: ${msg}` : msg;
        }
        return String(e);
      })
      .filter(Boolean)
      .join(', ');

    return formatted || fallback;
  }

  // Nested object with msg or message
  if (detail && typeof detail === 'object') {
    return detail.msg || detail.message || JSON.stringify(detail);
  }

  if (typeof detail === 'string' && detail.trim().length > 0) {
    return detail;
  }

  return fallback;
};

export default formatApiError;
