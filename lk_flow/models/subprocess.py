#!/usr/bin/env python
# encoding: utf-8
# Created by zza on 2021/6/22 11:05
# Copyright 2021 LinkSense Technology CO,. Ltd
import asyncio
import datetime
import logging
import os
from enum import Enum
from typing import Dict, List, Optional, Tuple

from lk_flow.config import conf
from lk_flow.env import logger
from lk_flow.errors import DictionaryNotExist, RunError
from lk_flow.models.tasks import Task

# For ensures that the python output is sent straight to get
os.environ["PYTHONUNBUFFERED"] = "1"


class ProcessStatus(str, Enum):
    sleeping = "sleeping"
    exit_normal = "exit_normal"
    exit_error = "exit_error"
    stopped = "stopped"
    running = "running"


class SubProcess:
    def __init__(self, config: Task):
        self.config: Task = config
        self.pid: Optional[int] = None  # Subprocess pid; None when not running
        self.state: Optional[str] = ProcessStatus.sleeping  # process state
        self.name: str = config.name
        self.exit_code: Optional[int] = None

        self.process: Optional[asyncio.subprocess.Process] = None
        self.last_start_datetime: Optional[datetime.datetime] = None
        self.last_stop_datetime: Optional[datetime.datetime] = None
        self._watcher_task: Optional[asyncio.Task] = None

        self.stdout_logfile = self._format_log_file(
            self.config.stdout_logfile, "out.log"
        )
        self.stderr_logfile = self._format_log_file(
            self.config.stderr_logfile, "err.log"
        )

    def _format_log_file(self, source_path: str, suffix: str) -> str:
        """
        非绝对路径放到配置路径文件夹去
        且自动创建文件夹
        """
        if source_path is None:  # use system default path
            source_path = os.path.join(
                conf.log_save_dir, f"{self.name}", f"{self.name}_{suffix}"
            )
            os.makedirs(os.path.dirname(source_path), exist_ok=True)
            return source_path

        if not os.path.isabs(source_path):
            # relative address . add to system log dir prefix
            source_path = os.path.abspath(os.path.join(conf.log_save_dir, source_path))
        if not os.path.exists(os.path.dirname(source_path)):
            # check path exists
            raise DictionaryNotExist(f"{os.path.dirname(source_path)} not exists")
        return source_path

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
        if " " in self.config.command:
            filename, *argv = self.config.command.split()
        else:
            filename = self.config.command
            argv = []
        filename = self._check_filename_exist(filename)
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
        env.update(environment)
        return env

    def _check_filename_exist(self, filename: str) -> str:
        if "/" in filename:
            try:
                os.stat(filename)
                return filename
            except FileNotFoundError:
                raise RunError(f"未找到命令{self.config.command}")
        else:
            for _dir in ["/bin", "/usr/bin", "/usr/local/bin"]:
                _path = os.path.join(_dir, filename)
                try:
                    os.stat(_path)
                    return _path
                except FileNotFoundError:
                    pass
            raise RunError("命令必须包含路径符'/'")

    async def _set_logger(
        self, process: asyncio.subprocess
    ) -> Tuple[asyncio.Task, asyncio.Task]:
        task_out = asyncio.create_task(
            self._handle_log_stream(logging.INFO, process.stdout, self.stdout_logfile)
        )
        asyncio.ensure_future(task_out, loop=asyncio.get_running_loop())
        task_err = asyncio.create_task(
            self._handle_log_stream(logging.ERROR, process.stderr, self.stderr_logfile)
        )
        asyncio.ensure_future(task_err, loop=asyncio.get_running_loop())
        return task_out, task_err

    async def _handle_log_stream(
        self,
        level: int,
        stream: asyncio.streams.StreamReader,
        log_file_path: str,
    ) -> None:
        f = open(log_file_path, 'ab')
        prefix = f"\n[{self.name}] ".encode()
        while not stream.at_eof():
            data = await stream.readline()
            f.write(data)
            f.flush()
            logger.info(prefix + data)
        f.close()

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
        asyncio_task = asyncio.create_task(
            self._process_watcher(process, task_out, task_err)
        )
        self._watcher_task = asyncio.ensure_future(
            asyncio_task,
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
        self.state = ProcessStatus.running
        self.last_start_datetime = datetime.datetime.now()
        self.exit_code = await process.wait()
        self.last_stop_datetime = datetime.datetime.now()
        if self.process == process:
            self.pid = None
            # log task will stop by stream.at_eof
            from lk_flow.core import EVENT, Context, Event

            event_bus = Context.get_instance().event_bus
            if self.exit_code == 0:
                # normal exit
                self.state = ProcessStatus.exit_normal
                event_bus.publish_event(Event(EVENT.TASK_FINISH, task_name=self.name))
            else:  # raise error
                self.state = ProcessStatus.exit_error
                event_bus.publish_event(
                    Event(EVENT.TASK_RUNNING_ERROR, task_name=self.name)
                )
        return self.exit_code

    async def stop(self) -> None:
        if self.is_running():
            self.process.terminate()
            self.last_stop_datetime = datetime.datetime.now()
            self._watcher_task.cancel()
            if os.getpgid(self.pid) == self.pid:
                os.killpg(self.pid, 9)  # kill as group
            else:
                os.kill(self.pid, 9)  # kill self
            self.pid = None
            self.state = ProcessStatus.stopped

    async def restart(self) -> None:
        await self.stop()
        await self.start()

    def is_running(self) -> bool:
        """It's sub_process is running"""  # pragma: no cover
        if self.process and self.process.returncode is None:
            return True
        return False

    def __del__(self):
        asyncio.run(self.stop())
