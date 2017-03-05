import base64
import decimal
import botocore.loaders
import botocore.session

import pytest

import pydynasync.types as T


def assert_success(response):
    code = response['ResponseMetadata']['HTTPStatusCode']
    assert 200 <= code <= 300


@pytest.fixture(scope='session')
def boto_loader():
    return botocore.loaders.Loader()


@pytest.fixture(scope='session')
def ddb_model(boto_loader):
    return boto_loader.load_service_model(
        type_name='service-2',
        service_name='dynamodb'
    )


@pytest.fixture(scope='session')
def ddb_operations(ddb_model):
    return ddb_model['operations']


@pytest.fixture(scope='session')
def ddb_shapes(ddb_model):
    return ddb_model['shapes']



def test_attr_type(ddb_shapes):
    """Verify attribute type constants against botocore."""
    expected = set(a.value for a in T.AttrType)
    actual = set(ddb_shapes['AttributeValue']['members'].keys())
    assert expected == actual


def test_key_type(ddb_shapes):
    expected = set(k.value for k in T.KeyType)
    actual = set(ddb_shapes['KeyType']['enum'])
    assert expected == actual


def test_stream_view_type(ddb_shapes):
    expected = set(s.value for s in T.StreamViewType)
    actual = set(ddb_shapes['StreamViewType']['enum'])
    assert expected == actual

def test_projection_type(ddb_shapes):
    expected = set(p.value for p in T.ProjectionType)
    actual = set(ddb_shapes['ProjectionType']['enum'])


def test_attrtype_string_call():
    assert T.AttrType.S() == {}

    assert T.AttrType.S(foo='bar') == {
        'foo': {
            'S': 'bar'
        }
    }

    assert T.AttrType.S(a='3', c='1', b='2') == {
        'a': {
            'S': '3',
        },
        'b': {
            'S': '2',
        },
        'c': {
            'S': '1',
        }
    }


def test_attrtype_number_call():
    assert T.AttrType.N() == {}

    assert T.AttrType.N(bar=42) == {
        'bar': {
            'N': '42',
        }
    }

    assert T.AttrType.N(foo=3, bar1=1.0, qux=decimal.Decimal('0.1')) == {
        'foo': {
            'N': '3',
        },
        'bar1': {
            'N': '1.0',
        },
        'qux': {
            'N': '0.1',
        }
    }


def test_attrtype_binary_call():
    data = b'b1', b'b2', b'b3'
    expected = list(map(base64.b64encode, data))

    assert T.AttrType.B() == {}


    assert T.AttrType.B(foo=data[0]) == {
        'foo': {
            'B': expected[0],
        }
    }

    assert T.AttrType.B(blah=data[1], blip=data[0], pvit=data[2]) == {
        'blah': {
            'B': expected[1],
        },
        'blip': {
            'B': expected[0],
        },
        'pvit': {
            'B': expected[2],
        }
    }


def test_attrtype_bool_call():
    assert T.AttrType.BOOL() == {}

    assert T.AttrType.BOOL(b=True) == {
        'b': {
            'BOOL': True,
        }
    }

    assert T.AttrType.BOOL(b=False, c=True) == {
        'b': {
            'BOOL': False,
        },
        'c': {
            'BOOL': True,
        }
    }


def test_attrtype_null_call():
    assert T.AttrType.NULL() == {}

    assert T.AttrType.NULL(a=True) == {
        'a': {
            'NULL': True,
        }
    }

    assert T.AttrType.NULL(a=True, c=True) == {
        'a': {
            'NULL': True,
        },
        'c': {
            'NULL': True,
        }
    }

    with pytest.raises(TypeError) as e:
        T.AttrType.NULL(a=False)


def test_attrtype_stringset_call():
    assert T.AttrType.SS() == {}

    assert T.AttrType.SS(foo=['ab', 'c', 'd']) == {
        'foo': {
            'SS': ['ab', 'c', 'd'],
        }
    }

    assert T.AttrType.SS(b=('2', '1', '4', '3'), a=['z', 'a', 'b']) == {
        'b': {
            'SS': ['2', '1', '4', '3'],
        },
        'a': {
            'SS': ['z', 'a', 'b'],
        }
    }


def test_attrtype_numberset_call():
    assert T.AttrType.NS() == {}

    assert T.AttrType.NS(a=[3, decimal.Decimal('1.0'), 2.01]) == {
        'a': {
            'NS': ['3', '1.0', '2.01'],
        }
    }

    assert T.AttrType.NS(a=[1, 2], b=(3, 4)) == {
        'a': {
            'NS': ['1', '2'],
        },
        'b': {
            'NS': ['3', '4'],
        }
    }


def test_attrtype_binaryset_call():
    data = b'b1', b'b2', b'b3', b'b4', b'b5'
    expected = list(map(base64.b64encode, data))

    assert T.AttrType.BS() == {}

    assert T.AttrType.BS(a=[data[0]]) == {
        'a': {
            'BS': [expected[0]],
        }
    }

    assert T.AttrType.BS(a=data[:2], b=data[2:4], c=data[4:5]) == {
        'a': {
            'BS': expected[:2],
        },
        'b': {
            'BS': expected[2:4],
        },
        'c': {
            'BS': expected[4:5],
        }
    }


@pytest.mark.parametrize(
    'attr_type,value', [
    (T.AttrType.S, 'asdf'),
    (T.AttrType.N, 3.14),
    (T.AttrType.B, b'mybinarydata'),
    (T.AttrType.BOOL, True),
    (T.AttrType.BOOL, False),
    (T.AttrType.NULL, True),
    (T.AttrType.SS, ['1', '2', '3']),
    (T.AttrType.NS, [1, decimal.Decimal('2.2'), '3']),
    (T.AttrType.BS, [b'1', b'thequickbrown']),
    (T.AttrType.L, [{'S': 'value1'}, {'N': '2'}]),
    (T.AttrType.M, {'foobar': {'S': 'myfoobar'},
                    'qux': {'N': '42'},
                    'pvit': {'NS': ['1', '2', '3']}}),
    (T.AttrType.M, {'top':
                     {'M': {'middle':
                             {'M': {'bottom': {'S': 'mybottom'}}}}}}),
])
def test_attrtype_ddb_ops(client, test1_table, test1_spec, attr_type, value):
    tablename = test1_spec.TableName
    pk = '42'
    item = {
       'Id': {
            'N': pk,
       }
    }
    serialized = attr_type(MyValue=value)
    item.update(serialized)
    put_result = client.put_item(
        TableName=tablename,
        Item=item,
    )
    print('put_result:', put_result)
    assert_success(put_result)

    try:
        result_item = client.get_item(
            TableName=tablename,
            Key={'Id': {'N': pk}},
        )
        assert_success(result_item)
        assert result_item['Item'] == item
        print('result_item:', result_item)
    finally:
        delete_result = client.delete_item(
            TableName=tablename,
            Key={
                'Id': {
                    'N': '42',
                }
            }
        )
        print('delete_result:', delete_result)
        assert_success(delete_result)

    # assert False

