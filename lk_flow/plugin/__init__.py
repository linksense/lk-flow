#!/usr/bin/env python
# encoding: utf-8
# Created by zza on 2021/6/25 18:16
# Copyright 2021 LinkSense Technology CO,. Ltd
from lk_flow.env import logger
from lk_flow.plugin.trigger import TimeTrigger


def loading_sys_plugin():
    plugins = [TimeTrigger]
    for plugin in plugins:
        logger.info(f"Loading plugin {plugin.__name__}")
