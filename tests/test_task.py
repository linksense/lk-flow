#!/usr/bin/env python
# encoding: utf-8
# Created by zza on 2021/6/16 18:22
# Copyright 2021 LinkSense Technology CO,. Ltd
import asyncio
import sys

import pytest

from lk_flow.errors import RunError
from lk_flow.models.subprocess import Subprocess
from lk_flow.models.tasks import Task
from tests.test_lk_flow import TestLkFlow


class TestTask(TestLkFlow):
    @pytest.mark.asyncio
    async def test_init(self):
        with pytest.raises(RunError):
            await Subprocess(Task(name="no command", command=None)).start()
        with pytest.raises(RunError):
            await Subprocess(
                Task(name="error_command", command=f"error_command http.server")
            ).start()
        with pytest.raises(RunError):
            await Subprocess(
                Task(
                    name="error_command", command=f"/bin/usr/error_command http.server"
                )
            ).start()

    @pytest.mark.asyncio
    async def test_run(self):
        t = Task(name="task", command=f"{sys.executable} -m http.server")

        p_manger = Subprocess(t)
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
        await Subprocess(
            Task(name="py version", command=f"{sys.executable} --version")
        ).start()
        await asyncio.sleep(2)  # wait for start

    @pytest.mark.asyncio
    async def test_run_error(self):
        p_manger = Subprocess(
            Task(
                name="error port",
                command=f"{sys.executable} -m http.server 22",
                directory=".",
            )
        )
        await p_manger.start()
        await asyncio.sleep(1)  # wait for start
        assert p_manger.pid is None

        p_manger = Subprocess(
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
