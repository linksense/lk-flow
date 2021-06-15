#!/usr/bin/python3
# encoding: utf-8
import os

import yaml


class Config:
    """
    大写字母的配置将读入flask app
    """

    LOG_FORMAT = (
        "[%(asctime)s] [%(uuid)s] [%(threadName)s:%(thread)d] [%(levelname)s]: "
        "%(message)s [%(pathname)s <%(lineno)d>]"
    )
    LOG_LEVEL = "DEBUG"

    # import os ; print(os.urandom(24))
    SECRET_KEY = b""

    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_recycle": 1800}

    SQLALCHEMY_DATABASE_URI = "sqlite:///lk_flow.db"
    MONGODB_SETTINGS = {
        "DB": "lk_flow",
        "host": "mongodb://<user>:<password>@127.0.0.1:27017/lk_flow",
    }

    sentry_dns = None
    redis_url = "redis://127.0.0.1:6379"

    def __init__(self):
        """
        >>> os.environ["lk_flow_config_path"] = os.path.abspath("lk_flow_config.yaml")
        >>> Config()
        read config.yaml from...
        """
        _default_path = "lk_flow_config.yaml"
        config_path = os.environ.get("lk_flow_config_path", _default_path)
        if config_path != _default_path:
            print("read config.yaml from : {}".format(config_path))

        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf8") as f:
                entries = yaml.safe_load(f)
            self.__dict__.update(entries or {})
            print("read {} values:".format(config_path))
            print(self.__dict__)


conf = Config()
