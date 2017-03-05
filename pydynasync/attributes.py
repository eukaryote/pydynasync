import abc
import collections.abc
import decimal
import weakref

from . import ddb, models, types, util


def check_number_range(value):
    if not (ddb.NUMBER_RANGE[0] < value < ddb.NUMBER_RANGE[1]):
        raise ValueError(f'{value} is outside permitted numeric range')


class Attribute(metaclass=abc.ABCMeta):

    # The types.AttrType value for this attribute, which if set by
    # a subclass will be used as the default when no `attr_type`
    # is provided to `__init__`.
    TYPE = None

    def __init__(self, *, nullable=False, ddb_name=None, attr_type=None):
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
        self.values = weakref.WeakKeyDictionary()
        self.original = weakref.WeakKeyDictionary()

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
        # if value is None:
        #     if not self.nullable:
        #         raise TypeError(f'{self.__name} may not be null')

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
            raise TypeError(f'{self.__name} may not be null')
        self.values.pop(instance, None)

    def __set_name__(self, owner, name):
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
        if value is None and not self.nullable:
            raise TypeError(f"'{self.name}' attribute is not nullable")
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

#TODO: this serialization/deserialization stuff should be
# usable by these attributes (high-level ORM) as well as
# by the calls like AttrType.S(Name="Jos K") (low-level API).

class String(Attribute):

    """
    Attribute that allows str values, and optionally None (if `nullable).
    """

    TYPE = types.AttrType.S

    def _check(self, value):
        value = super()._check(value)
        if value is not None and not isinstance(value, str):
            raise TypeError(f'String attribute requires a str value, not '
                            f'{type(value)}')
        return value


class StringSet(Attribute):

    """
    Attribute that allows a set of strings, and optionally None (if `nullable).
    """

    TYPE = types.AttrType.SS

    def _check(self, value):
        value = super()._check(value)
        if value is not None and not (isinstance(value, set) and
                                      all(isinstance(v, str) for v in value)):
            raise TypeError(f'StringSet attribute requires a set of str')
        return value

    def serialize(self, value):
        value = self._check(value)
        if value is not None:
            value = types.AttrType.SS(**{self.ddb_name: list(value)})
        return value

    def deserialize(self, value):
        return set(value[self.ddb_name][type.AttrType.SS.value])


class Binary(Attribute):

    """
    Attribute that allows bytes values, and optionally None (if `nullable).
    """

    TYPE = types.AttrType.B

    def __set__(self, instance, value):
        if not (isinstance(value, bytes) or (value is None and self.nullable)):
            msg = f'BinaryAttribute requires bytes value, not {type(value)}'
            raise TypeError(msg)

    def _check(self, value):
        if value is None and self.nullable:
            return None
        elif not isinstance(value, bytes):
            raise TypeError(value)
        return value


class Number(Attribute):

    """
    Base number type, which allows int, float or decimal.Decimal values.

    See also `Integer` and `Decimal` to constrain the type to just integral
    or decimal values.
    """

    TYPE = types.AttrType.N

    allowed_number_types = (int, float, decimal.Decimal)

    def _check(self, value):
        value = super()._check(value)
        if value is not None:
            if not isinstance(value, self.allowed_number_types):
                exp = ', '.join(t.__name__ for t in self.allowed_number_types)
                msg = f"value '{value}' should be of type: {exp}"
                raise TypeError(msg)
            elif not (ddb.NUMBER_RANGE[0] < value < ddb.NUMBER_RANGE[1]):
                raise ValueError(f'{value} is outside permitted numeric range')
        return value


class Integer(Number):

    """
    Attribute that allows integer values, and optionally None (if `nullable`).
    """

    allowed_number_types = (int,)


class Decimal(Number):

    """
    Attribute that allows decimal or float values, and optionally None
    (if `nullable`).
    """

    allowed_number_types = (decimal.Decimal, float)



class Boolean(Attribute):

    """
    Attribute that allows boolean values, and optionally None (if `nullable).
    """

    TYPE = types.AttrType.BOOL

    def _check(self, value):
        if not (isinstance(value, bool) or (value is None and self.nullable)):
            raise TypeError(f'{value} should be a bool')
        return value

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

    def _check(self, value):
        if not (value is True or (value is None and self.nullable)):
            msg = f'value "{value}" should be True or None if nullable'
            raise TypeError(msg)
        return value

    def __set__(self, instance, value):
        super().__set__(instance, self._check(value))

    def serialize(self, value):
        return self._check(value)

    def deserialize(self, value):
        return value


class List(Attribute):

    TYPE = types.AttrType.L

    def _check(self, value):
        if not (isinstance(value, (list, tuple)) or
                (value is None and self.nullable)):
            raise TypeError(f'{value} should be a list or tuple')
        return value

    def __set__(self, instance, value):
        super().__set__(instance, self._check(value))

    def serialize(self, value):
        value = self._check(value)
        return None if value is None else value


class Map(Attribute):

    TYPE = types.AttrType.M

    def _check(self, value):
        if not isinstance(value, collections.abc.Mapping):
            raise TypeError(f'{value} should be a mapping')

    def __set__(self, instance, value):
        super().__set__(instance, self._check(value))

    def serialize(self, value):
        value = self._check(value)
        return None if value is None else value

