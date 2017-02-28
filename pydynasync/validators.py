from .types import KeyType, StreamViewType, AttrType


def list_of(validate1):
    def check(seq):
        for elem in seq:
            validate1(elem)
    return check


def attribute_name(cls, attrib, val):
    if not isinstance(val, str) or not (1 <= len(val) <= 255):
        raise ValueError("'%s' is not a valid attribute name" % (val,))


def attribute_type(cls, attrib, val):
    if val not in (AttrType.S, AttrType.N, AttrType.B):
        raise ValueError("'%s' is not a valid attribute type" % (val,))


def key_type(cls, attrib, val):
    if val not in KeyType:
        raise ValueError("'%s' is not a valid key type" % (val,))


def stream_view_type(cls, attrib, val):
    if val is not None and val not in StreamViewType:
        raise ValueError("'%s' is not a valid stream view type" % (val,))
