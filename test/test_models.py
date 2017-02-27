import gc
from types import SimpleNamespace
from unittest.mock import patch
import weakref

import pytest

import pydynasync.models as M


class AttrTest(M.Model):

    required = M.Attribute()
    optional = M.Attribute(nullable=True)


class IntAttrTest(M.Model):

    required = M.IntegerAttribute()
    optional = M.IntegerAttribute(nullable=True)


class Person(M.Model):

    name = M.Attribute()
    nickname = M.Attribute(nullable=True)
    age = M.IntegerAttribute()


@pytest.fixture
def attr1():
    attr = AttrTest()
    attr.required = 'required-value'
    return SimpleNamespace(
        attr=attr,
        required=attr.required,
        members=('required', 'optional'),
    )


@pytest.fixture
def intattr1():
    attr = IntAttrTest()
    attr.required = 42
    M.ModelMeta.clear_changed(attr)
    return SimpleNamespace(
        attr=attr,
        required=attr.required,
        members=('required', 'optional'),
    )


@pytest.fixture
def person1():
    person = Person()
    person.name = 'Job Bluth'
    person.age = 35
    M.ModelMeta.clear_changed(person)
    return SimpleNamespace(
        person=person,
        name=person.name,
        nickname=person.nickname,
        age=person.age,
        members=('name', 'nickname', 'age'),
    )


def test_changes_none(person1):
    p = person1.person
    changes = M.Changes()
    assert changes.get(p) == {}


def test_changes_update(person1):
    p = person1.person
    changes = M.Changes()
    assert not changes.get(p)
    new_name = p.name + 'X'
    p.name = new_name
    changes.set(p, person1.members.index('name'))
    assert changes.get(p) == {'name': new_name}

    new_nickname = (p.nickname or '') + 'X'
    p.nickname = new_nickname
    changes.set(p, person1.members.index('nickname'))
    assert changes.get(p) == {
        'name': new_name,
        'nickname': new_nickname,
    }

    changes.unset(p, person1.members.index('nickname'))
    assert changes.get(p) == {
        'name': new_name,
    }


def test_attr_get(attr1):
    assert attr1.attr.required == attr1.required


def test_attr_set(attr1):
    new_value = attr1.attr.required + 'X'
    attr1.attr.required = new_value
    assert attr1.attr.required == new_value


def test_attr_del_nullable(attr1):
    a = attr1.attr
    a.optional = 'foo'
    assert a.optional == 'foo'
    del a.optional
    assert a.optional is None


def test_attr_del_not_nullable(attr1):
    with pytest.raises(TypeError) as e:
        del attr1.attr.required
    assert str(e.value) == 'required may not be null'


@pytest.mark.parametrize('value', [42, None, 'asdf'])
def test_attr_serialization(attr1, value):
    assert type(attr1.attr).required.serialize(value) == str(value)


def test_intattr_required_get(intattr1):
    assert intattr1.attr.required == intattr1.required


def test_intattr_required_set(intattr1):
    a = intattr1.attr
    new_value = a.required + 1
    a.required = new_value
    assert a.required == new_value

    with pytest.raises(TypeError) as e:
        a.required = '42'
    # TODO: improve error message
    assert str(e.value) == '42 should be an int'


def test_intattr_optional_set(intattr1):
    a = intattr1.attr

    # can set to int
    assert a.optional != a.required
    a.optional = a.required
    assert a.optional == a.required

    # can set to null
    a.optional = None

    # can't set to non-int/none
    with pytest.raises(TypeError) as e:
        a.optional = '42'
    assert str(e.value) == '42 should be an int'


def test_model_members():
    assert Person._members == ('name', 'nickname', 'age')


def test_clear_changed(person1):
    p = person1.person
    p.name += 'X'
    assert M.ModelMeta.get_changed(p)
    M.ModelMeta.clear_changed(p)
    assert not M.ModelMeta.get_changed(p)


