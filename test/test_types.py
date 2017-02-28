import botocore.loaders
import botocore.session

import pytest

import pydynasync.types as T


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
