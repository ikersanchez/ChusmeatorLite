from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    database_url: str = "sqlite:///./chusmeator.db"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    # LocationIQ API for address search
    locationiq_url: str = "https://us1.locationiq.com/v1/search"
    locationiq_api_key: str = ""
    # Secret key required in X-Admin-Key header to access /api/admin/* endpoints
    admin_key: str = ""
    # Secret key for session signing (change in production!)
    secret_key: str = "dev-secret-key-change-me-12345"
    session_cookie_name: str = "chusmeator_session"
    deepseek_api_key: str = ""
    
    # Abuse prevention limits
    max_pins_per_day: int = 20
    max_areas_per_day: int = 20
    max_comments_per_day: int = 20
    max_area_size_deg: float = 0.02  # Approx 2.2km (adjusted to 0.02)
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

