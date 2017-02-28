import abc
import collections.abc
import decimal
import weakref

from . import ddb, models, types, util
from .serialization import pack_scalar, unpack_scalar


class Attribute(metaclass=abc.ABCMeta):

    def __init__(self, *, nullable=False, ddb_name=None):
        self.__name = None
        self.__owner = None
        self.__index = None
        self.__nullable = nullable
        self.__ddb_name = ddb_name
        self.values = weakref.WeakKeyDictionary()
        self.original = weakref.WeakKeyDictionary()

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
        if value is None:
            if not self.nullable:
                raise TypeError(f'{self.__name} may not be null')

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

    @abc.abstractmethod
    def _check(self, value):
        """
        Check the value, returning value to use on success or raising
        TypeError or ValueError on failure.
        """
        if value is None and not self.nullable:
            raise TypeError(f"'{self.name}' attribute is not nullable")
        return value

    @abc.abstractmethod
    def serialize(self, value):
        """
        Serialize a valid value for this attribute type to a DynamoDB dict.
        """

    @abc.abstractmethod
    def deserialize(self, value):
        """
        Deserialize a DynamoDB dict to an attribute value of this attribute.
        """


Attribute._indexes = weakref.WeakKeyDictionary()

#TODO: this serialization/deserialization stuff should be
# usable by these attributes (high-level ORM) as well as
# by the calls like AttrType.S(Name="Jos K") (low-level API).

class String(Attribute):

    def _check(self, value):
        if not (isinstance(value, str) or (value is None and self.nullable)):
            raise TypeError(f'String attribute requires a str value, not '
                            f'{type(value)}')
        return value

    def serialize(self, value):
        if value is None and self.nullable:
            return None
        return pack_scalar(types.AttrType.S, self.ddb_name, self._check(value))

    def deserialize(self, value):
        if value is None and self.nullable:
            return None
        stype, sname, svalue = unpack_scalar(value)
        if stype is not types.AttrType.S:
            raise TypeError(value)
        if sname != self.ddb_name:
            raise ValueError(f"name {sname} in value does not match ddb_name "
                             f"{self.ddb_name}")
        return svalue



class StringSet(Attribute):

    def _check(self, value):
        if value is None and self.nullable:
            return None
        elif not (isinstance(value, set) and
                  all(isinstance(v, str) for v in value)):
            raise TypeError(f'StringSet attribute requires a set of str')
        return value

    def serialize(self, value):
        value = self._check(value)
        if value is None:
            return None
        return tuple(map(str, value))

    def deserialize(self, value):
        pass


class Binary(Attribute):

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

    def serialize(self, value):
        value = self._check(value)
        if value is None:
            return None
        return pack_scalar(types.AttrType.B, self.ddb_name, value)

    def deserialize(self, value):
        stype, sname, svalue = unpack_scalar(value)
        if stype is not Attr.B:
            raise ValueError(stype)
        elif sname != self.ddb_name:
            raise ValueError(sname)
        return svalue


class Number(Attribute):

    def _check(self, value):
        if value is None and self.nullable:
            return None

        if not isinstance(value, (int, float, decimal.Decimal)):
            msg = f'{value} should be an int, float, or decimal.Decimal'
            raise TypeError(msg)
        elif not (ddb.NUMBER_RANGE[0] < value < ddb.NUMBER_RANGE[1]):
            raise ValueError(f'{value} is outside permitted numeric range')
        return value

    def __set__(self, instance, value):
        super().__set__(instance, self._check(value))

    def serialize(self, value):
        value = self._check(value)
        return None if value is None else str(value)

    def deserialize(self, value):
        if self.nullable and value is None:
            return None
        try:
            return int(value)
        except ValueError:
            return float(value)


class Integer(Number):

    def _check(self, value):
        if value is None and self.nullable:
            return value
        if not isinstance(value, int):
            raise TypeError(f'{value} should be an int')
        return super()._check(value)

    def deserialize(self, value):
        if self.nullable and value is None:
            return None
        return int(value)


class Decimal(Number):

    def _check(self, value):
        if value is None and self.nullable:
            return value
        if not isinstance(value, (float, decimal.Decimal)):
            raise TypeError(f'{value} should be a float or decimal.Decimal')
        if isinstance(value, float):
            value = decimal.Decimal(str(value))
        return value

    def __set__(self, instance, value):
        super().__set__(instance, self._check(value))

    def serialize(self, value):
        value = self._check(value)
        return None if value is None else str(value)

    def deserialize(self, value):
        if self.nullable and value is None:
            return None
        return decimal.Decimal(value)


class Boolean(Attribute):

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


class List(Attribute):

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

    def _check(self, value):
        if not isinstance(value, collections.abc.Mapping):
            raise TypeError(f'{value} should be a mapping')

    def __set__(self, instance, value):
        super().__set__(instance, self._check(value))

    def serialize(self, value):
        value = self._check(value)
        return None if value is None else value

