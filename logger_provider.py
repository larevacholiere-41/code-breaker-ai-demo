import logging
from pathlib import Path
from logging import Logger
from typing import Dict


class LoggerProvider:
    __loggers: Dict[str, Logger] = {}

    @classmethod
    def get_logger(cls, name: str) -> Logger:
        if name not in cls.__loggers:
            cls.__loggers[name] = logging.getLogger(name)
            cls.__loggers[name].setLevel(logging.INFO)
            log_dir = Path("logs")
            log_dir.mkdir(parents=True, exist_ok=True)
            handler = logging.FileHandler(log_dir / f"{name}.log")
            handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
            cls.__loggers[name].addHandler(handler)

        return cls.__loggers[name]
