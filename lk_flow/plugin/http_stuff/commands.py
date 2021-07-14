#!/usr/bin/env python
# encoding: utf-8
# Created by zza on 2021/7/5 14:25
# Copyright 2021 LinkSense Technology CO,. Ltd
import asyncio
import functools
from typing import Callable, Dict, List

import pandas
import requests
import requests_async

from lk_flow.models import Task


def _async_request(method: str, url: str, **kwargs) -> requests_async.models.Response:
    """异步request"""

    async def _do_async_request() -> requests_async.models.Response:
        response = await requests_async.request(method, url, timeout=1, **kwargs)
        return response

    loop = asyncio.get_event_loop()
    result: requests_async.models.Response = loop.run_until_complete(
        _do_async_request()
    )
    return result


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

    def get_all_commands(self, use_async_requests: bool = True) -> Dict[str, Callable]:
        """
        获取所有系统命令

        Args:
            use_async_requests:
                默认使用异步requests
                使用会更改requests.request 算污染函数库了 命令模式下没问题

        Returns:

        """
        ret = dict()
        # 更换为异步请求
        if use_async_requests:
            requests.api.request = _async_request
        # 获取命令列表
        for attr_name in dir(self):
            if attr_name.startswith("_") or attr_name in self._not_commands:
                continue
            obj = getattr(self, attr_name)
            if callable(obj):
                ret[attr_name] = obj
        # 服务未启动时打印未启动提示
        if not self._url_is_listening():
            # 未启动提示装饰器
            def wrap_echo_message(func: Callable) -> Callable:
                @functools.wraps(func)
                def echo_message(*_, **__) -> str:
                    return self._server_no_run_message

                return echo_message

            # 替换
            for _func_name, _func in ret.items():
                ret[_func_name] = wrap_echo_message(_func)
        return ret

    def status(self, task_name: str = None, return_type: str = "table") -> str:
        """系统内task信息"""
        all_result: dict = requests.get(f"{self._base_path}/").json()["data"]

        if task_name:
            import re

            # 支持正则匹配task名称
            all_result = {
                _task_name: item
                for _task_name, item in all_result.items()
                if re.match(task_name, _task_name) or task_name in _task_name
            }
        if return_type == "json":
            import json

            return json.dumps(all_result, indent=4)

        elif return_type == "yaml":
            import yaml

            return yaml.dump(all_result)

        ret = []
        for task_name, item in all_result.items():
            info = {
                "name": task_name,
                "state": item["state"],
                "pid": item["pid"],
                "last_start_datetime": item["last_start_datetime"],
            }
            ret.append(info)
        if not ret:
            return "No task in system"
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
        """
        重启task

        Args:
            task_name: task名称

        Returns:
            执行结果
        """
        ret = self.stop(task_name)
        if ret != "stop":
            print(f"{task_name} is not running: {ret}")
        return self.start(task_name)

    def create(self, task_json: str = None) -> str:
        """
        创建task

        Examples:
            $ lk_flow create "{\"name\": \"t_date\", \"command\": \"date\", \"directory\": \".\"}"

        Args:
            task_json: Task json str 不输入则进入交互模式

        Returns:
            执行结果
        """
        import json

        from lk_flow.plugin.http_stuff._pydantic_input_helper import input_helper

        if task_json:
            if isinstance(task_json, dict):
                obj = Task(**task_json)
            else:
                try:
                    obj = Task(**json.loads(task_json))
                except json.decoder.JSONDecodeError as err:
                    return f"json 解析错误:{err}"
        else:  # pragma: no cover
            obj = input_helper(Task)
            print(f"Task json: {obj.json()}")
        url = f"{self._base_path}/tasks"
        resp = requests.post(url, json=obj.dict())
        result: dict = resp.json()
        return result["message"]

    def delete(self, task_name: str) -> str:
        """删除task"""
        url = f"{self._base_path}/tasks/{task_name}"
        result: str = requests.delete(url).json()["message"]
        return result

    def persist(
        self, task_name: str, save_type: str = "yaml", force: bool = False
    ) -> str:
        """
        将task持久保存 sql|yaml

        Examples:
            $ lk_flow persist t_echo --save_type yaml --force 1

        Args:
            task_name: 任务名
            save_type: 保存类型 yaml | sql
            force: 覆盖已有任务

        Returns:
            执行结果
        """
        if save_type == "yaml":
            from lk_flow.plugin.yaml_loader import YamlLoader

            url = f"{self._base_path}/tasks/{task_name}"
            res = requests.get(url).json()
            task = Task(**res["data"])
            print(f"{task_name} json: {task.json()}")
            yaml_str = YamlLoader.dump_to_file(task, ".", force=force)
            return yaml_str
        elif save_type == "sql":
            url = f"{self._base_path}/tasks/{task_name}/preservation/sql"
            data = {"force": force}
            result: str = requests.post(url, json=data).json()["message"]
            return result

        else:
            return "error save_type. please use it in [ yaml | sql ]"

    def schedule(self) -> dict:
        """查看task时间表"""
        url = f"{self._base_path}/time_trigger/process_schedule"
        result: dict = requests.get(url).json()["data"]
        return result