def test_get_changed(person1):
    p = person1.person
    changes = {}

    assert M.ModelMeta.get_changed(p) == changes

    original = p.name

    p.name = original
    assert M.ModelMeta.get_changed(p) == changes

    p.name = original + 'X'
    changes['name'] = original + 'X'
    assert M.ModelMeta.get_changed(p) == changes

    p.nickname = 'magician'
    changes['nickname'] = 'magician'
    assert M.ModelMeta.get_changed(p) == changes


def test_change_undo(person1):
    p = person1.person
    changes = {}

    M.ModelMeta.clear_changed(p)
    original_name = p.name
    type(p).name.reset(p, p.name)
    p.name = original_name + 'X'
    assert M.ModelMeta.get_changed(p) == {
        'name': original_name + 'X'
    }

    # setting back to original value should no longer show a change:
    p.name = original_name
    assert M.ModelMeta.get_changed(p) == {}


def test_change_undo_multiple(person1):
    p = person1.person
    changes = {}

    M.ModelMeta.clear_changed(p)
    original_name = p.name
    type(p).name.reset(p, p.name)
    new_name1 = original_name + 'X'
    new_name2 = new_name1 + 'X'
    p.name = new_name1
    p.name = new_name2
    assert M.ModelMeta.get_changed(p) == {
        'name': new_name2,
    }

    p.name = original_name
    assert not M.ModelMeta.get_changed(p)


def test_model_ddb_name_provided():
    name = 'myddbname'
    class ModelWithDDBName(M.Model, ddb_name=name):
        attr = M.Attribute()


    assert ModelWithDDBName._ddb_name == name


def test_model_init_keyword_args():

    class MyModel(M.Model):
        attr1 = M.Attribute()
        attr2 = M.Attribute()

    m = MyModel(attr1='1', attr2='2')
    assert m.attr1 == '1'
    assert m.attr2 == '2'


def test_model_key_when_not_weakref_call():
    """
    Equality checking is based on instance member values when not checked
    from one of the expected WeakKeyDictionary methods.
    """

    class P(M.Model):

        attr1 = M.Attribute()
        attr2 = M.Attribute()

    p = P()
    assert p._key() == (None, None)

    p.attr2 = 'foo'
    assert p._key() == (None, 'foo')

    p.attr1 = 'bar'
    assert p._key() == ('bar', 'foo')


def test_model_key_when_weakref_call():
    """
    Equality checking is based solely on the object itself when checked
    from one of the expected WeakKeyDictionary methods.
    """

    class P(M.Model):

        attr1 = M.Attribute()

    p1, p2 = P(), P()

    with patch('test.test_models.M.is_weakref_call') as is_weakref_call:
        is_weakref_call.return_value = True
        assert p1._key() is p1
        assert p2._key() is p2



def test_model_equality_empty():
    a1, a2 = AttrTest(), AttrTest()
    assert a1 == a2
    assert a2 == a1

    i1 = IntAttrTest()
    assert a1._key() == i1._key()
    assert a1 != i1
    assert i1 != a1

    a1.required = 42
    i1.required = 42
    assert a1 != i1
    assert i1 != a1


def test_model_equality_nonempty():
    name = 'foo'
    p1, p2 = Person(), Person()
    p1.name = name

    assert p1 == p1
    assert p1 != p2
    assert p2 != p1

    p2.name = name

    assert p1 == p2
    assert p2 == p1

    p1.name = p1.name + 'X'
    assert p2 != p1
    assert p1 != p2



def test_model_equality_when_weakref_call():

    class P(M.Model):

        attr1 = M.Attribute()

    p1, p2 = P(), P()

    assert p1 == p2
    assert p2 == p1

    # when called from a weakref target method, the
    # hash and equality use the default object semantics
    with patch('test.test_models.M.is_weakref_call') as is_weakref_call:
        is_weakref_call.return_value = True
        assert p1 != p2
        assert p2 != p1

    assert p1 == p2
    assert p2 == p1


def test_garbage_collection_of_model():

    class P1(M.Model):

        attr = M.Attribute()

    class P2(M.Model):

        attr = M.Attribute()


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
