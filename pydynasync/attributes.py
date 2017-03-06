import abc
import collections.abc
import decimal
import weakref

from . import ddb, types, util

# TODO: maybe change 'nullable' to 'required', with semantics of
# allowing None for scalars, empty set for set types, and empty
# list or map for document types.


def check_number_range(value):
    if not (ddb.NUMBER_RANGE[0] < value < ddb.NUMBER_RANGE[1]):
        raise ValueError(f'{value} is outside permitted numeric range')


class SetAttributeMixin:

    def __init__(self, *args, **kwargs):
        if kwargs.get('hash_key') or kwargs.get('range_key'):
            raise TypeError("Set attribute cannot be used as a "
                            "hash or range key")
        super().__init__(*args, **kwargs)

    def _check(self, value):
        if not isinstance(value, (set, list, tuple)):
            raise TypeError(
                "expected value of type [set,list,tuple] for {} attribute "
                "'{}', but received value '{}' of type [{}]".format(
                    type(self).__name__, self.name,
                    value, type(value).__name__))
        check_item = super()._check
        for elem in value:
            check_item(elem)
        return value


class Attribute(metaclass=abc.ABCMeta):

    # The types.AttrType value for this attribute, which if set by
    # a subclass will be used as the default when no `attr_type`
    # is provided to `__init__`.
    TYPE = None

    # Tuple of allowed python types, which the default implementation
    # of the `_check` method uses to type check attribute values.
    # Checking based solely on types is handled automatically if
    # the subclass sets the appropriate types, and the  `_check`
    # method may be overridden for more complex checks.
    # This is used for type-checking the value for non-set types, and
    # for type-checking the items in a set for set-types that
    # also define one or more types in `PYTHON_SET_TYPES`.
    PYTHON_TYPES = ()

    def __init__(self, *, nullable=False, ddb_name=None, attr_type=None,
                 hash_key=False, range_key=False):
        self.__type = attr_type or self.TYPE
        if not isinstance(self.__type, types.AttrType):
            msg = ("`attr_type` is required if no default `TYPE` is "
                   "set for class, and it must be an AttrType instance")
            raise ValueError(msg)
        self.__name = None
        self.__owner = None
        self.__index = None
        self.__nullable = nullable
        self.__ddb_name = ddb_name
        self.__set_type = self.type.is_set_type()
        self.values = weakref.WeakKeyDictionary()
        self.original = weakref.WeakKeyDictionary()
        self.__hash_key = hash_key
        self.__range_key = range_key

    @property
    def type(self):
        return self.__type

    @property
    def nullable(self):
        return self.__nullable

    @property
    def ddb_name(self):
        return self.__ddb_name

    @property
    def name(self):
        return self.__name

    @property
    def hash_key(self):
        return self.__hash_key

    @property
    def range_key(self):
        return self.__range_key

    def reset(self, instance, value):
        """
        Set value for instance and use that value as the original value
        for change tracking.
        """
        self.original[instance] = value
        self._set(instance, value)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        val = self.values.get(instance)
        return val if val is not util.NOTSET else None

    def __set__(self, instance, value):
        value = self._check(value)

        # if value is unchanged, we don't need to do anything
        if self.values.get(instance, util.NOTFOUND) == value:
            return

        update = getattr(
            type(type(instance))._changes,
            'unset' if value == self.original.get(instance, util.NOTFOUND)
            else 'set',
        )
        update(instance, self.__index)
        self._set(instance, value)

    def _set(self, instance, value):
        self.values[instance] = value

    def __delete__(self, instance):
        if not self.nullable:
            raise TypeError("{} attribute '{}' is not nullable and may not "
                            "be deleted".format(type(self).__name__,
                                                self.name))
        self.values.pop(instance, None)

    def __set_name__(self, owner, name):
        from . import models
        if not issubclass(owner, models.Model):
            msg = "model attributes may only be class attributes of a Model"
            raise TypeError(msg)
        # If no ddb_name was provided, then we use the name of the attribute
        # on the instance for the actual ddb name; we verify here
        # in either case that it's not a dynamodb reserved word.
        ddb_name = self.ddb_name or name
        if ddb.is_reserved_word(ddb_name):
            msg = (f"invalid DynamoDB attribute name: '{ddb_name}' is a "
                   "reserved word")
            raise ValueError(msg)
        self.__ddb_name = ddb_name
        self.__name = name
        self.__owner = owner
        indexes = type(self)._indexes
        self.__index = indexes.get(owner, 0)
        indexes[owner] = self.__index + 1

    def _check(self, value):
        """
        Check the value, returning value to use on success or raising
        TypeError or ValueError on failure.

        The default implementation just returns the value if it's not
        None or if it is None and the attribute is nullable, raising
        a TypeError if it is None and not nullable.

        Subclasses should call this to get the null check and then
        do whatever additional checks may be needed
        """
        if value is None:
            if not self.nullable:
                allowed = ', '.join(t.__name__ for t in self.PYTHON_TYPES)
                raise TypeError(
                    "expected non-None value of type [{}] for non-nullable "
                    "{} attribute '{}', but received value 'None'".format(
                        allowed, type(self).__name__, self.name))
        else:
            if not isinstance(value, self.PYTHON_TYPES):
                allowed = ', '.join(t.__name__ for t in self.PYTHON_TYPES)
                raise TypeError(
                    "expected value of type [{}] for {} attribute '{}', "
                    "but received value '{}' of type [{}]".format(
                        allowed, type(self).__name__, self.name,
                        value, type(value).__name__))
        return value

    def serialize(self, value):
        """
        Serialize a valid value for this attribute type to a DynamoDB dict.
        """
        value = self._check(value)
        if value is not None:
            value = self.__type.serialize(self.ddb_name, value)
        return value

    def deserialize(self, value):
        """
        Deserialize a DynamoDB dict to an attribute value of this attribute.
        """
        return self.__type.deserialize(self.ddb_name, value)


