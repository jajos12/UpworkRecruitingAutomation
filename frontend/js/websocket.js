// WebSocket connection management

let ws = null;
let reconnectTimeout = null;
const RECONNECT_DELAY = 3000;

function connectWebSocket() {
    try {
        ws = new WebSocket(CONFIG.WS_URL);

        ws.onopen = () => {
            console.log('✅ WebSocket connected');
            updateConnectionStatus(true);
            clearTimeout(reconnectTimeout);
        };

        ws.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                handleWebSocketMessage(message);
            } catch (error) {
                console.error('Failed to parse WebSocket message:', error);
            }
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        ws.onclose = () => {
            console.log('❌ WebSocket disconnected');
            updateConnectionStatus(false);

            // Attempt to reconnect
            reconnectTimeout = setTimeout(() => {
                console.log('🔄 Attempting to reconnect...');
                connectWebSocket();
            }, RECONNECT_DELAY);
        };

    } catch (error) {
        console.error('Failed to connect WebSocket:', error);
        reconnectTimeout = setTimeout(connectWebSocket, RECONNECT_DELAY);
    }
}

function handleWebSocketMessage(message) {
    console.log('📨 WebSocket message:', message);

    switch (message.type) {
        case 'connected':
            showToast('Connected to server', 'success');
            break;

        case 'activity':
            addActivityItem(message);
            break;

        case 'progress':
            updateProgress(message);
            break;

        case 'stats_update':
            updateStats(message.stats);
            break;

        case 'error':
            showToast(message.message, 'error');
            addActivityItem({
                event_type: 'error',
                message: message.message,
                timestamp: message.timestamp
            });
            break;

        default:
            console.log('Unknown message type:', message.type);
    }
}

function updateConnectionStatus(connected) {
    const statusEl = document.getElementById('connectionStatus');
    if (!statusEl) return;

    const dotEl = statusEl.querySelector('.status-dot');
    const textEl = statusEl.querySelector('.status-text');

    if (connected) {
        statusEl.classList.add('connected');
        textEl.textContent = 'Connected';
    } else {
        statusEl.classList.remove('connected');
        textEl.textContent = 'Disconnected';
    }
}

function updateProgress(message) {
    // You can add a nice progress bar UI here if needed
    console.log(`Progress: ${message.phase} - ${(message.progress * 100).toFixed(0)}%: ${message.message}`);

    addActivityItem({
        event_type: 'progress',
        message: `${message.message} (${(message.progress * 100).toFixed(0)}%)`,
        timestamp: message.timestamp
    });
}

// Initialize WebSocket on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', connectWebSocket);
} else {
    connectWebSocket();
}
