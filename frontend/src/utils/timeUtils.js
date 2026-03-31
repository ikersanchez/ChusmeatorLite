/**
 * Formats a date string into a relative time (e.g., "2 hours ago", "Yesterday").
 * @param {string} dateString - ISO date string.
 * @returns {string} - Formatted relative time.
 */
export const formatRelativeTime = (dateString) => {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);
    
    if (diffInSeconds < 60) {
        return 'Just now';
    }
    
    const diffInMinutes = Math.floor(diffInSeconds / 60);
    if (diffInMinutes < 60) {
        return `${diffInMinutes}m ago`;
    }
    
    const diffInHours = Math.floor(diffInMinutes / 60);
    if (diffInHours < 24) {
        return `${diffInHours}h ago`;
    }
    
    const diffInDays = Math.floor(diffInHours / 24);
    if (diffInDays === 1) {
        return 'Yesterday';
    }
    
    if (diffInDays < 7) {
        return `${diffInDays}d ago`;
    }
    
    return date.toLocaleDateString();
};
