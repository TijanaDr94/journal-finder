""" Application configuration """


from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """ Settings for the Journal Finder service. """
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    cors_origins: str = "*"

    app_title: str = "MDPI Journal Finder"
    app_version: str = "0.1.0"


settings = Settings()
