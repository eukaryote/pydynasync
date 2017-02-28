import base64

from pydynasync.types import AttrType, KeyType, ProjectionType
import pydynasync.exp as exp


def test_product_catalog_spec(product_catalog_spec):
    spec = product_catalog_spec
    assert spec.TableName == 'ProductCatalog'
    assert len(spec.AttributeDefinitions) == 1
    assert len(spec.KeySchema) == 1
    assert spec.AttributeDefinitions[0].AttributeType == AttrType.N


def test_forum_spec(forum_spec):
    spec = forum_spec
    assert spec.TableName == 'Forum'
    assert len(spec.AttributeDefinitions) == 1
    assert len(spec.KeySchema) == 1
    assert spec.AttributeDefinitions[0].AttributeType == AttrType.S


def test_thread_spec(thread_spec):
    spec = thread_spec
    assert spec.TableName == 'Thread'
    assert len(spec.AttributeDefinitions) == 2
    assert len(spec.KeySchema) == 2
    assert spec.AttributeDefinitions[0].AttributeType == AttrType.S
    assert spec.AttributeDefinitions[1].AttributeType == AttrType.S


def test_reply_spec(reply_spec):
    spec = reply_spec
    assert spec.TableName == 'Reply'
    assert spec.AttributeDefinitions == [
        exp.Attribute('Id', AttrType.S),
        exp.Attribute('ReplyDateTime', AttrType.S),
        exp.Attribute('PostedBy', AttrType.S),
    ]
    assert spec.KeySchema == [
        exp.Key('Id', KeyType.HASH),
        exp.Key('ReplyDateTime', KeyType.RANGE),
    ]
    assert spec.AttributeDefinitions[0].AttributeType == AttrType.S
    assert spec.AttributeDefinitions[1].AttributeType == AttrType.S
    assert spec.LocalSecondaryIndexes
    hkey, rkey = spec.KeySchema
    assert hkey.KeyType == KeyType.HASH
    assert rkey.KeyType == KeyType.RANGE
    lsi = spec.LocalSecondaryIndexes
    assert len(lsi) == 1
    index = lsi[0]
    assert index.IndexName == 'PostedByIndex'
    assert index.KeySchema == [
        exp.Key('Id', KeyType.HASH),
        exp.Key('PostedBy', KeyType.RANGE),
    ]
    assert index.Projection == exp.Projection(
        ProjectionType=ProjectionType.KEYS_ONLY,
        NonKeyAttributes=None
    )


def test_product_catalog_table(product_catalog_table, client):
    t = product_catalog_table
    assert client.describe_table(TableName=t['TableName'])


def test_forum_table(forum_table, client):
    t = forum_table
    assert client.describe_table(TableName=t['TableName'])


def test_thread_table(thread_table, client):
    t = thread_table
    assert client.describe_table(TableName=t['TableName'])


def test_reply_table(reply_table, client):
    t = reply_table
    assert client.describe_table(TableName=t['TableName'])


def test_test_table(test_table, client):
    t = test_table
    assert client.describe_table(TableName=t['TableName'])
    import pprint

    result = client.put_item(
        TableName='Test',
        Item={
            'Id': {'N': '1'},
            'Handiness': {'S': 'most decent'},
            'Adhoc': {'S': 'and another'},
        }
    )
    print('put_item result:')
    pprint.pprint(result)
    print()

    result = client.get_item(
        TableName='Test',
        Key={
            'Id': {'N': '1'},
            'Handiness': {'S': 'most decent'},
        },
        ReturnConsumedCapacity='TOTAL',
    )
    print('get_item result:')
    pprint.pprint(result)
    print()

    result = client.get_item(
        TableName='Test',
        Key={
            'Id': {'N': '1'},
            'Handiness': {'S': 'most decent'},
        },
        ProjectionExpression="Id,Handiness",
        ReturnConsumedCapacity='TOTAL',
    )
    print('get_item ProjectionExpression result:')
    pprint.pprint(result)
    print()

    result = client.delete_item(
        TableName='Test',
        Key={
            'Id': {'N': '1'},
            'Handiness': {'S': 'most decent'},
        },
        ReturnConsumedCapacity='TOTAL',
    )
    print('delete_item result:')
    pprint.pprint(result)
    print()

    result = client.put_item(
        TableName='Test',
        Item={
            'Id': {'N': '2'},
            'Handiness': {'S': '2'},
            'AND': {'S': 'reserved'},
        },
        ReturnConsumedCapacity='TOTAL',
    )
    print('put_item result:')
    pprint.pprint(result)
    print()

    result = client.get_item(
        TableName='Test',
        Key={
            'Id': {'N': '2'},
            'Handiness': {'S': '2'},
        },
        ReturnConsumedCapacity='TOTAL',
    )
    print('get_item (AND attr):')
    pprint.pprint(result)
    print()

    result = client.get_item(
        TableName='Test',
        Key={
            'Id': {'N': '1'},
            'Handiness': {'S': '2'},
        },
        ProjectionExpression='Id,Handiness',
        ReturnConsumedCapacity='TOTAL',
    )
    print('get_item ProjectionExpression:')
    pprint.pprint(result)
    print()

    result = client.delete_item(
        TableName='Test',
        Key={
            'Id': {'N': '2'},
            'Handiness': {'S': '2'},
        },
        ReturnConsumedCapacity='TOTAL',
    )
    print('delete_item result:')
    pprint.pprint(result)
    print()
    # assert False
