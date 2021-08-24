#!/usr/bin/env python
# encoding: utf-8
# Created by zza on 2021/6/25 17:05
# Copyright 2021 LinkSense Technology CO,. Ltd
"""
工具包
原则上只依赖 env.py config.py
core与model需要的工具包 在内部创建
"""
import functools
import inspect
import logging
import os
import time
from typing import Any, Callable

from lk_flow.env import logger


def time_consuming_log(log_level: logging.INFO) -> Callable:
    """耗时日志装饰器"""

    def middle_wrapper(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            bound_values = inspect.signature(func).bind(*args, **kwargs)

            start_log = "[Func {}]: {}(**{})".format(
                func.__name__, func.__name__, dict(bound_values.arguments)
            )
            logger.log(log_level, start_log)
            start_time = time.time()

            ret = func(*args, **kwargs)

            used_time = round(time.time() - start_time, 6)
            end_log = "[Func {}](finish in {}s) return: {}".format(
                func.__name__, used_time, ret
            )
            logger.log(log_level, end_log)
            return ret

        return wrapper

    return middle_wrapper


def add_systemd(work_dir: str = None) -> None:
    """add lk_flow daemon to system service"""
    import sys

    if not work_dir:
        work_dir = os.getcwd()
    python_exec = sys.executable
    service_file = os.path.join(os.path.dirname(__file__), "etc", "lk_flow.service")
    template = open(service_file, "r", encoding="utf8").read()

    service = template.format(python_exec=python_exec, work_dir=work_dir)
    with open("/usr/lib/systemd/system/lk_flow.service", "w", encoding="utf8") as f:
        f.write(service)
    os.popen("/usr/bin/systemctl start lk_flow.service")  # noqa: S605
    return


def ln_command() -> None:
    """create soft link to /usr/bin/lk_flow"""
    import sys

    python_exec = sys.executable
    exec_file = os.path.join(os.path.dirname(python_exec), "lk_flow")
    if not os.path.exists("/usr/bin/lk_flow"):
        os.symlink(exec_file, "/usr/bin/lk_flow")


if __name__ == "__main__":
    add_systemd()
