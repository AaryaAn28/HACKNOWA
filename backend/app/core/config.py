from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 100
    SIMULATION_GRID_RESOLUTION: float = 1.0
    DEFAULT_CRS: str = "EPSG:4326"
    ML_MODEL_DIR: str = "./models"
    WEBSOCKET_HEARTBEAT_SEC: int = 30
    DEMO_MODE: bool = False
    DEMO_SEED: int = 42
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
