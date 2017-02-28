import base64
import collections.abc
import decimal


def unpack_scalar(dict):
    from . import types
    if not (isinstance(value, collection.abc.mapping) and len(value) == 1):
        raise TypeError(value)
    sname, sdict = list(value.items())[0]
    if not isinstance(sname, str):
        raise TypeError(sname)
    if not (isinstance(sdict, dict) and len(sdict) == 1):
        raise TypeError(sdict)
    stype, svalue = list(sdict.values())[0]
    stype = types.AttrType.resolve(stype)
    if not isinstance(svalue, str):
        raise TypeError(svalue)
    if stype is types.AttrType.N:
        svalue = decimal.Decimal(svalue)
    elif stype is types.AttrType.B:
        svalue = base64.b64decode(svalue)
    elif stype in (types.AttrType.BOOL, types.AttrType.NULL):
        if svalue not in ('true', 'false'):
            raise ValueError(svalue)
        svalue = True if svalue == 'true' else False
    elif stype is not types.AttrType.S:
        raise TypeError(stype)
    return stype, sname, svalue


def pack_scalar(attr_type, attr_name, attr_value):
    from . import types
    if not isinstance(attr_name, str):
        raise TypeError(attr_name)
    if attr_type is types.AttrType.S:
        if not isinstance(attr_value, str):
            raise TypeError(attr_value)
    elif attr_type is types.AttrType.B:
        if not isinstance(attr_value, bytes):
            raise TypeError(attr_value)
        attr_value = base64.b64encode(attr_value)
    elif attr_type is types.AttrType.N:
        if not isinstance(attr_value, (float, decimal.Decimal)):
            raise TypeError(attr_value)
        if isinstance(attr_value, float):
            attr_value =  decimal.Decimal(str(attr_value))
    elif attr_type in (types.AttrType.BOOL, types.AttrType.NULL):
        if not isinstance(attr_value, bool):
            raise TypeError(attr_value)
        attr_value = 'true' if attr_value else 'false'
    else:
        raise ValueError(attr_type)
    return {
        attr_name: {attr_type.value: attr_value}
    }
