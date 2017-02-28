import enum


@enum.unique
class AttrType(enum.Enum):

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

    def __str__(self):
        return self.value


@enum.unique
class KeyType(enum.Enum):

    HASH = 'HASH'
    RANGE = 'RANGE'

    def __str__(self):
        return self.value


@enum.unique
class StreamViewType(enum.Enum):

    KEYS_ONLY = 'KEYS_ONLY'
    NEW_IMAGE = 'NEW_IMAGE'
    OLD_IMAGE = 'OLD_IMAGE'
    NEW_AND_OLD_IMAGES = 'NEW_AND_OLD_IMAGES'

    def __str__(self):
        return self.value


@enum.unique
class ProjectionType(enum.Enum):

    ALL = 'ALL'
    KEYS_ONLY = 'KEYS_ONLY'
    INCLUDE = 'INCLUDE'

    def __str__(self):
        return self.value
