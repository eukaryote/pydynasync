import gc
from unittest.mock import patch
import weakref

import pytest

import pydynasync.models as M
import pydynasync.attributes as A

from test import StringTest, IntegerTest, Person


def test_changes_none(person1):
    p = person1.person
    changes = M.Changes()
    assert changes.get(p) == {}


def test_changes_update_hash_key(person1):
    p = person1.person
    changes = M.Changes()
    assert not changes.get(p)

    new_value = 2345
    assert p.id != new_value
    p.id = new_value
    changes.set(p, person1.members.index('id'))
    assert changes.get(p) == {'id': new_value}


def test_changes_update(person1):
    p = person1.person
    changes = M.Changes()
    assert not changes.get(p)

    new_name = p.name_ + 'X'
    p.name_ = new_name
    changes.set(p, person1.members.index('name_'))
    assert changes.get(p) == {'name_': new_name}

    new_nickname = (p.nickname or '') + 'X'
    p.nickname = new_nickname
    changes.set(p, person1.members.index('nickname'))
    assert changes.get(p) == {
        'name_': new_name,
        'nickname': new_nickname,
    }

    changes.unset(p, person1.members.index('nickname'))
    assert changes.get(p) == {
        'name_': new_name,
    }


def test_clear_changed(person1):
    p = person1.person
    p.name_ += 'X'
    assert M.ModelMeta.get_changed(p)
    M.ModelMeta.clear_changed(p)
    assert not M.ModelMeta.get_changed(p)


def test_get_changed(person1):
    p = person1.person
    changes = {}

    assert M.ModelMeta.get_changed(p) == changes

    original = p.name_

    p.name_ = original
    assert M.ModelMeta.get_changed(p) == changes

    p.name_ = original + 'X'
    changes['name_'] = original + 'X'
    assert M.ModelMeta.get_changed(p) == changes

    p.nickname = 'magician'
    changes['nickname'] = 'magician'
    assert M.ModelMeta.get_changed(p) == changes


def test_change_undo(person1):
    p = person1.person

    M.ModelMeta.clear_changed(p)
    original_name = p.name_
    type(p).name_.reset(p, p.name_)
    p.name_ = original_name + 'X'
    assert M.ModelMeta.get_changed(p) == {
        'name_': original_name + 'X'
    }

    # setting back to original value should no longer show a change:
    p.name_ = original_name
    assert M.ModelMeta.get_changed(p) == {}


def test_change_undo_multiple(person1):
    p = person1.person

    M.ModelMeta.clear_changed(p)
    original_name = p.name_
    type(p).name_.reset(p, p.name_)
    new_name1 = original_name + 'X'
    new_name2 = new_name1 + 'X'
    p.name_ = new_name1
    p.name_ = new_name2
    assert M.ModelMeta.get_changed(p) == {
        'name_': new_name2,
    }

    p.name_ = original_name
    assert not M.ModelMeta.get_changed(p)


def test_model_members():
    assert Person._members == ('id', 'name_', 'nickname', 'age')


def test_model_ddb_name_provided():
    name = 'myddbname'

    class ModelWithDDBName(M.Model, ddb_name=name):
        id = A.Integer(hash_key=True)
        attr = A.String()

    assert ModelWithDDBName._ddb_name == name


def test_model_invalid_class_params():

    with pytest.raises(TypeError) as e:

        class MyModel(M.Model, foo='foo', bar='barbar'):
            id = A.Integer(hash_key=True)
            attr = A.String()

    assert str(e.value) == ("invalid model class parameter(s): foo, bar")


def test_model_hash_key():

    class MyModel(M.Model):
        id = A.Integer(hash_key=True)

    assert MyModel._hash_key is MyModel.id


def test_model_range_key():

    class MyModel1(M.Model):
        id = A.Integer(hash_key=True)

    assert MyModel1._range_key is None

    class MyModel2(M.Model):
        id = A.Integer(hash_key=True)
        attr = A.String(range_key=True)

    assert MyModel2._range_key is MyModel2.attr
    assert MyModel2._hash_key is MyModel2.id


