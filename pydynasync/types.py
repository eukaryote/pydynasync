import base64
import decimal
import enum
from .serialization import (
    make_scalar_converter, make_set_converter, null_converter,
    make_serialization_helpers, pack_set
)


class EnumBase:

    @classmethod
    def from_value(cls, value):
        """Get enum by value."""
        return cls[value]

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
                (k, self.serialize(k, v)[k]) for k, v in kwargs.items()
                # (k, pack_scalar(self, k, v)[k]) for k, v in kwargs.items()
            )
        elif self.is_set_type():
            return dict(
                # (k, self.serialize(k, v)[k]) for k, v in kwargs.items()
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
            return self.convert(value)
        raise NotImplementedError()

    def convert_set(self, value):
        if self.is_set_type():
            base_attr_type = AttrType[self.value[:1]]
            return list(map(base_attr_type.convert, value))
        raise NotImplementedError()


# Register convert function for each type
AttrType.B.convert = make_scalar_converter(str, {bytes: base64.b64encode})
AttrType.N.convert = make_scalar_converter(
    str,
    {str: lambda s: str(decimal.Decimal(s)),
     float: lambda x: str(decimal.Decimal(str(x))),
     int: str,
     decimal.Decimal: str},
    force=True,
)
AttrType.S.convert = make_scalar_converter(str, {})
AttrType.BOOL.convert = make_scalar_converter(bool, {bool: bool}, force=True)
AttrType.NULL.convert = null_converter
AttrType.BS.convert = make_set_converter(AttrType.B.convert)
AttrType.NS.convert = make_set_converter(AttrType.N.convert)
AttrType.SS.convert = make_set_converter(AttrType.S.convert)

# Register serialize/deserialize functions for each type
AttrType.B.serialize, AttrType.B.deserialize = make_serialization_helpers(
    AttrType.B,
    AttrType.B.convert,
    base64.b64decode,
)
AttrType.N.serialize, AttrType.N.deserialize = make_serialization_helpers(
    AttrType.N,
    AttrType.N.convert,
    lambda s: decimal.Decimal(s) if '.' in s else int(s),
)
AttrType.S.serialize, AttrType.S.deserialize = make_serialization_helpers(
    AttrType.S,
    AttrType.S.convert,
    lambda s: s,
)
AttrType.BOOL.serialize, AttrType.BOOL.deserialize = \
    make_serialization_helpers(
        AttrType.BOOL,
        AttrType.BOOL.convert,
        lambda b: b,
    )
AttrType.NULL.serialize, AttrType.NULL.deserialize = \
    make_serialization_helpers(
        AttrType.NULL,
        AttrType.NULL.convert,
        lambda b: None,
    )
AttrType.SS.serialize, AttrType.SS.deserialize = make_serialization_helpers(
    AttrType.SS,
    make_set_converter(AttrType.S.convert),
    set,
)
AttrType.NS.serialize, AttrType.NS.deserialize = make_serialization_helpers(
    AttrType.NS,
    make_set_converter(AttrType.N.convert),
    lambda value: set(map(AttrType.N.deserialize, value)),
)
AttrType.BS.serialize, AttrType.BS.deserialize = make_serialization_helpers(
    AttrType.BS,
    make_set_converter(AttrType.B.convert),
    lambda value: set(map(AttrType.B.deserialize, value)),
)


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
