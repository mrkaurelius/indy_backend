"""
Indy SDK crendential helper. schemalar buradan ayrildi.

# TODO hale yapilacak iyilestirmeler olabilir.
Notlar
- masterlink'i aries demolarida ekliyor.
- doc'daki orneklerin idsinin farkli olmasinin sebebi seqno'nun null olmasi
- credential id lerini bizim json dosyalari ile yonetmemiz daha kolay olur gibi
"""

import asyncio
import json
import pprint
import logging
import argparse

from indy import pool, ledger, wallet, did, anoncreds
from indy.error import ErrorCode, IndyError
from server_util import start_indy, stop_indy
from schema_util import get_added_schemas, get_schema_defs

from utils import open_wallet, get_pool_genesis_txn_path, PROTOCOL_VERSION, print_fail, print_log, get_indy_config, print_ok, print_warn, sha256_digest_hex


indy_config = get_indy_config()
pool_handle = None
wallet_handle = None


async def _save_cred_def_to_ledger(schema_id, cred_def_tag='TAG1', cred_def_type='CL'):
    """
    # TODO logify
    # TODO indy ledger error handling
    # TODO ne print edilecek ne loglanacak

    cli ile kullanilmasi icin tasarlandi. diger moduller kullanmamali
    schema_id yi ledgerden ceker ve cred def olarak ekler, 
    ayni sekilde birden fazla cred eklenebiliyor
    return: cred_def_id, None
    """

    steward_did = indy_config["steward_did"]

    schema_req = await ledger.build_get_schema_request(None, schema_id)
    schema_response = await ledger.sign_and_submit_request(pool_handle, wallet_handle, steward_did, schema_req)
    schema_id, schema_json = await ledger.parse_get_schema_response(schema_response)

    print_warn(f'res schema id: {schema_id} schema json{schema_json}')

    # TODO if fetch schema then add cred def
    # if True:
    #     print_ok(schema_id)

    cred_def_config = json.dumps({"support_revocation": False})

    print_fail(schema_json)

    (cred_def_id, cred_def_json) = \
        await anoncreds.issuer_create_and_store_credential_def(wallet_handle,
                                                               steward_did,
                                                               schema_json,
                                                               cred_def_tag,
                                                               cred_def_type,
                                                               cred_def_config)
    print_ok(f"cred def id: {cred_def_id}")
    print_ok(f"cred def json: {cred_def_json}")

    cred_def_request = await ledger.build_cred_def_request(steward_did, cred_def_json)
    cred_def_resp = await ledger.sign_and_submit_request(pool_handle, wallet_handle, steward_did, cred_def_request)
    print_fail(cred_def_resp)
    cred_def_resp = json.loads(cred_def_resp)

    # TODO response burada yermi emin degilim
    if cred_def_resp['op'] == 'REJET':
        print_fail('cred def tx rejected !')
        return None

    print_ok(f'cred def {cred_def_id} added to ledger !')
    return cred_def_id


# TODO neler eksik belirle
async def _init_creds():
    '''
    schemalari ledgere cred def olarak ekle.
    '''

    schema_ids = get_added_schemas()
    schema_ids = json.loads(schema_ids)
    print_fail(f"schema ids: {schema_ids}")

    cred_def_list = []

    for schema_id in schema_ids:
        cred_def_id = await _save_cred_def_to_ledger(schema_id)
        if cred_def_id != None:
            cred_def_list.append(cred_def_id)

    print_warn(cred_def_list)

    if len(cred_def_list) > 0:
        print_ok('writing cred def ids to json')
        with open('server_json/server_cred_defs.json', 'w') as f:
            f.write(json.dumps(cred_def_list))


def get_cred_defs():
    '''
    ledgerden degil, local json dan cred defleri getirir,
    istenirse ledgerden de getirilecek hale getirilebilir
    '''

    with open('server_json/server_cred_defs.json', 'r') as f:
        cred_defs = f.read()
        return cred_defs


def create_gvt_cred_values_json(name, age, sex, height):
    '''
    verilen degerlere gore gvt schemasi icin credetial values json'u dondurur.
    '''
    # TODO check if all str

    cred_value = {}
    cred_value['name'] = {}
    cred_value['name']['raw'] = name
    cred_value['name']['encoded'] = sha256_digest_hex(name)

    cred_value['age'] = {}
    cred_value['age']['raw'] = age
    cred_value['age']['encoded'] = age

    cred_value['sex'] = {}
    cred_value['sex']['raw'] = sex
    cred_value['sex']['encoded'] = sha256_digest_hex(sex)

    cred_value['height'] = {}
    cred_value['height']['raw'] = height
    cred_value['height']['encoded'] = height

    return json.dumps(cred_value)


if __name__ == '__main__':
    """
    Diger moduller util'i kullanirken argumanlari haric indy kutuphanesi ile etkilesmemeli.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument('--init', action='store_true', help='init schemes')
    parser.add_argument('--list-cred-defs', action='store_true', help='')
    args = parser.parse_args()

    loop = asyncio.get_event_loop()

    if args.init:
        pool_handle, wallet_handle = loop.run_until_complete(
            start_indy(indy_config))

        print('initing credentials')
        loop.run_until_complete(_init_creds())

        loop.run_until_complete(stop_indy(pool_handle, wallet_handle))

    elif args.list_cred_defs:
        cred_defs = get_cred_defs()
        print(cred_defs)

    loop.close()
