"""
indy schema helper scripts
"""

import pyqrcode
import asyncio
import json
import pprint
import logging
import argparse
import asyncio

from indy import pool, ledger, wallet, did, anoncreds
from indy.error import IndyError, ErrorCode

from server_util import start_indy, stop_indy
from utils import get_indy_config, print_server_qr_terminal, print_warn, print_ok, print_fail


logging.basicConfig(level=logging.DEBUG)

# TODO handle'leri boyle tanimlamak ne kadar dogru
indy_config = get_indy_config()
pool_handle = None
wallet_handle = None


# TODO handle lar cirkin olmadan nasil olur
# TODO kritik yerleri kirmizi yap
async def save_schema_to_ledger(pool_handle, wallet_handle, schema):
    '''
    schemayi ledgere indy confige gore ekler ve shema_id yi geri doner

    returns: schema_id
    '''

    steward_did = indy_config['steward_did']
    schema_id, schema_json = await anoncreds.issuer_create_schema(steward_did,
                                                                  schema['name'],
                                                                  schema['version'],
                                                                  schema['attributes'])
    pprint.pprint(schema_json)
    pprint.pprint(schema_id)
    logging.info("schema {}\nschema id: {}".format(
        schema_json, schema_id))

    try:
        schema_request = await ledger.build_schema_request(steward_did, schema_json)
        logging.info("schema request: {}".format(schema_request))

        schema_response = \
            await ledger.sign_and_submit_request(pool_handle,
                                                 wallet_handle,
                                                 steward_did,
                                                 schema_request)

        logging.info("schema response: {}".format(schema_response))

    except Exception as e:
        print("Exception happened")
        logging.error(e)

    # print_warn(type(schema_response))
    schema_response = json.loads(schema_response)

    if schema_response['op'] == 'REJECT':
        print_fail('schema tx rejected !')
        return None

    print_ok('schema {} added to ledger !'.format(schema_id))
    # append schema id to server_schemas.json
    return schema_id


def get_schema_defs():
    """
    ledgere eklenmemis (schema tanimlari) schemalari listele
    """

    with open('json_schemas/indy/indy_schemas.json', 'r') as f:
        schemas = f.read()
        return schemas


def get_added_schemas():
    """
    ledgere eklenmis schemalri listele list_schema_defs den farkli olmali. id vb gibi verileride ekle.
    """

    with open('server_json/server_schemas.json', 'r') as f:
        schemas = f.read()
        return schemas


async def init_schemas():
    """
    tanimlanmis schemalari ledgere ekler ve schema id leri server_json/server_schemas.json'a yazar
    """

    pool_handle, wallet_handle = await start_indy(indy_config)
    schemas_str = get_schema_defs()
    schemas = json.loads(schemas_str)
    schema_ids = []

    print('schema defs')
    print(schemas)

    for s in schemas:
        schema_id = await save_schema_to_ledger(pool_handle, wallet_handle, s)
        if schema_id != None:
            schema_ids.append(schema_id)

    # print_warn(schema_ids)

    if len(schema_ids) > 0:
        print_ok('writing schema ids to json.')

        with open('server_json/server_schemas.json', 'w') as f:
            f.write(json.dumps(schema_ids))

    await stop_indy(pool_handle, wallet_handle)


# gelistirme amacli dummy
async def dummy():
    print('saving schema')
    schema = {
        'name': 'gvtaa',
        'version': '1.0',
        'attributes': '["age", "sex", "height", "name"]'
    }

    pool_handle, wallet_handle = await start_indy(indy_config)

    await save_schema_to_ledger(pool_handle, wallet_handle, schema)

    await stop_indy(pool_handle, wallet_handle)

# TODO cli olarak calismayi destekle
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--init', action='store_true', help='init schemes')
    parser.add_argument('--list-schema-defs', action='store_true', help='')
    parser.add_argument('--list-added-schemas', action='store_true', help='')
    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    if args.init:
        print("initing schemas")
        loop.run_until_complete(init_schemas())

    elif args.list_schema_defs:
        print('listing schema defs')
        schema_defs = get_schema_defs()
        print(schema_defs)

    elif args.list_added_schemas:
        print('listing added ledger (ledger)')
        added_schemas = get_added_schemas()
        print(added_schemas)
    else:
        loop.run_until_complete(dummy())

    loop.close()
