#!/usr/bin/env python
# encoding: utf-8
# Created by zza on 2021/6/30 15:12
# Copyright 2021 LinkSense Technology CO,. Ltd
import asyncio
from typing import Any, Dict

from lk_flow.core import ModAbstraction


class HttpControlServer(ModAbstraction):
    """通过http接口控制server"""

    uv_task: asyncio.Task

    @classmethod
    def setup_mod(cls, mod_config: Dict[str, Any]) -> None:
        from lk_flow.plugin.http_stuff.apis import start_server

        # get config
        host = mod_config.get("host", "0.0.0.0")
        port = mod_config.get("port", 8000)
        log_level = mod_config.get("log_level", "info")
        # start FastAPI app
        loop = asyncio.get_event_loop()
        uv_task = start_server(host, port, log_level)
        cls.uv_task = asyncio.create_task(uv_task)
        asyncio.ensure_future(cls.uv_task, loop=loop)

    @classmethod
    def teardown_mod(cls) -> None:
        cls.uv_task.cancel()
