from typing import Optional
from pydantic import BaseModel
from dotenv import load_dotenv
import os


class Config(BaseModel):
    '''
    Settings class for centralized access to environment variables.
    '''
    BASE_MODEL: str = 'gpt-5-mini'
    OPENAI_API_KEY: str

    GUESSER_MAX_ATTEMPTS: int = 15

    FASTAPI_HOST: str = '0.0.0.0'
    FASTAPI_PORT: int = 5013
    FASTAPI_RELOAD: bool = False
    FASTAPI_ROOT_PATH: str = '/'


class ConfigProvider:
    __config: Optional[Config] = None

    @classmethod
    def get_config(cls) -> Config:
        if cls.__config is None:
            cls.__config = cls.__load_config()
        return cls.__config

    @classmethod
    def __load_config(cls) -> Config:

        load_dotenv(override=True)
        config = Config.model_validate(os.environ)
        return config
