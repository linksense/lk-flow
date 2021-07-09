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

    log_save_dir = "/var/log/lk_flow"
    sentry_dns = None
    # 配置文件
    sleep_time = 5
    # mod config
    mod_dir: str = None
    mod_config: Dict[str, Dict[str, Any]] = defaultdict(dict)
    mod_config["SQLOrmMod"]["SQLALCHEMY_DATABASE_URI"] = "sqlite:///lk_flow.db"

    # Flag
    mod_loaded: bool = False  # 是否需要加载mod 避免重复加载而报错

    def __init__(self):
        """
        >>> os.environ["lk_flow_config_path"] = os.path.abspath("lk_flow_config.yaml")
        >>> Config()
        <lk_flow.config.Config object at...
        """
        import logging

        _default_path = "lk_flow_config.yaml"
        config_path = os.environ.get("lk_flow_config_path", _default_path)

        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf8") as f:
                entries = yaml.safe_load(f)

            mod_config = (entries or {}).pop("mod_config", defaultdict(dict))
            self.__dict__.update(entries or {})

            logger = logging.getLogger("lk_flow")
            logger.setLevel(self.LOG_LEVEL)
            logger.info("read {} values:".format(config_path))
            logger.info(f"config:{self.__dict__}\nmod_config:")
            for _mod_name, _mod_config in mod_config.items():
                self.mod_config[_mod_name] = _mod_config
                logger.info(f"  [{_mod_name}]:{_mod_config}")

            if config_path != _default_path:
                logger.info("read config.yaml from : {}".format(config_path))


conf = Config()
