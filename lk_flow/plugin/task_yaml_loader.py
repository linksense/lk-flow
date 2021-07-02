#!/usr/bin/env python
# encoding: utf-8
# Created by zza on 2021/6/30 11:13
# Copyright 2021 LinkSense Technology CO,. Ltd
import os
from typing import Any, Dict

import yaml
from lk_flow.core import Context, ModAbstraction
from lk_flow.env import logger
from lk_flow.models import Task


class TaskYamlLoader(ModAbstraction):
    @classmethod
    def init_mod(cls, mod_config: Dict[str, Any]) -> None:
        """初始化mod 无配置文件夹自动创建"""
        yaml_path = mod_config.get("task_yaml_dir")
        if not os.path.exists(yaml_path):
            os.mkdir(yaml_path)

    @classmethod
    def setup_mod(cls, mod_config: Dict[str, Any]) -> None:
        yaml_path = mod_config.get("task_yaml_dir")

        context = Context.get_instance()
        for file_name in os.listdir(yaml_path):
            with open(os.path.join(yaml_path, file_name), "r", encoding="utf8") as f:
                task_data = yaml.safe_load(f)
            if not task_data:
                logger.info(f"{file_name} is empty")
                continue
            task = Task(**task_data)
            context.add_task(task)

    @classmethod
    def teardown_mod(cls) -> None:
        pass
