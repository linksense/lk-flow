#!/usr/bin/env python
# encoding: utf-8
# Created by zza on 2021/6/16 18:22
# Copyright 2021 LinkSense Technology CO,. Ltd
import asyncio
import sys

import pytest
from pydantic import ValidationError

from lk_flow import Context, conf
from lk_flow.errors import DictionaryNotExist, RunError
from lk_flow.models.subprocess import ProcessStatus, SubProcess
from lk_flow.models.tasks import Task


class TestTask:
    @classmethod
    def setup_class(cls):
        context = Context(config=conf)

    def test_create(self):
        with pytest.raises(ValidationError):
            Task(name="no command", command=None, trigger_events="err_trigger_events")

    @pytest.mark.asyncio
    async def test_init(self):
        subprocess = SubProcess(
            Task(
                name="t_date",
                command="date",
                environment="LK_FLOW_ENABLED=2",
                stdout_logfile="/var/log/lk_flow/t_date.log",
                stderr_logfile="/var/log/lk_flow/t_date.err",
            )
        )
        await subprocess.start()
        await asyncio.sleep(1)
        assert subprocess.exit_code == 0

        with pytest.raises(RunError):
            await SubProcess(Task(name="no command", command=None)).start()
        with pytest.raises(RunError):
            await SubProcess(
                Task(name="error_command", command=f"error_command http.server")
            ).start()
        with pytest.raises(RunError):
            await SubProcess(
                Task(
                    name="error_command", command=f"/bin/usr/error_command http.server"
                )
            ).start()

        with pytest.raises(DictionaryNotExist):
            await SubProcess(
                Task(
                    name="t_not_dir",
                    command=f"python http.server",
                    stderr_logfile="./not_exist_dir/err.log",
                    stdout_logfile="./not_exist_dir/info.log",
                )
            ).start()

    @pytest.mark.asyncio
    async def test_run(self):
        t = Task(name="task", command=f"{sys.executable} -m http.server")

        p_manger = SubProcess(t)
        assert p_manger.is_running() is False
        await p_manger.start()
        assert p_manger.pid is not None
        assert p_manger.is_running() is True
        # await asyncio.sleep(2)  # wait for start
        # stop
        await p_manger.stop()
        await asyncio.sleep(2)  # wait for start
        assert p_manger.is_running() is False
        assert p_manger.pid is None

        await p_manger.restart()
        assert p_manger.pid is not None
        assert p_manger.is_running() is True
        # teardown
        await p_manger.stop()
        await asyncio.sleep(2)  # wait for stop
        assert p_manger.is_running() is False

    @pytest.mark.asyncio
    async def test_run_with_normal_exit(self):
        await SubProcess(
            Task(name="py version", command=f"{sys.executable} --version")
        ).start()
        await asyncio.sleep(2)  # wait for start

    @pytest.mark.asyncio
    async def test_run_error(self):
        p_manger = SubProcess(
            Task(
                name="error port",
                command=f"{sys.executable} -m http.server 22",
                directory=".",
            )
        )
        await p_manger.start()
        await asyncio.sleep(3)  # wait for start
        assert p_manger.state is ProcessStatus.exit_error

        p_manger = SubProcess(
            Task(
                name="error dir",
                command=f"{sys.executable} -m http.server",
                directory="./not_exit",
            )
        )
        with pytest.raises(RunError):
            await p_manger.start()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(TestTask().test_run())
