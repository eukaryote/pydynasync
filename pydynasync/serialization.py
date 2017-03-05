import base64
import collections.abc
import decimal


class Converter:

    def __init__(self, cls, funcs, *, force=False):
        self._cls = cls
        self._funcs = funcs
        self._force = force

    def __call__(self, value, *, force=None):
        type_ = type(value)
        force = force or (force is None and self._force)
        if force or not isinstance(value, self._cls):
            func = self._funcs.get(type_)
            # print('type_:', type_, func, self._funcs)
            if func is None:
                print(
                    f"{self} found no converter func in {self._funcs} for "
                    f"value {value} of type {type_}"
                )
                # print('self._funcs:', self._funcs)
                valid_types = ', '.join(t.__name__ for t in self._funcs)
                raise TypeError(
                    f"expected type [{valid_types}] but found type "
                    f"[{type_.__name__}] for value {value}"
                    f" [type={type(value)}]"
                    f" [no converter found in {self._funcs}]"
                )
            value = func(value)
        return value

    def __repr__(self):
        return '<Converter([{}] -> {}, force={})>'.format(
            ','.join(c.__name__ for c in self._funcs.keys()),
            self._cls.__name__,
            self._force
        )

    __str__ = __repr__


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
        elif not attr_value:
            raise ValueError(attr_value)
        attr_value = base64.b64encode(attr_value)
    elif attr_type is types.AttrType.N:
        if not isinstance(attr_value, (int, float, decimal.Decimal)):
            raise TypeError(attr_value)
        if not isinstance(attr_value, decimal.Decimal):
            attr_value =  decimal.Decimal(str(attr_value))
        attr_value = str(attr_value)
    elif attr_type is types.AttrType.BOOL:
        if not isinstance(attr_value, bool):
            raise TypeError(attr_value)
    elif attr_type is types.AttrType.NULL:
        if not isinstance(attr_value, bool):
            raise TypeError(attr_value)
        elif attr_value is not True:
            raise ValueError(attr_value)
    else:
        raise ValueError(attr_type)
    return {
        attr_name: {attr_type.value: attr_value}
    }


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
