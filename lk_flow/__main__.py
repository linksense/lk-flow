#!/usr/bin/python3
# encoding: utf-8
""" lk_flow 's entry_points"""
import fire


def entry_point() -> None:  # pragma: no cover
    """
    默认函数 触发fire包
    https://github.com/google/python-fire
    """
    fire.Fire()


def ipython() -> None:  # pragma: no cover
    """打开ipython命令"""
    from IPython import embed

    embed()


def version() -> None:
    """显示当前版本"""
    import lk_flow

    print(lk_flow.__version__)


if __name__ == "__main__":
    entry_point()
