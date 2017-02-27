import decimal
import weakref

from . import ddb, models, util


class Attribute:

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

    def serialize(self, value):
        return value if isinstance(value, str) else str(value)

    def deserialize(self, value):
        return value


Attribute._indexes = weakref.WeakKeyDictionary()


class Binary(Attribute):

    def __set__(self, instance, value):
        if not (isinstance(value, bytes) or (value is None and self.nullable)):
            msg = f'BinaryAttribute requires bytes value, not {type(value)}'
            raise TypeError(msg)

    def serialize(self, value):
        return super().serialize(base64.b64encode(value))

    def deserialize(self, value):
        return super().deserialize(base64.b64decode(value))


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

