#!/usr/bin/env python
# encoding: utf-8
# Created by zza on 2021/7/6 14:22
# Copyright 2021 LinkSense Technology CO,. Ltd
from typing import Any, Type

import pydantic
from pydantic import BaseModel
from pydantic.validators import find_validators

from lk_flow.models import Task


def _deal_field(field: pydantic.fields.ModelField) -> Any:
    """处理每一个字段"""
    while True:
        default = f"[{field.default}]" if field.default is not None else ""
        value = input(f"[{field.type_.__name__}] {field.name}     {default}:  ")
        if field.default is not None and (isinstance(value, str) and not value):
            value = field.default
        try:
            for validator in find_validators(field.type_, field.model_config):
                value = validator(value)
            return value
        except pydantic.errors.PydanticTypeError as err:
            print(f"Error: {value} {err.msg_template}")


def input_helper(class_type: Type[BaseModel] = Task) -> Type[Type[BaseModel]]:
    """将pydantic.Model通过交互方式创建"""
    values = {}
    for name, field in class_type.__fields__.items():
        value = _deal_field(field)
        values[name] = value
    return class_type(**values)


if __name__ == "__main__":
    print(input_helper())
