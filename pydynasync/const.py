import enum


@enum.unique
class Type(enum.Enum):

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
    NN = 'NN'      # Number Set
    BB = 'BB'      # Binary Set

    def is_scalar_type(self):
        return self in (Type.S, Type.N, Type.B, Type.BOOL, Type.NULL)

    def is_document_type(self):
        return self in (Type.M, Type.L)

    def is_set_type(self):
        return self in (Type.SS, Type.NN, Type.BB)

    def __str__(self):
        return self.value


@enum.unique
class KeyType(enum.Enum):

    HASH = 'HASH'
    RANGE = 'RANGE'


@enum.unique
class StreamViewType(enum.Enum):

    KEYS_ONLY = 'KEYS_ONLY'
    NEW_IMAGE = 'NEW_IMAGE'
    OLD_IMAGE = 'OLD_IMAGE'
    NEW_AND_OLD_IMAGES = 'NEW_AND_OLD_IMAGES'


@enum.unique
class ProjectionType(enum.Enum):

    ALL = 'ALL'
    KEYS_ONLY = 'KEYS_ONLY'
    INCLUDE = 'INCLUDE'
