#!/usr/bin/env python
# encoding: utf-8
# Created by zza on 2021/6/29 17:13
# Copyright 2021 LinkSense Technology CO,. Ltd
import datetime

from lk_flow.config import conf
from lk_flow.core import EVENT, Context, Event
from lk_flow.models import Task
from lk_flow.plugin.time_trigger import TimeTrigger


class TestTimeTrigger:
    def setup_method(self):
        del Context._env
        Context._env = None

    def test_work(self):
        context = Context(conf)
        task = Task(
            name="t_time_trigger_task",
            command="/usr/bin/date",
            cron_expression="0/1 * * * * * ",
        )
        task_2 = Task(name="t_time_trigger_task_2", cron_expression="0/1 0 0 * * * ")
        task_3 = Task(
            name="t_time_trigger_task_3",
            command="watch date",
            cron_expression="0/1 * * * * * ",
        )
        context.add_task(task)

        TimeTrigger.setup_mod({})
        # trigger
        context.add_task(task_2)
        context.add_task(task_3)

        assert task.name in TimeTrigger.PROCESS_SCHEDULE

        event = Event(
            EVENT.HEARTBEAT, now=datetime.datetime.now() + datetime.timedelta(seconds=2)
        )

        TimeTrigger._work(event)
        TimeTrigger._work(
            Event(
                EVENT.HEARTBEAT,
                now=datetime.datetime.now() + datetime.timedelta(seconds=2),
            )
        )

        context.delete_task(task_2.name)
