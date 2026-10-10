"""
Reality Sculptor — WebSocket State Manager
============================================

Manages WebSocket connections between the Python backend and
Unreal Engine 5 / Frontend clients.

The backend SENDS simulation state updates:
- simulation_state
- water_field
- heat_field
- traffic_state
- infrastructure_state
- intervention_state
- causal_events
- sensor_events

Unreal renders them. Unreal NEVER independently invents
the simulation result.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger


class StateChannel(str, Enum):
    """WebSocket channels for different state types."""
    SIMULATION = "simulation_state"
    WATER_FIELD = "water_field"
    HEAT_FIELD = "heat_field"
    TRAFFIC = "traffic_state"
    INFRASTRUCTURE = "infrastructure_state"
    INTERVENTION = "intervention_state"
    CAUSAL = "causal_events"
    SENSOR = "sensor_events"
    CINEMATIC = "cinematic_events"
    SYSTEM = "system_status"
    DRIFT = "drift_events"
    QUESTIONS = "questions"


@dataclass
class ConnectedClient:
    """Represents a connected WebSocket client."""
    client_id: str
    websocket: WebSocket
    subscribed_channels: set[StateChannel] = field(default_factory=lambda: set(StateChannel))
    client_type: str = "unknown"  # "unreal", "frontend", "monitor"


class WebSocketManager:
    """
    Centralized WebSocket manager for real-time state synchronization.

    Ensures Unreal Engine and frontend clients receive state updates
    from the single source of truth (World State Engine).

    Usage:
        manager = WebSocketManager()
        await manager.connect(websocket, client_id="unreal-01", client_type="unreal")
        await manager.broadcast_state(StateChannel.WATER_FIELD, water_data)
    """

    def __init__(self) -> None:
        self._clients: dict[str, ConnectedClient] = {}
        self._lock = asyncio.Lock()
        self._event_history: list[dict[str, Any]] = []
        self._max_history = 1000

    async def connect(
        self,
        websocket: WebSocket,
        client_id: str,
        client_type: str = "unknown",
        channels: set[StateChannel] | None = None,
    ) -> ConnectedClient:
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        client = ConnectedClient(
            client_id=client_id,
            websocket=websocket,
            subscribed_channels=channels or set(StateChannel),
            client_type=client_type,
        )
        async with self._lock:
            self._clients[client_id] = client
        logger.info(
            f"WebSocket connected: {client_id} (type={client_type}, "
            f"channels={len(client.subscribed_channels)})"
        )

        # Send initial handshake
        await self._send_to_client(client, {
            "type": "handshake",
            "client_id": client_id,
            "available_channels": [c.value for c in StateChannel],
            "system": "Reality Sculptor",
            "version": "0.1.0-mvp",
        })

        return client

    async def disconnect(self, client_id: str) -> None:
        """Remove a disconnected client."""
        async with self._lock:
            if client_id in self._clients:
                del self._clients[client_id]
                logger.info(f"WebSocket disconnected: {client_id}")

    async def broadcast_state(
        self,
        channel: StateChannel,
        data: dict[str, Any],
        exclude: str | None = None,
    ) -> int:
        """
        Broadcast state update to all subscribed clients.

        Args:
            channel: The state channel to broadcast on
            data: The state data to send
            exclude: Client ID to exclude from broadcast

        Returns:
            Number of clients that received the message
        """
        message = {
            "type": "state_update",
            "channel": channel.value,
            "data": data,
        }

        # Record in history
        self._event_history.append(message)
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]

        sent_count = 0
        disconnected: list[str] = []

        async with self._lock:
            clients = list(self._clients.items())

        for client_id, client in clients:
            if client_id == exclude:
                continue
            if channel not in client.subscribed_channels:
                continue
            try:
                await self._send_to_client(client, message)
                sent_count += 1
            except (WebSocketDisconnect, RuntimeError):
                disconnected.append(client_id)

        # Clean up disconnected clients
        for cid in disconnected:
            await self.disconnect(cid)

        return sent_count

    async def broadcast_channel(self, channel_name: str, data: dict[str, Any]) -> int:
        """Convenience method to broadcast by channel string name."""
        channel_map = {
            "simulation": StateChannel.SIMULATION,
            "interventions": StateChannel.INTERVENTION,
            "causal": StateChannel.CAUSAL,
            "sensor": StateChannel.SENSOR,
            "drift": StateChannel.DRIFT,
            "water": StateChannel.WATER_FIELD,
            "heat": StateChannel.HEAT_FIELD
        }
        ch = channel_map.get(channel_name.lower(), StateChannel.SIMULATION)
        return await self.broadcast_state(ch, data)


    async def send_simulation_event(
        self,
        event_type: str,
        data: dict[str, Any],
    ) -> None:
        """
        Send a cinematic/simulation event.

        Event types (for camera system):
        - RAIN_START, RUNOFF_START, DRAIN_STRESS, DRAIN_OVERFLOW
        - FLOOD_ZONE_CREATED, ROAD_CLOSED, TRAFFIC_REROUTE
        - EMERGENCY_ROUTE_DEGRADED, CAUSAL_DISCOVERY
        - INTERVENTION_FOUND, INTERVENTION_INSTALLED
        - WORLD_REACTION, SENSOR_CONTRADICTION
        - REALITY_DRIFT, REPLAN
        """
        await self.broadcast_state(StateChannel.CINEMATIC, {
            "event_type": event_type,
            **data,
        })

    async def send_water_field(
        self,
        water_depths: list[list[float]],
        flow_vectors: list[list[tuple[float, float]]] | None = None,
        bounds: dict[str, float] | None = None,
        timestamp: float = 0.0,
    ) -> None:
        """
        Send water depth field to Unreal for rendering.

        Water visualization must follow the flow field:
        - accumulate in depressions
        - follow terrain gradients
        - interact with roads and drainage
        """
        await self.broadcast_state(StateChannel.WATER_FIELD, {
            "water_depths": water_depths,
            "flow_vectors": flow_vectors,
            "bounds": bounds,
            "timestamp": timestamp,
        })

    async def send_heat_field(
        self,
        surface_temperatures: list[list[float]],
        human_exposure: list[list[float]] | None = None,
        bounds: dict[str, float] | None = None,
        sun_position: dict[str, float] | None = None,
    ) -> None:
        """Send spatial heat field to Unreal for heat haze and material rendering."""
        await self.broadcast_state(StateChannel.HEAT_FIELD, {
            "surface_temperatures": surface_temperatures,
            "human_exposure": human_exposure,
            "bounds": bounds,
            "sun_position": sun_position,
        })

    async def send_traffic_state(
        self,
        road_segments: list[dict[str, Any]],
        congestion_level: float,
        emergency_routes: list[dict[str, Any]] | None = None,
    ) -> None:
        """Send traffic state for vehicle density and speed rendering."""
        await self.broadcast_state(StateChannel.TRAFFIC, {
            "road_segments": road_segments,
            "congestion_level": congestion_level,
            "emergency_routes": emergency_routes,
        })

    async def send_intervention_state(
        self,
        intervention_id: str,
        phase: str,
        progress: float,
        visual_changes: list[dict[str, Any]],
    ) -> None:
        """
        Send intervention installation state for visual animation.

        Phases: PROPOSED, INSTALLING, ACTIVE, DEGRADING, FAILED
        """
        await self.broadcast_state(StateChannel.INTERVENTION, {
            "intervention_id": intervention_id,
            "phase": phase,
            "progress": progress,
            "visual_changes": visual_changes,
        })

    async def send_drift_alert(
        self,
        drift_level: str,
        variable: str,
        expected: float,
        observed: float,
        details: dict[str, Any],
    ) -> None:
        """Send reality drift detection event."""
        await self.broadcast_state(StateChannel.DRIFT, {
            "drift_level": drift_level,
            "variable": variable,
            "expected": expected,
            "observed": observed,
            "details": details,
        })

    @staticmethod
    async def _send_to_client(
        client: ConnectedClient, message: dict[str, Any]
    ) -> None:
        """Send a JSON message to a specific client."""
        await client.websocket.send_json(message)

    @property
    def connected_count(self) -> int:
        """Number of currently connected clients."""
        return len(self._clients)

    @property
    def client_ids(self) -> list[str]:
        """List of connected client IDs."""
        return list(self._clients.keys())
