// Configuration for frontend application

const CONFIG = {
    // API endpoints
    API_BASE_URL: window.location.origin,
    API_PREFIX: '/api',
    
    // WebSocket
    WS_URL: `ws://${window.location.host}/ws`,
    
    // Tier thresholds (must match backend)
    TIER_1_THRESHOLD: 85,
    TIER_2_THRESHOLD: 70,
    
    // UI settings
    TOAST_DURATION: 5000, // milliseconds
    ACTIVITY_FEED_MAX_ITEMS: 100,
};

// Helper to build API URLs
function apiUrl(path) {
    return `${CONFIG.API_BASE_URL}${CONFIG.API_PREFIX}${path}`;
}
