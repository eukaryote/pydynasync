import base64
import decimal
import enum
import itertools
from .serialization import Converter, pack_scalar, pack_set, unpack_scalar


class EnumBase:

    @classmethod
    def from_value(cls, value):
        """Get enum by value."""
        return cls.__members__[value]

    def __str__(self):
        """Use value as str representation, but not for repr."""
        return self.value


@enum.unique
class AttrType(EnumBase, enum.Enum):

    # Scalar types
    S = 'S'        # String
    N = 'N'        # Number
    B = 'B'        # Binary
    BOOL = 'BOOL'  # Boolean
    NULL = 'NULL'  # Null

    # Document types
    M = 'M'        # Map
    L = 'L'        # List

    # Set types
    SS = 'SS'      # String Set
    NS = 'NS'      # Number Set
    BS = 'BS'      # Binary Set

    def is_scalar_type(self):
        return self in (
            AttrType.S, AttrType.N, AttrType.B, AttrType.BOOL, AttrType.NULL
        )

    def is_document_type(self):
        return self in (AttrType.M, AttrType.L)

    def is_set_type(self):
        return self in (AttrType.SS, AttrType.NS, AttrType.BS)

    def __call__(self, **kwargs):
        if self.is_scalar_type():
            return dict(
                # TODO: should also convert first
                (k, pack_scalar(self, k, v)[k]) for k, v in kwargs.items()
            )
        elif self.is_set_type():
            return dict(
                (k, pack_set(self, k, self.convert_set(v))[k])
                for k, v in kwargs.items()
            )
        elif self is AttrType.L:
            return dict(
                (k, {'L': v}) for k, v in kwargs.items()
            )
        elif self is AttrType.M:
            return dict(
                (k, {'M': v}) for k, v in kwargs.items()
            )
        raise NotImplementedError()

    def convert_one(self, value):
        if self.is_scalar_type():
            return AttrType._converters[self](value)
        raise NotImplementedError()

    def convert_set(self, value):
        if self.is_set_type():
            converter = AttrType._converters[getattr(AttrType, self.value[:1])]
            return list(map(converter, value))
        raise NotImplementedError()


AttrType._converters = {
    AttrType.S: Converter(str, {str: lambda s: s}),
    AttrType.B: Converter(str, {bytes: base64.b64encode}),
    AttrType.N: Converter(str, {str: lambda s: str(decimal.Decimal(s)),
                                float: lambda x: str(decimal.Decimal(str(x))),
                                int: str,
                                decimal.Decimal: str}, force=True),
    AttrType.BOOL: Converter(bool,
                             {bool: bool},
                             force=True),
    AttrType.NULL: Converter(str,
                             {bool: (lambda b: 'true' if b else 'false')},
                             force=True),
}

# AttrType.serializers = {
#     'S': str,
#     'N': lambda v: decimal.Decimal(str(v)),
#     'B': base64.b64encode,

# }

@enum.unique
class KeyType(EnumBase, enum.Enum):

    HASH = 'HASH'
    RANGE = 'RANGE'


@enum.unique
class StreamViewType(EnumBase, enum.Enum):

    KEYS_ONLY = 'KEYS_ONLY'
    NEW_IMAGE = 'NEW_IMAGE'
    OLD_IMAGE = 'OLD_IMAGE'
    NEW_AND_OLD_IMAGES = 'NEW_AND_OLD_IMAGES'


@enum.unique
class ProjectionType(EnumBase, enum.Enum):

    ALL = 'ALL'
    KEYS_ONLY = 'KEYS_ONLY'
    INCLUDE = 'INCLUDE'


@enum.unique
class ConsumedCapacity(EnumBase, enum.Enum):

    INDEXES = 'INDEXES'
    TOTAL = 'TOTAL'
    NONE = 'NONE'

@enum.unique
class ReturnValues(EnumBase, enum.Enum):

    NONE = 'NONE'
    ALL_OLD = 'ALL_OLD'
    UPDATED_OLD = 'UPDATED_OLD'
    ALL_NEW = 'ALL_NEW'
    UPDATED_NEW = 'UPDATED_NEW'
