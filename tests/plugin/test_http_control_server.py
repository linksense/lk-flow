#!/usr/bin/env python
# encoding: utf-8
# Created by zza on 2021/7/8 17:57
# Copyright 2021 LinkSense Technology CO,. Ltd
import asyncio
import json
import os
from typing import Callable, Dict

import pytest

from lk_flow import Config, ProcessStatus, Task, start_server
from lk_flow.__main__ import init
from lk_flow.plugin.http_control_server import HttpControlServer
from lk_flow.plugin.http_stuff._pydantic_input_helper import input_helper
from lk_flow.plugin.http_stuff.commands import ControlCommands
from tests.test_lk_flow import TestLkFlow


class TestHttpControlServer(TestLkFlow):
    sleep_time = 5
    _future = None

    @classmethod
    def setup_class(cls):
        super(TestHttpControlServer, cls).setup_class()
        if os.path.exists("lk_flow.db"):
            os.remove("lk_flow.db")

    async def _get_commands(self):
        init()
        conf = Config()
        conf.sleep_time = self.sleep_time
        conf.mod_config["HttpControlServer"] = {"enable": True}
        # start server
        start_server_task = asyncio.create_task(start_server())
        self._future = asyncio.ensure_future(
            start_server_task, loop=asyncio.get_running_loop()
        )
        await asyncio.sleep(1)
        # get_commands
        commands: Dict[str, Callable] = HttpControlServer.get_commands({})
        return commands

    @pytest.mark.asyncio
    async def test_no_server(self):
        commands: Dict[str, Callable] = HttpControlServer.get_commands({})
        command_status = commands["status"]
        assert ControlCommands._server_no_run_message == command_status()

    @pytest.mark.asyncio
    async def test_all_commands(self):
        commands = await self._get_commands()

        # status
        command_status = commands["status"]
        for _ in range(3):
            if "No task" not in command_status():
                break
            await asyncio.sleep(1)
            # get_commands
            commands: Dict[str, Callable] = HttpControlServer.get_commands({})
            # status
            command_status = commands["status"]

        res = command_status("t_", return_type="json")
        assert "t_echo_1" in res
        res = command_status("t_", return_type="yaml")
        assert "t_echo_1" in res

        # schedule
        command_schedule = commands["schedule"]
        res = command_schedule()
        assert "t_echo_1" in res

        # delete yaml task
        command_delete = commands["delete"]
        command_delete("t_echo_1")
        command_delete("t_http_server")
        assert "No task" in command_status()
        # create
        task_name = "t_date"
        command_create = commands["create"]
        task_dict = {"name": task_name, "command": "watch date", "directory": "."}
        res = command_create(json.dumps(task_dict))
        assert res == "ok"
        res = command_create(task_dict)
        assert "already used" in res
        res = command_create('{"name":error}')
        assert "json 解析错误" in res

        # start
        command_start = commands["start"]
        command_start(task_name)
        res = command_status()
        assert "t_date" in res

        # stop
        command_stop = commands["stop"]
        res = command_stop(task_name)
        assert res == ProcessStatus.stopped

        # restart
        command_restart = commands["restart"]
        res = command_restart(task_name)
        assert res is not None

        # delete
        res = command_delete(task_name)
        assert res == "ok"

        self._test_persist(commands)
        # sys_close
        command_sys_close = commands["sys_close"]
        res = command_sys_close()
        assert res == "system_close"
        await asyncio.sleep(3)  # wait for teardown_mod

    def _test_persist(self, commands):
        # create
        task_name = "t_date_1"
        command_create = commands["create"]
        res = command_create(
            task_json='{{"name": "{}", "command": "watch date", "directory": "."}}'.format(
                task_name
            )
        )
        assert res == "ok"
        # persist yaml
        if os.path.exists(f"{task_name}.yaml"):
            os.remove(f"{task_name}.yaml")

        command_persist = commands["persist"]
        res = command_persist(task_name, force=True)
        assert task_name in res
        assert os.path.exists(f"{task_name}.yaml")
        os.remove(f"{task_name}.yaml")

        # persist sql
        command_persist = commands["persist"]
        command_persist(task_name, save_type="sql")
        command_persist = commands["persist"]
        command_persist("t_date_not_exist", save_type="sql")

        command_persist = commands["persist"]
        res = command_persist(task_name, save_type="error_type")
        assert "error" in res

    def test_pydantic_input_helper(self, monkeypatch):

        return_map = {
            "[str] name     :  ": "t_task",
            "[str] command     :  ": "t_task",
            "[str] directory     :  ": ".",
            "[bool] auto_restart     [False]:  ": "asd",
            "[int] restart_retries     [0]:  ": "",
            "[str] environment     :  ": "",
            "[str] stdout_logfile     :  ": "",
            "[str] stderr_logfile     :  ": "",
            "[str] cron_expression     :  ": "",
            "[str] trigger_events     :  ": "",
            "[str] extra_json     [{}]:  ": "",
        }

        def fake_input(input_text):
            msg = return_map[input_text]
            if input_text == "[bool] auto_restart     [False]:  ":  # for Error hint
                return_map["[bool] auto_restart     [False]:  "] = "True"
            return msg

        monkeypatch.setattr("builtins.input", fake_input)
        ret: Task = input_helper()
        assert ret.name == "t_task"
