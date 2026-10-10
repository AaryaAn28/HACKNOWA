import asyncio
import random

class DemoSequencer:
    def __init__(self, seed: int = 42, websocket_manager=None):
        self.seed = seed
        self.rng = random.Random(seed)
        self.websocket_manager = websocket_manager

    async def broadcast(self, message: dict):
        if self.websocket_manager:
            await self.websocket_manager.broadcast(message)
        else:
            print(f"Mock Broadcast: {message}")

    async def play_sequence(self):
        """Play the 90-second cinematic demo sequence."""
        # 0-8s: Cinematic flyover
        await self.broadcast({"event": "camera_mode", "mode": "cinematic_flyover", "location": "Houston"})
        await asyncio.sleep(8)
        
        # 8-15s: Reality Scan
        await self.broadcast({"event": "overlay", "type": "reality_scan", "status": "detecting"})
        await asyncio.sleep(7)
        
        # 15-22s: World reconstruction status
        await self.broadcast({"event": "status_display", "message": "World reconstruction complete"})
        await asyncio.sleep(7)
        
        # 22-30s: Disaster trigger
        await self.broadcast({"event": "weather", "type": "rainfall", "intensity": "progressive"})
        await asyncio.sleep(8)
        
        # 30-42s: Flood simulation
        await self.broadcast({"event": "simulation", "type": "flood", "state": "active"})
        await asyncio.sleep(12)
        
        # 42-48s: Causal X-Ray
        await self.broadcast({"event": "overlay", "type": "causal_xray", "highlight": "failure_chain"})
        await asyncio.sleep(6)
        
        # 48-52s: Critical nodes pulse
        await self.broadcast({"event": "highlight", "targets": "critical_nodes", "action": "pulse"})
        await asyncio.sleep(4)
        
        # 52-58s: Question Engine
        await self.broadcast({"event": "ui_prompt", "questions": ["What is the root cause?", "How can we mitigate this?"]})
        await asyncio.sleep(6)
        
        # 58-65s: Intervention generation
        await self.broadcast({"event": "intervention", "status": "generating", "mode": "minimal_force"})
        await asyncio.sleep(7)
        
        # 65-72s: Multi-future stress test
        await self.broadcast({"event": "visualization", "type": "multi_future", "status": "stress_testing"})
        await asyncio.sleep(7)
        
        # 72-78s: Virtual installation
        await self.broadcast({"event": "intervention", "action": "install", "upgrades": ["drain", "bioswale"]})
        await asyncio.sleep(6)
        
        # 78-84s: World reacts
        await self.broadcast({"event": "simulation", "type": "recovery", "water": "receding", "traffic": "recovering"})
        await asyncio.sleep(6)
        
        # 84-88s: Reality Drift alert
        await self.broadcast({"event": "alert", "type": "reality_drift", "cause": "sensor_contradiction"})
        await asyncio.sleep(4)
        
        # 88-93s: Automatic replan
        await self.broadcast({"event": "intervention", "action": "replan", "status": "new_intervention_applied"})
        await asyncio.sleep(5)
        
        # 93-95s: Final impact dashboard
        await self.broadcast({"event": "ui_display", "type": "impact_dashboard", "status": "final"})
        await asyncio.sleep(2)
