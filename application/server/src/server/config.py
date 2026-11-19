from functools import lru_cache

from pydantic import SecretStr
from sqlalchemy.engine import URL
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
    # Database: either one DATABASE_URL, or the parts (what the ECS task definition passes).
    # With neither, a local SQLite file is used.
    database_url: str = ""
    db_host: str = ""
    db_port: int = 3306
    db_name: str = ""
    db_username: str = ""
    db_password: SecretStr = SecretStr("")
    db_driver: str = "mysql+aiomysql"

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
    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        if self.db_host and self.db_name:
            # URL.create escapes special characters in the password, which a hand-built string would not.
            return URL.create(
                self.db_driver,
                username=self.db_username or None,
                password=self.db_password.get_secret_value() or None,
                host=self.db_host,
                port=self.db_port,
                database=self.db_name,
            ).render_as_string(hide_password=False)
        return "sqlite+aiosqlite:///./flynow.db"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
