#!/usr/bin/env python
# encoding: utf-8
# Created by zza on 2021/6/16 17:47
# Copyright 2021 LinkSense Technology CO,. Ltd
import asyncio

import aioschedule


async def init_time_trigger() -> None:
    aioschedule.every().day.at("20:00").do(print)


async def start_server() -> None:
    with True:
        await init_time_trigger()
        await asyncio.sleep(60)
