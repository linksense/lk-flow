#!/usr/bin/env python
# encoding: utf-8
# Created by zza on 2021/7/1 17:34
# Copyright 2021 LinkSense Technology CO,. Ltd
from collections import defaultdict
from typing import Any, Dict, List

from lk_flow.core import EVENT, Context, Event, ModAbstraction
from lk_flow.models import Task


class HookTrigger(ModAbstraction):
    # {event_name : hook_task_name: [trigger_task_name2] }
    hook_listeners: Dict[EVENT, Dict[str, List[str]]] = defaultdict(
        lambda: defaultdict(list)
    )

    @classmethod
    def setup_mod(cls, mod_config: Dict[str, Any]) -> None:
        context: Context = Context.get_instance()
        # add event hook
        context.event_bus.add_listener(EVENT.SYSTEM_SETUP, cls.process_set_add)

        context.event_bus.add_listener(EVENT.TASK_ADD, cls.task_hook_add)
        context.event_bus.add_listener(EVENT.TASK_DELETE, cls.task_hook_remove)
        # listener Task event
        context.event_bus.add_listener(EVENT.TASK_PRE_START, cls.task_hook_trigger)
        context.event_bus.add_listener(EVENT.TASK_RUNNING, cls.task_hook_trigger)
        context.event_bus.add_listener(EVENT.TASK_STOP, cls.task_hook_trigger)
        context.event_bus.add_listener(EVENT.TASK_FINISH, cls.task_hook_trigger)
        context.event_bus.add_listener(EVENT.TASK_RUNNING_ERROR, cls.task_hook_trigger)
        context.event_bus.add_listener(EVENT.TASK_FINISH_ERROR, cls.task_hook_trigger)

    @classmethod
    def teardown_mod(cls) -> None:
        pass

    @classmethod
    def add_task_hook(cls, trigger_events: str, trigger_task_name: str) -> True:
        """Task.trigger_events解析

        Args:[动画表情]
            trigger_events: eg.'Event_Name__hook_task_name Event_Name2__hook_task_name2'
            trigger_task_name: 事件被触发时，启动的task名
        """
        if not trigger_events:
            return
        for trigger_event in trigger_events.split():
            event_name, hook_task_name = trigger_event.split("__")
            event = EVENT(event_name.lower())
            cls.hook_listeners[event][hook_task_name].append(trigger_task_name)

    @classmethod
    def process_set_add(cls, _: Event) -> None:
        """
        在SYSTEM_SETUP事件时读取context
        给所有process增加hook
        """

        context = Context.get_instance()
        for task_name, process in context.get_all_processes():
            if process.config.trigger_events:
                cls.add_task_hook(process.config.trigger_events, process.config.name)

    @classmethod
    def task_hook_add(cls, event: Event) -> None:
        """
        trigger_task加入系统
        装载trigger_task.trigger_events配置
        """
        task: Task = event.task
        cls.add_task_hook(task.trigger_events, task.name)

    @classmethod
    def task_hook_remove(cls, event: Event) -> None:
        """
        trigger_task被移除系统
        移除对应的钩子
        """
        task: Task = event.task
        if not task.trigger_events:
            return
        for trigger_event in task.trigger_events.split():
            event_name, hook_task_name = trigger_event.split("__")
            event = EVENT(event_name.lower())
            if task.name in cls.hook_listeners[event][hook_task_name]:
                cls.hook_listeners[event][hook_task_name].remove(task.name)

    @classmethod
    def task_hook_trigger(cls, event: Event) -> None:
        """事件来后触发对应的监听任务"""
        context = Context.get_instance()
        for trigger_task_name in cls.hook_listeners[event.event_type][event.task_name]:
            context.start_task(trigger_task_name)
