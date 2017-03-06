from botocore.exceptions import ClientError

import pytest

import pydynasync.exp as exp


def test_create_delete_table(client):
    name = 'CreateDeleteTest'
    spec = exp.make_table_spec(name)
    with pytest.raises(ClientError):
        client.describe_table(TableName=name)
    resp = exp.create_table(client, spec)
    try:
        assert resp['AttributeDefinitions']
    finally:
        client.delete_table(TableName=name)
