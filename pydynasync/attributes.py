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

    @classmethod
    def serialize(cls, value):
        return value if isinstance(value, str) else str(value)

    @classmethod
    def deserialize(cls, value):
        return value


Attribute._indexes = weakref.WeakKeyDictionary()


class BinaryAttribute(Attribute):

    def __set__(self, instance, value):
        if not (isinstance(value, bytes) or (value is None and self.nullable)):
            msg = f'BinaryAttribute requires bytes value, not {type(value)}'
            raise TypeError(msg)

    @classmethod
    def serialize(cls, value):
        return Attribute.serialize(base64.b64encode(value))

    @classmethod
    def deserialize(cls, value):
        return Attribute.deserialize(base64.b64decode(value))



class IntegerAttribute(Attribute):

    def __set__(self, instance, value):
        if not (isinstance(value, int) or (value is None and self.nullable)):
            raise TypeError(f'{value} should be an int')
        super().__set__(instance, value)
