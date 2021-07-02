#!/usr/bin/env python
# encoding: utf-8
# Created by zza on 2021/7/1 14:27
# Copyright 2021 LinkSense Technology CO,. Ltd
import uvicorn
from fastapi import APIRouter, FastAPI

from lk_flow.core import EVENT, Context, Event
from lk_flow.models import Task
from lk_flow.plugin.http_stuff.models import (
    CommonResponse,
    ProcessMapResponse,
    ProcessResponse,
    SubProcessModel,
)

api_router = APIRouter()


@api_router.get("/", response_model=ProcessMapResponse)
async def system_info() -> ProcessMapResponse:
    """获取系统内的task信息"""
    context = Context.get_instance()
    data = dict()
    for name, subprocess in context.get_all_processes():
        data[name] = SubProcessModel.from_orm(subprocess)
    return ProcessMapResponse(data=data)


@api_router.get("/system_close", response_model=CommonResponse)
async def system_close() -> CommonResponse:
    """发送关闭系统事件 随后关闭系统"""
    context = Context.get_instance()
    context.event_bus.publish_event(Event(EVENT.SYSTEM_CLOSE))
    return CommonResponse(message="system_close")


@api_router.get("/process/{task_name}/start", response_model=ProcessResponse)
async def task_start(task_name: str) -> ProcessResponse:
    """启动task"""
    context = Context.get_instance()
    context.start_task(task_name)
    subprocess = SubProcessModel.from_orm(context.get_process(task_name))
    return ProcessResponse(data=subprocess)


@api_router.get("/process/{task_name}/stop", response_model=ProcessResponse)
async def task_stop(task_name: str) -> ProcessResponse:
    """手动关闭task"""
    context = Context.get_instance()
    context.stop_task(task_name=task_name)
    subprocess = SubProcessModel.from_orm(context.get_process(task_name))
    return ProcessResponse(data=subprocess)


@api_router.post("/process", response_model=ProcessResponse)
async def task_create(task: Task) -> ProcessResponse:
    context = Context.get_instance()
    item = context.add_task(task)
    if not item:
        return ProcessResponse(code=-1, message=f"{task.name} is already exists")
    return ProcessResponse(data=SubProcessModel.from_orm(item))


@api_router.delete("/process/{task_name}", response_model=CommonResponse)
async def task_delete(task_name: str) -> CommonResponse:
    context = Context.get_instance()
    context.stop_task(task_name)
    context.delete_task(task_name)
    return CommonResponse()


async def start_server(
    host: str = "0.0.0.0",
    port: int = 9002,
    log_level: str = "info",
    api_path: str = "/lk_flow/api/v1",
) -> None:
    """启动服务"""
    app = FastAPI()
    app.include_router(api_router, prefix=api_path)
    config = uvicorn.Config(
        app, host=host, port=port, log_level=log_level, reload=False
    )
    server = uvicorn.Server(config)
    await server.serve()
