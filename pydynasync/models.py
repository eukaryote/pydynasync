import collections
import inspect
import itertools
import sys
import traceback
from traceback import walk_stack
from weakref import ref, WeakKeyDictionary

NOTFOUND = object()
NOTSET = object()


weakkeydict_codes = tuple(
    func.__code__ for _, func in
        inspect.getmembers(WeakKeyDictionary, inspect.isfunction)
)

def is_weakref_call(*, framenum=2):
    for frame, _ in traceback.walk_stack(sys._getframe(framenum)):
        try:
            if frame.f_code in weakkeydict_codes:
                return True
        except AttributeError:
            pass
    return False


class Attribute:

    def __init__(self, *, nullable=False):
        self.__nullable = nullable
        self.values = WeakKeyDictionary()
        self.original = WeakKeyDictionary()

    @property
    def nullable(self):
        return self.__nullable

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
        return val if val is not NOTSET else None

    def __set__(self, instance, value):
        if value is None:
            if not self.nullable:
                raise TypeError(f'{self.__name} may not be null')

        if self.values.get(instance, NOTFOUND) == value:
            return

        update = getattr(
            type(type(instance))._changes,
            'unset' if value == self.original.get(instance, NOTFOUND) else 'set',
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
        if not issubclass(owner, Model):
            msg = "model attributes may only be class attributes of a Model"
            raise TypeError(msg)
        self.__name = name
        self.__owner = owner
        indexes = type(self)._indexes
        self.__index = indexes.get(owner, 0)
        indexes[owner] = self.__index + 1

    @classmethod
    def serialize(cls, value):
        return str(value)

    @classmethod
    def deserialize(cls, value):
        return value


Attribute._indexes = WeakKeyDictionary()



class IntegerAttribute(Attribute):

    def __set__(self, instance, value):
        if not (isinstance(value, int) or (value is None and self.nullable)):
            raise TypeError(f'{value} should be an int')
        super().__set__(instance, value)


class Changes:

    def __init__(self):
        self._changes = WeakKeyDictionary()

    def _convert(self, instance, value):
        return {
            name: getattr(instance, name, None)
            for index, name in enumerate(type(instance)._members)
            if (value or 0) & (1 << index)
        } if value else {}

    def get(self, instance):
        return self._convert(instance, self._changes.get(instance, 0))

    def set(self, instance, index):
        prev = self._changes.get(instance, 0)
        self._changes[instance] = prev | (1 << index)

    def unset(self, instance, index):
        prev = self._changes.get(instance, 0)
        self._changes[instance] = prev & ~(1 << index)

    def clear(self, instance):
        self._changes[instance] = 0




class ModelMeta(type):

    @classmethod
    def __prepare__(metacls, name, bases, **kwds):
        return collections.OrderedDict()

    def __new__(cls, name, bases, namespace, **kwds):
        # print(f'__new__, name={name}, bases={bases}, namespace={namespace}, '
        #       f'kwds={kwds}')
        ddb_name = kwds.pop('ddb_name', None) or name
        if kwds:
            msg = "invalid class parameter(s): " + ', '.join(kwds.keys())
            raise TypeError(msg)
        result = type.__new__(cls, name, bases, dict(namespace))
        result._members = tuple(x for x in namespace if not x.startswith('__'))
        result._ddb_name = ddb_name
        return result

    @classmethod
    def get_changed(metacls, instance):
        return metacls._changes.get(instance)

    @classmethod
    def clear_changed(metacls, instance):
        metacls._changes.clear(instance)


ModelMeta._changes = Changes()


class Model(metaclass=ModelMeta):

    def __init_subclass__(cls, **kwargs):
        # print(f'__init_subclass__({cls}, {kwargs})')
        ddb_name = kwargs.pop('ddb_name', cls.__name__)
        super().__init_subclass__(**kwargs)
        cls._ddb_name = ddb_name

    def __init__(self, *, _reset=False, **kwargs):
        members = type(self)._members
        for name in members:
            descriptor = getattr(type(self), name)
            value = kwargs.pop(name, NOTSET)
            if value is not NOTSET:
                if _reset:
                    descriptor.reset(self, value)
                else:
                    setattr(self, name, value)
        if kwargs:
            raise TypeError("invalid attributes: " + ', '.join(kwargs.keys()))

    def _key(self):
        """
        Get instance key to be used for equality testing and hashing.
        """
        # Instances of this class are stored in a WeakKeyDictionary, and in
        # that context, equality and hashing should follow object()
        # semantics (based on object identity and never changing regardless
        # of changes to member values), but when not being called from
        # one of the target weakref methods, we use the tuple of
        # all member values as the key for equality testing and hashing,
        # which is what users of the library will expect.
        return self if is_weakref_call() else tuple(
            getattr(self, name, None) for name in type(self)._members
        )

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        key = self._key()
        return (key == other._key()
                if key is not self
                else self is other)

    def __hash__(self):
        return object.__hash__(self._key())


class Person(Model):

    name = Attribute()
    age = IntegerAttribute()
    hair_color = Attribute()


me = Person()
me.name = 'Joseph Knecht'
me.age = 42
me.hair_color = 'brown'

other = Person()
other.name = 'Fritz Tegularius'
other.age = 29
other.hair_color = 'blonde'
