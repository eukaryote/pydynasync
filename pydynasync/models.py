import collections
from weakref import WeakKeyDictionary

from . import ddb, util
from .util import NOTFOUND, NOTSET


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
        return self if util.is_weakref_call() else tuple(
            getattr(self, name, None) for name in type(self)._members
        )

    def __hash__(self):
        return object.__hash__(self._key())

    def __eq__(self, other):
        if other is self:
            return True
        elif type(self) != type(other):
            return NotImplemented
        key = self._key()
        return (key == other._key()
                if key is not self
                else self is other)

    def __ne__(self, other):
        if other is self:
            return False
        elif type(self) != type(other):
            return NotImplemented
        return not(self == other)
