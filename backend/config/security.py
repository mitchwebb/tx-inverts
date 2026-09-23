from pydantic_settings import BaseSettings


class SecuritySettings(BaseSettings):
    turnstile_key: str
