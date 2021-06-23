#!/usr/bin/python3
# encoding: utf-8
""" lk_flow 's entry_points"""
import fire


def entry_point() -> None:  # pragma: no cover
    """
    默认函数 触发fire包
    https://github.com/google/python-fire
    """
    fire.core.Display = lambda lines, out: print(*lines, file=out)
    fire.Fire()


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
    """初始化数据库"""
    from lk_flow.env import sql_db
    from lk_flow.models.tasks import TaskOrm
    print(TaskOrm)
    sql_db.create_all()


if __name__ == "__main__":
    entry_point()
