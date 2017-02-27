import decimal
import types

import pytest

from pydynasync import attributes as A, ddb, models as M

from test import BoolTest, DecTest, NumTest


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


def test_number_range():

    class P(M.Model):

        num = A.Number()


    p = P()

    with pytest.raises(ValueError) as e:
        p.num = ddb.NUMBER_RANGE[0]

    assert str(e.value).endswith('is outside permitted numeric range')

    with pytest.raises(ValueError) as e:
        p.num = ddb.NUMBER_RANGE[1]
    assert str(e.value).endswith('is outside permitted numeric range')


@pytest.mark.parametrize('value', [-1, 0, 1E75])
def test_number_check_required_valid(value):
    assert NumTest.required._check(value) is value


@pytest.mark.parametrize('value', [-1, 0, 1E75, None])
def test_number_check_optional_valid(value):
    assert NumTest.optional._check(value) is value


@pytest.mark.parametrize('value,result', [
    (1, '1'),
    (0, '0'),
    (1.1, '1.1'),

])
def test_number_serialization_required(value, result):
    assert NumTest.required.serialize(value) == result
    assert NumTest.required.deserialize(result) == value


def test_number_serialization_optional():
    assert NumTest.optional.serialize(None) is None
    assert NumTest.optional.deserialize(None) is None
    assert NumTest.optional.serialize(1.1) == '1.1'
    assert NumTest.optional.deserialize('1.1') == 1.1


@pytest.mark.parametrize('value,result', [
    (1.1, decimal.Decimal('1.1')),
    (decimal.Decimal('1.1'), decimal.Decimal('1.1'))
])
def test_decimal_check_required_value(value, result):
    assert DecTest.required._check(value) == result


@pytest.mark.parametrize('value,result', [
    (1.1, decimal.Decimal('1.1')),
    (decimal.Decimal('1.1'), decimal.Decimal('1.1')),
    (None, None),
])
def test_decimal_check_optional_value(value, result):
    assert DecTest.optional._check(value) == result


@pytest.mark.parametrize('value,result', [(True, 'true'), (False, 'false')])
def test_boolean_serialization_required(value, result):
    assert BoolTest.required.serialize(value) == result
    assert BoolTest.required.deserialize(result) == value


@pytest.mark.parametrize('value,result', [(True, 'true'), (False, 'false')])
def test_boolean_serialization_optional(value, result):
    assert BoolTest.optional.serialize(value) == result
    assert BoolTest.optional.deserialize(result) == value


@pytest.mark.parametrize('value', [type, 'foo', None])
def test_boolean_check_required_wrong_types(value):
    with pytest.raises(TypeError) as e:
        BoolTest.required._check(value)
    assert str(e.value) == f'{value} should be a bool'


@pytest.mark.parametrize('value', [True, False])
def test_boolean_check_required_valid(value):
    assert BoolTest.required._check(value) is value


@pytest.mark.parametrize('value', [type, 'foo', 0])
def test_boolean_check_optional_wrong_types(value):
    with pytest.raises(TypeError) as e:
        BoolTest.optional._check(value)
    assert str(e.value) == f'{value} should be a bool'


@pytest.mark.parametrize('value', [True, False, None])
def test_boolean_check_optional_valid(value):
    assert BoolTest.optional._check(value) is value
