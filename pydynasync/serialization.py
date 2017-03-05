import base64
import collections.abc
import datetime
import decimal
import json


def null_converter(value):
    if value is not True:
        raise TypeError('bool True is only valid value for NULL type')
    return value


def make_scalar_converter(cls, tests, *, force=False):
    if type(cls) is not type:
        raise TypeError(cls)

    if not tests:
        def convert(value):
            if not isinstance(value, cls):
                raise TypeError("expected type '{}' but got type '{}'".format(
                                cls.__name__, type(value).__name__))
            return value

        return convert

    for k, v in tests.items():
        if type(k) is not type:
            raise TypeError(k)
        if not callable(v):
            raise TypeError(v)

    def convert(value):
        if force or not isinstance(value, cls):
            type_ = type(value)
            try:
                func = tests[type_]
            except KeyError:
                valid_types = ', '.join(t.__name__ for t in tests)
                raise TypeError(
                    f"expected type [{valid_types}] but found type "
                    f"[{type_.__name__}] for value {value}"
                )
            else:
                value = func(value)
        return value

    return convert


def make_set_converter(scalar_converter):
    return lambda value: list(map(scalar_converter, value))


def make_serialization_helpers(attr_type, convert_to, convert_from):

    descriptor = attr_type.value

    def serialize(name, value):
        return {name: {descriptor: convert_to(value)}}

    def deserialize(name, value):
        try:
            attr_value = value[name]
        except KeyError:
            raise ValueError("no value found for name '{}' in DynamoDB "
                             "dict: {}".format(name, value))
        try:
            result = attr_value[descriptor]
        except KeyError:
            raise ValueError("no value found for descriptor '{}' in DynamoDB "
                             "dict: {}".format(descriptor, attr_value))
        return convert_from(result)

    return serialize, deserialize


def pack_set(attr_type, attr_name, attr_value):
    from . import types
    if not isinstance(attr_name, str):
        raise TypeError(attr_name)
    if not attr_type.is_set_type():
        raise ValueError(attr_type)

    return {
        attr_name: {
            attr_type.value: attr_value,
        }
    }



"""
class JSONEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            ...
        return json.JSONEncoder.default(self, obj)


def to_json(obj):
    return json.dumps(obj, separators=(',', ':'))


def from_json(text):
    return json.loads(text, parse_float=decimal.Decimal)
"""