Attribute._indexes = weakref.WeakKeyDictionary()


class String(Attribute):

    """
    Attribute that allows str values, and optionally None (if `nullable).
    """

    TYPE = types.AttrType.S
    PYTHON_TYPES = (str,)


class StringSet(SetAttributeMixin, Attribute):

    """
    Attribute that allows a set of strings, and optionally None (if `nullable).
    """

    TYPE = types.AttrType.SS
    PYTHON_TYPES = String.PYTHON_TYPES

    def serialize(self, value):
        value = self._check(value)
        if value is not None:
            value = types.AttrType.SS(**{self.ddb_name: list(value)})
        return value

    def deserialize(self, value):
        return set(value[self.ddb_name][type.AttrType.SS.value])


class Binary(Attribute):

    """
    Attribute that allows bytes values.
    """

    TYPE = types.AttrType.B
    PYTHON_TYPES = (bytes, bytearray)

    def _check(self, value):
        value = super()._check(value)
        if value is not None and not isinstance(value, (bytearray, bytes)):
            raise TypeError(value)
        return value


class BinarySet(SetAttributeMixin, Attribute):

    """
    Attribute that allows a set of bytes or bytearray values.
    """

    TYPE = types.AttrType.BS
    PYTHON_TYPES = Binary.PYTHON_TYPES


class Number(Attribute):

    """
    Base number type, which allows int, float or decimal.Decimal values.

    See also `Integer` and `Decimal` to constrain the type to just integral
    or decimal values.
    """

    TYPE = types.AttrType.N
    PYTHON_TYPES = (int, float, decimal.Decimal)

    def _check(self, value):
        value = super()._check(value)
        if value is not None:
            # don't allow True/False, even though there are technically ints
            if value is True or value is False:
                allowed = ', '.join(t.__name__ for t in self.PYTHON_TYPES)
                raise TypeError(
                    "expected value of type [{}] for {} attribute '{}', "
                    "but received value '{}' of type [{}]".format(
                        allowed, type(self).__name__, self.name,
                        value, type(value).__name__))
            if not (ddb.NUMBER_RANGE[0] < value < ddb.NUMBER_RANGE[1]):
                raise ValueError(f'{value} is outside permitted numeric range')
        return value

    def __set__(self, instance, value):
        super().__set__(instance, self._check(value))


class NumberSet(SetAttributeMixin, Attribute):

    """
    Attribute that allows int, decimal, and float values.
    """

    TYPE = types.AttrType.NS
    PYTHON_TYPES = Number.PYTHON_TYPES


class Integer(Number):

    """
    Attribute that allows integer values, and optionally None (if `nullable`).
    """

    PYTHON_TYPES = (int,)


class IntegerSet(SetAttributeMixin, Attribute):

    """
    Attribute that allows a set of integer values.
    """

    TYPE = types.AttrType.NS
    PYTHON_TYPES = Integer.PYTHON_TYPES


class Decimal(Number):

    """
    Attribute that allows decimal or float values, and optionally None
    (if `nullable`).
    """

    PYTHON_TYPES = (decimal.Decimal, float)


class DecimalSet(SetAttributeMixin, Attribute):

    """
    Attribute that allows a set of decimal.Decimal values.
    """

    TYPE = types.AttrType.NS
    PYTHON_TYPES = Decimal.PYTHON_TYPES


class Boolean(Attribute):

    """
    Attribute that allows boolean values, and optionally None (if `nullable).
    """

    TYPE = types.AttrType.BOOL
    PYTHON_TYPES = (bool,)

    def __set__(self, instance, value):
        super().__set__(instance, self._check(value))

    def serialize(self, value):
        value = self._check(value)
        return None if value is None else ('true' if value else 'false')

    def deserialize(self, value):
        if self.nullable and value is None:
            return None
        result = {'true': True, 'false': False}.get(value)
        if result is None:
            msg = ("serialized boolean value should be 'true' or 'false', "
                   f"not {value}")
            raise ValueError(msg)
        return result


class Null(Attribute):

    TYPE = types.AttrType.NULL
    PYTHON_TYPES = (type(None),)

    def _check(self, value):
        # override to give better error message
        if value is not None:
            raise TypeError("expected None value for Null attribute '{}', "
                            "but received value '{}'".format(self.name, value))
        return None


class List(Attribute):

    TYPE = types.AttrType.L

    def _check(self, value):
        if not (isinstance(value, (list, tuple)) or
                (value is None and self.nullable)):
            raise TypeError("expected value of type [list, tuple] for List "
                            "attribute '{}', but received value '{}' "
                            "of type [{}]".format(self.name, value,
                                                  type(value).__name__))
        return value

    def __set__(self, instance, value):
        super().__set__(instance, self._check(value))

    def serialize(self, value):
        value = self._check(value)
        return None if value is None else value


class Map(Attribute):

    TYPE = types.AttrType.M

    def _check(self, value):
        # TODO: check value in map
        if (not isinstance(value, collections.abc.Mapping) or
                not (value or self.nullable)):
            raise TypeError("expected value of type [mapping] for Map "
                            "attribute '{}', but received value '{}' "
                            "of type [{}]".format(self.name, value,
                                                  type(value).__name__))
        return value

    def __set__(self, instance, value):
        super().__set__(instance, self._check(value))

    def serialize(self, value):
        value = self._check(value)
        return None if value is None else value
