"""WebSocket connection manager for real-time updates."""

from typing import List, Dict, Any
from datetime import datetime
from fastapi import WebSocket
import json
import asyncio


class WebSocketManager:
    """
    Manages WebSocket connections and broadcasts events.
    
    Used for real-time updates to the frontend during pipeline execution.
    """
    
    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        # Send welcome message
        await self.send_personal_message({
            "type": "connected",
            "message": "WebSocket connection established",
            "timestamp": datetime.now().isoformat()
        }, websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send message to a specific connection."""
        try:
            await websocket.send_json(message)
        except Exception:
            # Connection closed, remove it
            self.disconnect(websocket)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients."""
        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = datetime.now().isoformat()
        
        # Send to all connections
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)
    
    async def broadcast_activity(self, event_type: str, message: str, data: Dict[str, Any] = None):
        """Broadcast an activity event."""
        await self.broadcast({
            "type": "activity",
            "event_type": event_type,
            "message": message,
            "data": data or {},
            "timestamp": datetime.now().isoformat()
        })
    
    async def broadcast_progress(self, phase: str, progress: float, message: str):
        """Broadcast pipeline progress update."""
        await self.broadcast({
            "type": "progress",
            "phase": phase,
            "progress": progress,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
    
    async def broadcast_error(self, error_message: str):
        """Broadcast an error message."""
        await self.broadcast({
            "type": "error",
            "message": error_message,
            "timestamp": datetime.now().isoformat()
        })
    
    async def broadcast_stats(self, stats: Dict[str, Any]):
        """Broadcast updated statistics."""
        await self.broadcast({
            "type": "stats_update",
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        })


# Global instance
ws_manager = WebSocketManager()
