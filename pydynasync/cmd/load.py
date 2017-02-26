import json
import sys
import time

from botocore.exceptions import ClientError

from .. import exp, devguide


def read_json(path):
    with open(path, 'rb') as f:
        return json.load(f)


def delete_table(client, table_name, *, wait=True):
    try:
        client.delete_table(TableName=table_name)
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            return
        raise
    else:
        waiter = client.get_waiter('table_not_exists')
        while waiter.wait(TableName=table_name):
            time.sleep(0.25)


def put_json(client, data):
    for table_name, elems  in data.items():
        print('TableName=%s: ' % (table_name,), sep='', end='')
        delete_table(client, table_name, wait=True)
        spec = devguide.specs[table_name]
        exp.create_table(client, spec, wait=True)
        for elem in elems:
            params = elem['PutRequest']
            params['TableName'] = table_name
            params['ReturnValues'] = 'NONE'
            resp = client.put_item(**params)
            assert resp['ResponseMetadata']['HTTPStatusCode'] == 200
            print('.', sep='', end='')
        print()



def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if len(argv) != 1 or argv[0] in ('-h', '--help'):
        msg = "usage: python -m pydynasync.load path"
        raise ValueError(msg)
    path = argv[0]
    data = read_json(path)
    client = exp.get_client()
    put_json(client, data)



if __name__ == '__main__':
    main()
