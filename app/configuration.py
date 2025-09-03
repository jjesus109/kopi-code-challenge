from pydantic_settings import BaseSettings


class Configuration(BaseSettings):

    port: int
    host: str
    log_level: str
    db_host: str
    db_port: str
    db_user: str
    db_password: str
    db_name: str
    db_motor: str
    google_api_key: str
