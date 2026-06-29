"""Digital Workforce Platform — 数字员工平台"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "digital-workforce"
    environment: str = "development"
    api_prefix: str = "/api"

    database_host: str = Field(default="localhost", validation_alias="DATABASE_HOST")
    database_port: int = Field(default=5432, validation_alias="DATABASE_PORT")
    database_user: str = Field(default="postgres", validation_alias="DATABASE_USER")
    database_password: str = Field(default="", validation_alias="DATABASE_PASSWORD")
    database_name: str = Field(default="tactile", validation_alias="DATABASE_NAME")
    database_schema: str = "dw"
    sqlite_path: str = Field(default="", validation_alias="SQLITE_PATH")

    jwt_secret: str = "digital-workforce-dev-secret"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7

    admin_email: str = "admin@spreadx.ai"
    admin_password: str = "Dw@Admin2026"
    qa_email: str = "qa@spreadx.ai"
    qa_password: str = "Dw@Test2026"

    cors_origins: str = "*"

    tactile_api_base: str = Field(default="https://foxrouter.com/api", validation_alias="TACTILE_API_BASE")
    tactile_api_key: str = Field(default="", validation_alias="TACTILE_API_KEY")
    tactile_workspace_id: int = Field(default=0, validation_alias="TACTILE_WORKSPACE_ID")
    tactile_template_agent_id: int = Field(default=0, validation_alias="TACTILE_AGENT_ID")
    tactile_default_model: str = Field(default="gpt-4o", validation_alias="TACTILE_DEFAULT_MODEL")
    tactile_default_runtime_type: str = Field(default="ecs-ubuntu", validation_alias="TACTILE_DEFAULT_RUNTIME_TYPE")
    tactile_skill_creator_agent_id: int = Field(default=0, validation_alias="TACTILE_SKILL_CREATOR_AGENT_ID")
    spider_radar_public_api_base: str = Field(
        default="http://localhost:8000/api", validation_alias="DW_PUBLIC_API_BASE"
    )

    @property
    def database_url(self) -> str:
        if self.sqlite_path:
            return f"sqlite:///{self.sqlite_path}"
        return (
            f"postgresql+psycopg2://{self.database_user}:{self.database_password}"
            f"@{self.database_host}:{self.database_port}/{self.database_name}"
        )

    @property
    def uses_sqlite(self) -> bool:
        return bool(self.sqlite_path)

    @property
    def tactile_base_url(self) -> str:
        return self.tactile_api_base.rstrip("/").removesuffix("/api")


settings = Settings()


@lru_cache
def get_settings() -> Settings:
    return settings
