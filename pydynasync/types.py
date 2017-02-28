import decimal
import enum
from .serialization import pack_scalar, unpack_scalar


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
        if not self.is_scalar_type():
            # TODO: implement for non-scalar types
            raise NotImplementedError()
        d = {}
        for k, v in kwargs.items():
            d.update(pack_scalar(self, k, v))
        return d

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
