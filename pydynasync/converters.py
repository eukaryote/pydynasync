import attr
from .const import ProjectionType


def to_boto(obj):
    if attr.has(type(obj)):
        obj = attr.asdict(obj, filter=lambda a, v: v not in (None, [], ()))
    elif not isinstance(obj, dict):
        raise TypeError("to_boto requires an attrcls or a dict")
    return obj


def list_of(convert1):

    def convert_all(obj):
        if obj is None:
            return []
        else: return list(map(convert1, obj))
    return convert_all


def attribute_definition(obj):
    from .exp import Attribute
    if not isinstance(obj, Attribute):
        if not isinstance(obj, dict):
            raise TypeError("attribute definition should be dict or Attribute")
        obj = Attribute(**obj)
    return obj


def provisioned_throughput(obj):
    from .exp import ProvisionedThroughput
    if obj == False:
        obj = ProvisionedThroughput(False, None)
    elif not isinstance(obj, ProvisionedThroughput):
        if isinstance(obj, dict):
            obj = ProvisionedThroughput(**obj)
        elif isinstance(obj, int):
            obj = ProvisionedThroughput(obj, obj)
        elif isinstance(obj, tuple):
            valid = len(obj) == 2
            if valid:
                valid = all(map(lambda x: isinstance(x, int) and x > 0, obj))
            if not valid:
                msg = ("provisioned throughput tuple should be a pair "
                       "of positive ints")
                raise ValueError
            obj = ProvisionedThroughput(*obj)
        else:
            msg = ("provisioned throughput should be an int, a pair of ints, "
                   "or a dict or ProvisionedThroughput value")
            raise TypeError(msg)
    return obj


def lsi(obj):
    from .exp import LSI
    if not isinstance(obj, LSI):
        if isinstance(obj, dict):
            obj = LSI(**obj)
        else:
            raise TypeError('local secondary index should be a dict or LSI')
    return obj


def gsi(obj):
    from .exp import GSI
    if not isinstance(obj, GSI):
        if isinstance(obj, dict):
            obj = GSI(**obj)
        else:
            raise TypeError('global seconary index should be a dict or GSI')
    return obj


def key(obj):
    from .exp import Key
    if not isinstance(obj, Key):
        if isinstance(obj, dict):
            obj = Key(**obj)
        elif isinstance(obj, tuple) and len(obj) == 2:
            obj = Key(*obj)
        else:
            raise ValueError('Key should be a dict, 2-tuple, or Key')
    return obj


def stream_specification(obj):
    from .exp import StreamSpecification
    if obj is None:
        obj = StreamSpecification(False, None)
    elif not isinstance(obj, StreamSpecification):
        if isinstance(obj, dict):
            obj = StreamSpecification(**obj)
        elif isinstance(obj, tuple):
            if len(obj) == 1:
                if obj[0] != False:
                    msg = ("stream specification 1-tuple may only "
                           "contain False")
                    raise ValueError(msg)
                obj = StreamSpecification(False, None)
            elif len(obj) != 2:
                msg = "stream specification tuple should be 1-tuple or 2-tuple"
                raise ValueError(msg)
            else:
                obj = StreamSpecification(*obj)
        else:
            msg = ("stream specification should be dict, 2-tuple or "
                   "StreamSpecification")
            raise ValueError(msg)
    return obj


def projection(obj):
    from .exp import Projection
    if obj is None:
        return Projection(
            ProjectionType=ProjectionType.KEYS_ONLY,
            NonKeyAttributes=[],
        )
    elif isinstance(obj, dict):
        return Projection(
            ProjectionType=obj['ProjectionType'],
            NonKeyAttributes=obj.get('NonKeyAttributes', []),
        )
    return obj
