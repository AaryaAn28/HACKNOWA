import enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import datetime

class SensorType(enum.Enum):
    WATER_LEVEL = "WATER_LEVEL"
    RAIN_GAUGE = "RAIN_GAUGE"
    TEMPERATURE = "TEMPERATURE"
    TRAFFIC = "TRAFFIC"
    AIR_QUALITY = "AIR_QUALITY"
    FLOW_METER = "FLOW_METER"
    PRESSURE = "PRESSURE"

@dataclass
class Sensor:
    id: str
    type: SensorType
    location: tuple
    current_value: float
    confidence: float
    last_reading: datetime.datetime
    status: str

class DriftHistory:
    def __init__(self):
        self.drifts: List[Dict[str, Any]] = []
        
    def log_drift(self, sensor_id: str, predicted: float, actual: float, timestamp: datetime.datetime):
        self.drifts.append({
            "sensor_id": sensor_id, 
            "predicted": predicted, 
            "actual": actual, 
            "timestamp": timestamp,
            "error_percentage": abs(predicted - actual) / actual if actual != 0 else float('inf')
        })

class SensorNetwork:
    """
    Sensor Network & Reality Feedback Service.
    Ingests live data and compares with simulation predictions (Reality Feedback Lock).
    """
    def __init__(self):
        self.sensors: Dict[str, Sensor] = {}
        self.drift_history = DriftHistory()
        self.reality_drift_threshold = 0.15 # 15% error threshold for REALITY_DRIFT
        
    def register_sensor(self, sensor: Sensor):
        self.sensors[sensor.id] = sensor
        
    def remove_sensor(self, sensor_id: str):
        if sensor_id in self.sensors:
            del self.sensors[sensor_id]
            
    def ingest_reading(self, sensor_id: str, value: float, timestamp: datetime.datetime):
        """Ingests readings from CSV, JSON, API, or MQTT."""
        if sensor_id in self.sensors:
            sensor = self.sensors[sensor_id]
            sensor.current_value = value
            sensor.last_reading = timestamp
            
    def check_reality_feedback_lock(self, predictions: Dict[str, float]) -> bool:
        """
        Compares simulation predictions against real sensor readings.
        When residual error > threshold, declares REALITY_DRIFT.
        """
        drift_detected = False
        for sensor_id, predicted_value in predictions.items():
            if sensor_id in self.sensors:
                actual_value = self.sensors[sensor_id].current_value
                if actual_value != 0:
                    error = abs(predicted_value - actual_value) / actual_value
                    if error > self.reality_drift_threshold:
                        drift_detected = True
                        self.drift_history.log_drift(sensor_id, predicted_value, actual_value, datetime.datetime.now())
                        self.trigger_recalibration()
                        
        if drift_detected:
            self.trigger_replan()
        return not drift_detected
        
    def trigger_recalibration(self):
        """Automatic recalibration trigger."""
        pass
        
    def trigger_replan(self):
        """Replan trigger initiated by REALITY_DRIFT."""
        pass
