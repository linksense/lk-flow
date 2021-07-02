#!/usr/bin/env python
# encoding: utf-8
# Created by zza on 2021/7/5 14:25
# Copyright 2021 LinkSense Technology CO,. Ltd
from typing import Callable, Dict

import requests
from tabulate import tabulate


class ControlCommands:
    def __init__(
        self, host: str = "0.0.0.0", port: int = 9002, api_path: str = "/lk_flow/api/v1"
    ):
        if host == "0.0.0.0":
            host = "localhost"
        self._base_path = f"http://{host}:{port}{api_path}"

    def get_all_commands(self) -> Dict[str, Callable]:
        ret = dict()
        for attr_name in dir(self):
            if attr_name.startswith("_") or attr_name == "get_all_commands":
                continue
            obj = getattr(self, attr_name)
            if callable(obj):
                ret[attr_name] = obj
        return ret

    def status(self) -> str:
        """系统内task信息"""
        all_result: dict = requests.get(f"{self._base_path}/").json()["data"]

        ret = []
        for task_name, item in all_result.items():
            info = {
                "name": task_name,
                "state": item["state"],
                "pid": item["pid"],
                "last_start_datetime": item["last_start_datetime"],
            }
            ret.append(info)
        table = tabulate(ret, headers="keys")
        return table

    def sys_close(self) -> str:
        """关闭系统"""
        result: str = requests.get(f"{self._base_path}/system_close").json()["message"]
        return result

    def start(self, task_name: str) -> str:
        """启动task"""
        url = f"{self._base_path}/process/{task_name}/start"
        result: str = requests.get(url).json()["data"]["pid"]
        return result

    def stop(self, task_name: str) -> str:
        """手动停止task"""
        url = f"{self._base_path}/process/{task_name}/stop"
        result: str = requests.get(url).json()["data"]["pid"]
        return result
