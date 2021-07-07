#!/usr/bin/env python
# encoding: utf-8
# Created by zza on 2021/7/5 14:25
# Copyright 2021 LinkSense Technology CO,. Ltd
import functools
import json
from typing import Callable, Dict, List

import pandas
import requests

from lk_flow.models import Task


class ControlCommands:
    _not_commands: List[str] = ["get_all_commands"]
    _server_no_run_message: str = "lk_flow 服务未启动"

    def __init__(
        self, host: str = "0.0.0.0", port: int = 9002, api_path: str = "/lk_flow/api/v1"
    ):
        if host == "0.0.0.0":
            host = "localhost"
        self._base_path = f"http://{host}:{port}{api_path}"

    def _url_is_listening(self) -> bool:
        """检查端口是否监听"""
        try:
            requests.get(f"{self._base_path}/").json()
        except requests.exceptions.ConnectionError:
            return False
        return True

    def get_all_commands(self) -> Dict[str, Callable]:
        ret = dict()
        for attr_name in dir(self):
            if attr_name.startswith("_") or attr_name in self._not_commands:
                continue
            obj = getattr(self, attr_name)
            if callable(obj):
                ret[attr_name] = obj

        if not self._url_is_listening():

            def wrap_echo_message(func: Callable) -> Callable:
                @functools.wraps(func)
                def echo_message() -> str:
                    return self._server_no_run_message

                return echo_message

            for _func_name, _func in ret.items():
                ret[_func_name] = wrap_echo_message(_func)
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
        df = pandas.DataFrame(ret)
        df = df.set_index("name")
        return str(df)

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
        result: str = requests.get(url).json()["data"]["state"]
        return result

    def restart(self, task_name: str) -> str:
        """重启task"""
        ret = self.stop(task_name)
        if ret != "stop":
            print(f"{task_name} is not running: {ret}")
        return self.start(task_name)

    def create(self, task_json: str = None) -> str:
        """
        创建task

        Example:
            $ lk_flow create "{\"name\": \"t_date\", \"command\": \"date\", \"directory\": \".\"}"
        """
        from lk_flow.plugin.http_stuff._pydantic_input_helper import input_helper

        if task_json:
            if isinstance(task_json, dict):
                obj = Task(**task_json)
            else:
                try:
                    obj = Task(**json.loads(task_json))
                except json.decoder.JSONDecodeError as err:
                    return f"json 解析错误:{err}"
        else:
            obj = input_helper(Task)
            print(f"Task json: {obj.json()}")
        url = f"{self._base_path}/tasks"
        resp = requests.post(url, json=obj.dict())
        result: dict = resp.json()
        return result["message"]

    def delete(self, task_name: str) -> str:
        """删除task"""
        url = f"{self._base_path}/task/{task_name}"
        result: str = requests.delete(url).json()["message"]
        return result

    def persist(
        self, task_name: str, save_type: str = "yaml", force: bool = False
    ) -> str:
        """将task持久保存 sql|yaml"""
        if save_type == "yaml":
            url = f"{self._base_path}/tasks/{task_name}/preservation/yaml"
            data = {"force": force, "file_path": "."}
            result: str = requests.post(url, json=data).json()["message"]
            return result
        elif save_type == "sql":
            url = f"{self._base_path}/tasks/{task_name}/preservation/sql"
            data = {"force": force}
            result: str = requests.post(url, json=data).json()["message"]
            return result
        else:
            return "error save_type. please use it in [ yaml | sql ]"
