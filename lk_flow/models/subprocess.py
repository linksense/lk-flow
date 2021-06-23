#!/usr/bin/env python
# encoding: utf-8
# Created by zza on 2021/6/22 11:05
# Copyright 2021 LinkSense Technology CO,. Ltd
import asyncio
import datetime
import logging
import os
from typing import Dict, List, Optional, Tuple

from lk_flow.env import logger
from lk_flow.errors import ProcessRuntimeError, RunError
from lk_flow.models.tasks import Task


class SubProcess:
    def __init__(self, config: Task):
        self.config: Task = config
        self.pid: Optional[int] = None  # Subprocess pid; None when not running
        self.state: Optional[str] = None  # process state
        self.name: str = config.name
        self.exit_code: Optional[int] = None

        self.process: Optional[asyncio.subprocess.Process] = None
        self.last_start_datetime: Optional[datetime.datetime] = None
        self.last_stop_datetime: Optional[datetime.datetime] = None
        self._watcher_task: Optional[asyncio.Task] = None

    def _prepare_start(self) -> Tuple[str, List[str], Dict[str, str]]:
        # directory
        if self.config.directory is not None:
            cwd = self.config.directory
            try:
                if cwd is not None:
                    os.chdir(cwd)
            except OSError as why:
                raise RunError(f"couldn't chdir to {cwd}: {why}")
        # env
        env = self._make_env()
        # command
        if self.config.command is None:
            raise RunError("No command for {}".format(self.config))
        filename, *argv = self.config.command.split()
        self._check_filename_exist(filename)
        # exit_code
        self.exit_code = None
        return filename, argv, env

    def _make_env(self) -> dict:
        env = os.environ.copy()
        env["LK_FLOW_ENABLED"] = "1"
        if not self.config.environment:
            return env
        environments = self.config.environment.strip().split(";")
        environment = dict()
        for i in environments:
            if i:
                k, v = i.split("=")
                environment[k] = v
        env.update(self.config.environment)
        return env

    def _check_filename_exist(self, filename: str) -> None:
        if "/" in filename:
            try:
                os.stat(filename)
            except FileNotFoundError:
                raise RunError(f"未找到命令{self.config.command}")
        else:
            raise RunError("命令必须包含路径符'/'")

    async def _set_logger(
        self, process: asyncio.subprocess
    ) -> Tuple[asyncio.Task, asyncio.Task]:
        task_out = asyncio.create_task(
            self._handel_log_stream(logging.INFO, process.stdout)
        )
        asyncio.ensure_future(task_out, loop=asyncio.get_running_loop())
        task_err = asyncio.create_task(
            self._handel_log_stream(logging.ERROR, process.stderr)
        )
        asyncio.ensure_future(task_err, loop=asyncio.get_running_loop())
        return task_out, task_err

    async def _handel_log_stream(
        self, level: int, stream: asyncio.streams.StreamReader
    ) -> None:
        while not stream.at_eof():
            data = await stream.readline()
            line = data.decode("ascii").rstrip()
            logger.log(level, line)

    async def start(self) -> None:
        filename, argv, env = self._prepare_start()

        if self.process is not None:
            del self.process
            self.process = None

        # run
        process = await asyncio.create_subprocess_exec(
            filename,
            *argv,
            cwd=self.config.directory,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        self.process = process
        self.pid = self.process.pid

        task_out, task_err = await self._set_logger(self.process)
        self._watcher_task = asyncio.ensure_future(
            asyncio.create_task(self._process_watcher(process, task_out, task_err)),
            loop=asyncio.get_running_loop(),
        )

    async def _process_watcher(
        self,
        process: asyncio.subprocess,
        task_out: asyncio.Task,
        task_err: asyncio.Task,
    ) -> int:
        """
        watcher current process, return the process exit code.

        if current process not manager process, will not replace pid.
        """
        exit_code = await process.wait()
        if self.process == process:
            self.pid = None
            task_out.cancel()
            task_err.cancel()
            if exit_code != 0:
                raise ProcessRuntimeError(f"{self.config} exit with code {exit_code}")
        self.exit_code = exit_code
        return exit_code

    async def stop(self) -> None:
        if self.is_running():
            self.process.terminate()
            self._watcher_task.cancel()
            self.pid = None

    async def restart(self) -> None:
        await self.stop()
        await self.start()

    def is_running(self) -> bool:
        """It's sub_process is running"""  # pragma: no cover
        if self.process and self.process.returncode is None:
            return True
        return False

    def __del__(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.stop())
