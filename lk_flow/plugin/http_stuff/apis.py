#!/usr/bin/env python
# encoding: utf-8
# Created by zza on 2021/7/1 14:27
# Copyright 2021 LinkSense Technology CO,. Ltd
import traceback

import uvicorn
from fastapi import APIRouter, FastAPI, Request
from starlette.responses import JSONResponse

from lk_flow import conf, logger
from lk_flow.core import EVENT, Context, Event
from lk_flow.errors import LkFlowBaseError, TaskNotFoundError
from lk_flow.models import Task
from lk_flow.plugin.http_stuff.models import (
    CommonResponse,
    ProcessMapResponse,
    ProcessResponse,
    SaveToSqlRequest,
    ScheduleResponse,
    SubProcessModel,
    SystemInfo,
    SystemInfoResponse,
    TaskResponse,
)

api_router = APIRouter()


async def base_error_handler(request: Request, exc: LkFlowBaseError) -> JSONResponse:
    logger.error(traceback.format_exc())
    return JSONResponse(status_code=200, content={"message": exc.message, "code": -1})


@api_router.get("/processes", response_model=ProcessMapResponse)
async def get_processes() -> ProcessMapResponse:
    """获取系统内的task信息"""
    context = Context.get_instance()
    data = dict()
    for name, subprocess in context.get_all_processes():
        data[name] = SubProcessModel.from_orm(subprocess)
    return ProcessMapResponse(data=data)


@api_router.get("/system", response_model=SystemInfoResponse)
async def system_info() -> SystemInfoResponse:
    context = Context.get_instance()
    info = SystemInfo(
        system_start_time=context.system_start_time,
        mod_config=conf.mod_config,
        log_level=conf.LOG_LEVEL,
        log_save_dir=conf.log_save_dir,
        system_log_file=conf.system_log_file,
        sleep_time=conf.sleep_time,
        log_format=conf.LOG_FORMAT,
    )
    return SystemInfoResponse(data=info)


@api_router.get("/system_close", response_model=CommonResponse)
async def system_close() -> CommonResponse:
    """发送关闭系统事件 随后关闭系统"""
    context = Context.get_instance()
    context.event_bus.publish_event(Event(EVENT.EXEC_SYSTEM_CLOSE))
    return CommonResponse(message="system_close")


@api_router.get("/processes/{task_name}", response_model=ProcessResponse)
async def get_task(task_name: str) -> ProcessResponse:
    """process查询"""
    context = Context.get_instance()
    context.get_process(task_name)
    subprocess = SubProcessModel.from_orm(context.get_process(task_name))
    return ProcessResponse(data=subprocess)


@api_router.post("/processes/{task_name}/start", response_model=ProcessResponse)
async def task_start(task_name: str, task: Task = None) -> ProcessResponse:
    """启动task

    Args:
        task_name: 任务名
        task: 如果任务不存在 则载入的任务配置

    Returns:
        ProcessResponse
    """
    context = Context.get_instance()
    if task:
        task.name = task_name  # 保持名称统一
        try:
            context.get_process(task_name=task.name)
        except TaskNotFoundError:
            context.add_task(task)
    context.start_task(task_name)
    subprocess = SubProcessModel.from_orm(context.get_process(task_name))
    return ProcessResponse(data=subprocess)


@api_router.post("/processes/{task_name}/stop", response_model=ProcessResponse)
async def task_stop(task_name: str) -> ProcessResponse:
    """手动关闭task"""
    context = Context.get_instance()
    context.stop_task(task_name=task_name)
    subprocess = SubProcessModel.from_orm(context.get_process(task_name))
    return ProcessResponse(data=subprocess)


@api_router.post("/tasks", response_model=ProcessResponse)
async def task_create(task: Task) -> ProcessResponse:
    context = Context.get_instance()
    item = context.add_task(task)
    return ProcessResponse(data=SubProcessModel.from_orm(item))


@api_router.get("/tasks/{task_name}", response_model=TaskResponse)
async def task_get(task_name: str) -> TaskResponse:
    context = Context.get_instance()
    process = context.get_process(task_name)
    return TaskResponse(data=process.config)


@api_router.delete("/tasks/{task_name}", response_model=CommonResponse)
async def task_delete(task_name: str) -> CommonResponse:
    context = Context.get_instance()
    context.stop_task(task_name)
    context.delete_task(task_name)
    return CommonResponse()


@api_router.post("/tasks/{task_name}/preservation/sql", response_model=CommonResponse)
async def task_save_to_sql(
    task_name: str, save_to_sql_request: SaveToSqlRequest = SaveToSqlRequest()
) -> CommonResponse:
    """将task保存至yaml"""
    from lk_flow.plugin.sql_orm import SQLOrmMod

    context = Context.get_instance()
    task = context.get_process(task_name).config
    mod: SQLOrmMod = context.get_mod(SQLOrmMod.__name__)
    mod.create_task_orm(task=task, force=save_to_sql_request.force)
    return CommonResponse(message="ok")


@api_router.get("/time_trigger/process_schedule", response_model=ScheduleResponse)
async def time_trigger_get() -> ScheduleResponse:
    """
    获取所有计划执行任务

    Returns:
        '{"message": "ok", "code": 0, "data": {"task_name": "2021-07-14T14:59:00.123456"}}'

    """
    from lk_flow.plugin.time_trigger import TimeTrigger

    context = Context.get_instance()
    mod: TimeTrigger = context.get_mod("TimeTrigger")
    resp = ScheduleResponse(data=mod.PROCESS_SCHEDULE)
    return resp


async def start_server(
    host: str = "0.0.0.0",
    port: int = 9002,
    log_level: str = "info",
    api_path: str = "/lk_flow/api/v1",
) -> None:
    """启动服务"""
    app = FastAPI()
    app.include_router(api_router, prefix=api_path)
    app.add_exception_handler(LkFlowBaseError, base_error_handler)
    config = uvicorn.Config(
        app, host=host, port=port, log_level=log_level.lower(), reload=False
    )
    server = uvicorn.Server(config)
    await server.serve()
