from pydantic import BaseSettings

class Settings(BaseSettings):
    app_name: str = 'tlspack admin'
    db_file: str
    class Config:
        env_file = '.env_admin'

