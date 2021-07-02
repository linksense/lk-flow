#!/usr/bin/env python
# encoding: utf-8
# Created by zza on 2021/6/24 10:05
# Copyright 2021 LinkSense Technology CO,. Ltd
""" 总启动流程文件 """
import asyncio
import datetime
import traceback

from lk_flow.config import conf
from lk_flow.core import Context
from lk_flow.core.event import EVENT, Event
from lk_flow.core.mod import loading_plugin, setup_mod, teardown_mod
from lk_flow.env import logger


async def start_server() -> None:
    """
    启动系统

    1.初始化Context
    2.载入mod
    3.setup_mod
    4.发送SYSTEM_SETUP事件
    5.开始server 不停发HEARTBEAT
    6.接受到SYSTEM_CLOSE事件或异常结束
    7.发送SYSTEM_TEARDOWN事件
    8.teardown_mod
    """
    context = Context(config=conf)
    loading_plugin(context.config.mod_dir)
    setup_mod(context)
    # setup server
    context.event_bus.publish_event(Event(EVENT.SYSTEM_SETUP))
    try:
        while context.loop_enable:
            context.event_bus.publish_event(
                Event(EVENT.HEARTBEAT, now=datetime.datetime.now())
            )
            await asyncio.sleep(context.sleep_time)
    except Exception as err:
        logger.error(f"系统级错误 {err}")
        logger.error(traceback.format_exc())

    context.event_bus.publish_event(Event(EVENT.SYSTEM_TEARDOWN))
    teardown_mod(context)
