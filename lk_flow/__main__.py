#!/usr/bin/python3
# encoding: utf-8
""" lk_flow 's entry_points"""
import fire

from lk_flow.core import loading_plugin


def ipython() -> None:  # pragma: no cover
    """打开ipython命令"""
    from IPython import embed

    embed()


def version() -> str:
    """显示当前版本"""
    import lk_flow

    return lk_flow.__version__


def run() -> None:  # pragma: no cover
    """启动守护进程"""
    import asyncio

    from lk_flow.main import start_server

    asyncio.get_event_loop().run_until_complete(start_server())


def init() -> None:
    """初始化系统"""
    from lk_flow.config import conf
    from lk_flow.core import Context, mod_init

    context = Context(config=conf)
    loading_plugin(context.config.mod_dir)
    mod_init(context)


def entry_point() -> None:  # pragma: no cover
    """
    默认函数 触发fire包
    https://github.com/google/python-fire
    """

    from lk_flow.core.mod import loading_plugin_command

    command_map = {
        "version": version,
        "run": run,
        "init": init,
    }
    command_map.update(loading_plugin_command())
    fire.core.Display = lambda lines, out: print(*lines, file=out)
    fire.Fire(command_map)


if __name__ == "__main__":
    entry_point()
