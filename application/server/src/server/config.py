from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    sabre_client_id: SecretStr = SecretStr("")
    sabre_client_secret: SecretStr = SecretStr("")
    sabre_user_id: str = ""
    sabre_password: SecretStr = SecretStr("")
    sabre_pcc: str = ""
    sabre_base_url: str = "https://api.cert.platform.sabre.com"
    use_mock: bool | None = None
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    search_ttl_minutes: int = 30
    database_url: str = "sqlite+aiosqlite:///./flynow.db"

    @property
    def resolved_client_id(self) -> str:
        # Sabre's test page lists a user ID + PCC; the token API wants them as V1:<user>:<pcc>:AA.
        if self.sabre_client_id.get_secret_value():
            return self.sabre_client_id.get_secret_value()
        if self.sabre_user_id.startswith("V1:"):
            return self.sabre_user_id
        if self.sabre_user_id and self.sabre_pcc:
            return f"V1:{self.sabre_user_id}:{self.sabre_pcc}:AA"
        return ""

    @property
    def resolved_client_secret(self) -> str:
        return self.sabre_client_secret.get_secret_value() or self.sabre_password.get_secret_value()

    @property
    def has_credentials(self) -> bool:
        return bool(self.resolved_client_id and self.resolved_client_secret)

    @property
    def mock_enabled(self) -> bool:
        if self.use_mock is not None:
            return self.use_mock
        return not self.has_credentials

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
