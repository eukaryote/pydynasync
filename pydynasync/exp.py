import logging
import os
import time

import attr

import botocore.config
from botocore.exceptions import ClientError

import boto3

import attr

from . import converters as C, validators as V
from .const import KeyType, StreamViewType, Type

logging.basicConfig()

# boto3.set_stream_logger(name='botocore')

DYNAMODB_CONFIG = botocore.config.Config(signature_version='s3v4')

@attr.s
class ProvisionedThroughput:
   ReadCapacityUnits = attr.ib(convert=int)
   WriteCapacityUnits = attr.ib(convert=int)

   def to_boto(self):
        return attr.asdict(self)


@attr.s
class Projection:
    ProjectionType = attr.ib(convert=C.projection)
    NonKeyAttributes = attr.ib(convert=C.list_of(V.attribute_name))

    def to_boto(self):
        d = {
            'ProjectionType': self.ProjectionType.value,
        }
        if self.NonKeyAttributes:
            d['NonKeyAttributes'] = self.NonKeyAttributes[:]
        return d


@attr.s
class Spec:
    TableName = attr.ib()
    KeySchema = attr.ib(convert=C.list_of(C.key))
    AttributeDefinitions = attr.ib(convert=C.list_of(C.attribute_definition))
    ProvisionedThroughput = attr.ib(default=(5, 5),
                                    convert=C.provisioned_throughput)
    StreamSpecification = attr.ib(convert=C.stream_specification,
                                  default=False)
    LocalSecondaryIndexes = attr.ib(convert=C.list_of(C.lsi), default=None)
    GlobalSecondaryIndexes = attr.ib(convert=C.list_of(C.gsi), default=None)

    def to_boto(self):
        return {
            'TableName': self.TableName,
            'KeySchema': list(k.to_boto() for k in self.KeySchema),
            'AttributeDefinitions': list(a.to_boto()
                                         for a in self.AttributeDefinitions),
            'ProvisionedThroughput': self.ProvisionedThroughput.to_boto(),
            'StreamSpecification': self.StreamSpecification.to_boto(),
            'LocalSecondaryIndexes': list(i.to_boto()
                                          for i in self.LocalSecondaryIndexes),
            'GlobalSecondaryIndexes': list(i.to_boto()
                                           for i in self.GlobalSecondaryIndexes)
        }


@attr.s
class Attribute:
    AttributeName = attr.ib(validator=V.attribute_name)
    AttributeType = attr.ib(validator=V.attribute_type)

    def to_boto(self):
        return {
            'AttributeName': self.AttributeName,
            'AttributeType': self.AttributeType.value,
        }


@attr.s
class Key:
    AttributeName = attr.ib(validator=V.attribute_name)
    KeyType = attr.ib(validator=V.key_type)

    def to_boto(self):
        return {
            'AttributeName': self.AttributeName,
            'KeyType': self.KeyType.value,
        }


@attr.s
class LSI:
    """A local secondary index."""
    IndexName = attr.ib(validator=V.attribute_name)
    KeySchema = attr.ib(convert=C.list_of(C.key))
    Projection = attr.ib(convert=C.projection)

    def to_boto(self):
        return {
            'IndexName': self.IndexName,
            'KeySchema':  list(k.to_boto() for k in self.KeySchema),
            'Projection': self.Projection.to_boto(),
        }


@attr.s
class GSI(LSI):
    """A global secondary index."""
    ProvisionedThroughput = attr.ib(default=(5, 5),
                                    convert=C.provisioned_throughput)

    def to_boto(self):
        return attr.asdict()

@attr.s
class StreamSpecification:
    StreamEnabled = attr.ib(default=False)
    StreamViewType = attr.ib(default=StreamViewType.KEYS_ONLY,
                             validator=V.stream_view_type,)

    def to_boto(self):
        d = {
            'StreamEnabled': self.StreamEnabled,
        }
        if self.StreamEnabled:
            d['StreamViewType'] = self.StreamViewType.value,
        return d


def make_table_spec(name, *, id=None, range=None, extra_attrs=None,
                    capacity=(10, 5), stream_specification=None,
                    local_secondary_indexes=None,
                    global_secondary_indexes=None):
    if id is None:
        iname, itype = 'id', Type.N
    else:
        iname, itype = id
    keys = [Key(AttributeName=iname, KeyType=KeyType.HASH)]
    attrs = [Attribute(AttributeName=iname, AttributeType=itype)]
    if range is not None:
        rname, rtype = range
        keys.append(Key(AttributeName=rname, KeyType=KeyType.RANGE))
        attrs.append(Attribute(AttributeName=rname, AttributeType=rtype))
    if extra_attrs:
        attrs.extend(map(C.attribute_definition, extra_attrs))

    params = dict(
        AttributeDefinitions=attrs,
        TableName=name,
        KeySchema=keys,
        ProvisionedThroughput=C.provisioned_throughput(capacity),
        StreamSpecification=C.stream_specification(stream_specification)
    )
    if local_secondary_indexes:
        local_secondary_indexes = C.list_of(C.lsi)(local_secondary_indexes)
        params['LocalSecondaryIndexes'] = local_secondary_indexes
    if global_secondary_indexes:
        global_secondary_indexes = C.list_of(C.gsi)(global_secondary_indexes)
        params['GlobalSecondaryIndexes'] = global_secondary_indexes
    return Spec(**params)


def create_table(client, spec, wait=False):
    d = dict((k, v) for k, v in spec.to_boto().items() if v not in [None, []])
    result = client.create_table(**d)
    if wait:
        waiter = client.get_waiter('table_exists')
        while waiter.wait(TableName=spec.TableName):
            time.sleep(0.25)
    return result['TableDescription']


def resolve(endpoint, session, config):
    if endpoint is None:
        endpoint = os.environ['DYNAMODB_ENDPOINT_URL']
    if session is None:
        session = make_session()
    if config is None:
        config = DYNAMODB_CONFIG
    return endpoint, session, config


def get_client(*, endpoint=None, session=None, config=None):
    endpoint, session, config = resolve(endpoint, session, config)
    return session.client('dynamodb', endpoint_url=endpoint, config=config)


def get_resource(*, endpoint=None, session=None, config=None):
    endpoint, session, config = resolve(endpoint, session, config)
    return session.resource('dynamodb', endpoint_url=endpoint, config=config)


def make_session():
    return boto3.session.Session()


def main():
    session = make_session()
    client = get_client(session=session)
    print(client)
    name = 'Test'
    try:
        table = client.describe_table(TableName=name)
    except ClientError as e:
        #e.response['Error']['Code']
        resp = client.create_table(make_table_spec(name))


if __name__ == '__main__':
    main()
