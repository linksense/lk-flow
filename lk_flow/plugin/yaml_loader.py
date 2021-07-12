#!/usr/bin/env python
# encoding: utf-8
# Created by zza on 2021/6/30 11:13
# Copyright 2021 LinkSense Technology CO,. Ltd
import os
from typing import Any, Callable, Dict

import yaml
from lk_flow.core import Context, ModAbstraction
from lk_flow.env import logger
from lk_flow.errors import DirNotFoundError, YamlFileExistsError
from lk_flow.models import Task


class YamlLoader(ModAbstraction):
    context: Context

    @classmethod
    def init_mod(cls, mod_config: Dict[str, Any]) -> None:
        """初始化mod 无配置文件夹自动创建"""
        yaml_path = mod_config.get("task_yaml_dir")
        if yaml_path and not os.path.exists(yaml_path):
            os.mkdir(yaml_path)

    @classmethod
    def setup_mod(cls, mod_config: Dict[str, Any]) -> None:
        """
        读取 yaml_path位置下的*.yaml文件，将task载入到系统

        Args:
            mod_config: task_yaml_dir 配置地址

        Returns:
            None
        """
        yaml_path = mod_config.get("task_yaml_dir")

        if not yaml_path:
            logger.debug(f"{yaml_path} is None. continue")
            return

        if not os.path.exists(yaml_path):
            logger.warning(f"{yaml_path} not exists")
            return

        cls.context = Context.get_instance()
        for file_name in os.listdir(yaml_path):
            yaml_file_path = os.path.join(yaml_path, file_name)
            cls.read_yaml_file(yaml_file_path)

    @classmethod
    def read_yaml_file(cls, yaml_file_path: str) -> None:
        """将yaml文件载入系统"""
        with open(yaml_file_path, "r", encoding="utf8") as f:
            task_data = yaml.safe_load(f)
        if not task_data:
            logger.info(f"{yaml_file_path} is empty")
            return
        task = Task(**task_data)
        cls.context.add_task(task)
        return

    @classmethod
    def dump_to_file(
        cls, task: Task, file_path: str = "./yaml", force: bool = True
    ) -> None:
        """将task保存至yaml"""
        if not os.path.exists(file_path) or not os.path.isdir(file_path):
            raise DirNotFoundError(f"dir {file_path} not exists")
        path = os.path.join(file_path, f"{task.name}.yaml")

        if not force and os.path.exists(path):
            raise YamlFileExistsError(f"{path} exists")
        yaml_str = yaml.dump(task.dict())
        with open(path, "w", encoding="utf8") as f:
            f.write(yaml_str)
        return

    @classmethod
    def get_commands(cls, mod_config: Dict[str, Any]) -> Dict[str, Callable]:
        """增加系统默认命令"""
        return {"read_yaml_file": cls.read_yaml_file}