def test_model_init_keyword_args():

    class MyModel(M.Model):
        id = A.Integer(hash_key=True)
        attr1 = A.String()
        attr2 = A.String()

    m = MyModel(attr1='1', attr2='2')
    assert m.attr1 == '1'
    assert m.attr2 == '2'


def test_model_key_when_not_weakref_call():
    """
    Equality checking is based on instance member values when not checked
    from one of the expected WeakKeyDictionary methods.
    """

    class P(M.Model):
        id = A.Integer(hash_key=True)
        attr1 = A.String()
        attr2 = A.String()

    p = P()
    assert p._key() == (None, None, None)

    p.attr2 = 'foo'
    assert p._key() == (None, None, 'foo')

    p.attr1 = 'bar'
    assert p._key() == (None, 'bar', 'foo')

    p.id = 1
    assert p._key() == (1, 'bar', 'foo')


def test_model_key_when_weakref_call():
    """
    Equality checking is based solely on the object itself when checked
    from one of the expected WeakKeyDictionary methods.
    """

    class P(M.Model):
        id = A.Integer(hash_key=True)
        attr1 = A.String()

    p1, p2 = P(), P()

    with patch('pydynasync.models.util.is_weakref_call') as is_weakref_call:
        is_weakref_call.return_value = True
        assert p1._key() is p1
        assert p2._key() is p2


def test_model_equality_empty():
    a1, a2 = StringTest(), StringTest()
    assert a1 == a2
    assert a2 == a1

    i1 = IntegerTest()
    assert a1._key() == i1._key()
    assert a1 != i1
    assert i1 != a1

    a1.required = '42'
    i1.required = 42
    assert a1 != i1
    assert i1 != a1


def test_model_equality_nonempty():
    name = 'foo'
    p1, p2 = Person(), Person()
    p1.name_ = name

    assert p1 == p1
    assert p1 != p2
    assert p2 != p1

    p2.name_ = name

    assert p1 == p2
    assert p2 == p1

    p1.name_ = p1.name_ + 'X'
    assert p2 != p1
    assert p1 != p2


def test_model_equality_when_weakref_call():

    class P(M.Model):
        id = A.Integer(hash_key=True)
        attr1 = A.String()

    p1, p2 = P(), P()

    assert p1 == p2
    assert p2 == p1

    # when called from a weakref target method, the
    # hash and equality use the default object semantics
    with patch('pydynasync.models.util.is_weakref_call') as is_weakref_call:
        is_weakref_call.return_value = True
        assert p1 != p2
        assert p2 != p1

    assert p1 == p2
    assert p2 == p1


def test_garbage_collection_of_model():

    class P1(M.Model):
        id = A.Integer(hash_key=True)
        attr = A.String()

    class P2(M.Model):
        id = A.Integer(hash_key=True)
        attr = A.String()

    ref1 = weakref.ref(P1)
    ref2 = weakref.ref(P2)

    p1, p2 = P1(), P2()
    p1.attr = 'myvalue'
    p2.attr = 'othervalue'
    assert ref1()
    assert ref2()

    del p1
    del P1
    gc.collect()
    assert not ref1()
    assert ref2()

    del p2
    del P2
    gc.collect()
    assert not ref2()


def test_model_requires_hash_key():

    with pytest.raises(TypeError) as e:

        class MyModel(M.Model):

            id = A.Integer()

    assert str(e.value) == ("model class 'MyModel' does not define a "
                            "hash_key attribute")


def test_model_more_than_one_range_key():

    with pytest.raises(TypeError) as e:

        class MyModel(M.Model):
            id = A.Integer(hash_key=True)
            attr1 = A.Integer(range_key=True)
            attr2 = A.Integer(range_key=True)

    assert str(e.value) == ("model class 'MyModel' defines more "
                            "than one range_key attribute")
