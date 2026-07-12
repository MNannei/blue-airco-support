from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "blue-airco-support"
    app_env: str = "development"
    database_url: str = (
        "postgresql://blue_airco:local-development-only@localhost:5432/"
        "blue_airco_support"
    )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
