import types

import pytest

from pydynasync import attributes as A, models as M


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


def test_attribute_name_not_reserved_word():

    # Python intercepts the ValueError and raises a RuntimeError
    with pytest.raises(RuntimeError) as e:

        class P(M.Model):

            exists = A.Attribute()

    cause = e.value.__cause__
    assert isinstance(cause, ValueError)

    msg = "invalid DynamoDB attribute name: 'exists' is a reserved word"
    assert str(cause) == msg


def test_attribute_name_ddb_name():

    class P1(M.Model):

        name = A.Attribute(ddb_name='name_')


    assert P1.name.ddb_name == 'name_'

    class P2(M.Model):

        name_ = A.Attribute()

    assert P2.name_.ddb_name == 'name_'
