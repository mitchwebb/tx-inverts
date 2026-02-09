import logging
import logging.config

LOGGING_CONFIG = {
    "version": 1,
    "formatters": {
        "default": {
            "format": "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": "backend.log",
            "formatter": "default",
        }
    },

    "loggers": {
        "api": {
            "handlers": ["console"],
            "level": "INFO",
        },
        "data": {
            "handlers": ["file"],
            "level": "INFO",
        },
        "tasks": {
            "handlers": ["file"],
            "level": "INFO",
        },
        "db": {
            "handlers": ["file"],
            "level": "ERROR",
        },
        "security": {
            "handlers": ["file"],
            "level": "WARNING",
        },
    },
}


def setup_logging():
    logging.config.dictConfig(LOGGING_CONFIG)


# Export canonical loggers
api_logger = logging.getLogger("api")
db_logger = logging.getLogger("db")
security_logger = logging.getLogger("security")
data_logger = logging.getLogger("data")
tasks_logger = logging.getLogger("tasks")
