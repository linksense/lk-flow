#!/usr/bin/env python
# encoding: utf-8
# Created by zza on 2021/6/30 11:13
# Copyright 2021 LinkSense Technology CO,. Ltd
import os
from typing import Any, Callable, Dict, List

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
    ) -> str:
        """将task保存至yaml"""
        if not os.path.exists(file_path) or not os.path.isdir(file_path):
            raise DirNotFoundError(f"dir {file_path} not exists")
        path = os.path.join(file_path, f"{task.name}.yaml")

        if not force and os.path.exists(path):
            raise YamlFileExistsError(f"{path} exists")
        yaml_str = yaml.dump(task.dict(), sort_keys=False)
        with open(path, "w", encoding="utf8") as f:
            f.write(yaml_str)
        return yaml_str

    @classmethod
    def get_commands(cls, mod_config: Dict[str, Any]) -> Dict[str, Callable]:
        """增加系统默认命令"""
        return {
            "read_yaml_file": cls.read_yaml_file,
            "convert_config_to_yaml": cls.convert_config_to_yaml,
        }

    @classmethod
    def convert_config_to_yaml(cls) -> None:
        """supervisor config convert to yaml"""
        file_list = [
            file_name
            for file_name in os.listdir(os.getcwd())
            if file_name.endswith(".ini")
        ]
        for file_name in file_list:
            print(f"{file_name} convert:")
            convert_file_list = cls._parser_config(file_name)
            for result in convert_file_list:
                print(" " * 2, result)

    @classmethod
    def _parser_config(cls, file_name: str) -> List[str]:
        import configparser

        _start = len("program:")
        parser = configparser.ConfigParser()
        parser.read(file_name)
        file_list = []
        for element in parser.sections():
            if "program:" not in element:
                print(f"{file_name} not supervisor config. pass")
                break

            task = Task(
                name=element[_start:],
                command=parser.get(element, "command", fallback=None),
                directory=parser.get(element, "directory", fallback=None),
                auto_restart=parser.getboolean(element, "auto_restart", fallback=False),
                restart_retries=parser.getint(element, "startretries", fallback=0),
                environment=parser.get(element, "environment", fallback=None),
            )
            if os.path.exists(f"{task.name}.yaml"):
                file_list.append(f"{task.name}.yaml existed")
                continue
            cls.dump_to_file(task, ".", force=False)
            file_list.append(f"{task.name}.yaml")
        return file_list
