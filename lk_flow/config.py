#!/usr/bin/python3
# encoding: utf-8
import os
from collections import defaultdict
from typing import Any, Dict

import yaml


class Config:
    """
    大写字母的配置将读入flask app
    """

    LOG_FORMAT = (
        "[%(asctime)s] [%(threadName)s:%(thread)d] [%(levelname)s]: "
        "%(message)s [%(pathname)s <%(lineno)d>]"
    )
    LOG_LEVEL = "DEBUG"

    # import os ; print(os.urandom(24))
    SECRET_KEY = b""

    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_recycle": 1800}

    SQLALCHEMY_DATABASE_URI = "sqlite:///{}".format(
        os.path.join(os.path.abspath("."), "lk_flow.db")
    )

    sentry_dns = None
    # 配置文件
    sleep_time = 5
    # mod config
    mod_dir: str = None
    mod_config: Dict[str, Dict[str, Any]] = defaultdict(dict)

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
            print("read {} values:".format(config_path))
            mod_config = (entries or {}).pop("mod_config", defaultdict(dict))
            self.__dict__.update(entries or {})
            print("config:", self.__dict__, "\nmod_config:")
            for _mod_name, _mod_config in mod_config.items():
                self.mod_config[_mod_name] = _mod_config
                print(f"  [{_mod_name}]:{_mod_config}")


conf = Config()
