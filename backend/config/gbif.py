# GBIF settings class
from pydantic_settings import BaseSettings


# GBIF
class GBIFSettings(BaseSettings):
    user: str
    password: str
    email: str

    # UAT Endpoint Credentials
    # The GBIF UAT requires another account, so these are optional
    # The test using this is skipped if they are not provided
    uat_user: str | None = None
    uat_email: str | None = None
    uat_password: str | None = None
