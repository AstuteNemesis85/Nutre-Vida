/**
 * Safely renders content that might be an object or string
 * @param {any} content - The content to render
 * @returns {string} - A safe string representation
 */
export const renderSafe = (content) => {
  if (content === null || content === undefined) {
    return '';
  }
  
  if (typeof content === 'string') {
    return content;
  }
  
  if (typeof content === 'number' || typeof content === 'boolean') {
    return String(content);
  }
  
  if (typeof content === 'object') {
    // Handle common object patterns that might come from backend
    if (content.type && content.title && content.message) {
      // Notification-like object {type, title, message, priority}
      return `${content.title}: ${content.message}`;
    }
    
    if (content.message) {
      return content.message;
    }
    
    if (content.title) {
      return content.title + (content.message ? `: ${content.message}` : '');
    }
    
    if (content.text) {
      return content.text;
    }
    
    if (content.content) {
      return content.content;
    }
    
    // For arrays, join them with newlines
    if (Array.isArray(content)) {
      return content.map(item => renderSafe(item)).join('\n');
    }
    
    // Last resort: safely stringify the object
    try {
      return JSON.stringify(content, null, 2);
    } catch (e) {
      return 'Unable to display content';
    }
  }
  
  return String(content);
};

export default renderSafe;