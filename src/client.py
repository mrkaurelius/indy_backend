"""
basic backend client. prototype for androidapp
"""

import argparse
import asyncio
import parser
import json
import requests
import logging
import base64

from utils import print_fail, print_ok, print_server_qr_terminal, PROTOCOL_VERSION, print_warn
from indy import anoncreds, pool, ledger, wallet, did, crypto
from indy.error import IndyError, ErrorCode

logging.basicConfig(level=logging.DEBUG)


async def main():
    pass


async def get_credential():
    '''
    # TODO Hicbirsekilde hata kontrolu yok !
    '''

    print_ok('get credential started')

    # 0. open wallet and create master link
    wallet_config = json.dumps({"id": "client_wallet"})
    wallet_credentials = json.dumps({"key": "very_secret_key"})
    wallet_handle = await wallet.open_wallet(wallet_config, wallet_credentials)
    pool_handle = await pool.open_pool_ledger(config_name='sandbox', config=None)

    link_secret_name = 'link_secret'

    # 1. get available creds
    req = requests.get('http://localhost:3000/availablecreds')
    cred_def_ids = req.text
    cred_def_ids = json.loads(cred_def_ids)
    print_ok(cred_def_ids)

    # TODO credentialin attribute lari ledgerden cekilebilir.
    # 2. get cred offer

    cred_offer_url = f'http://localhost:3000/credoffer/{cred_def_ids[0]}'
    # print(cred_offer_url)
    req = requests.get(cred_offer_url)
    cred_offer_ret = req.text
    cred_offer_ret = json.loads(cred_offer_ret)
    cred_offer_json = cred_offer_ret['cred_offer_json']
    cred_offer_json = json.loads(cred_offer_json)
    cred_offer_json = json.dumps(cred_offer_json)

    print_ok(cred_offer_json)

    # 3. create and send cred req
    '''
    {
        cred_offer_json: cred_offer_json
        cred_req_json: cred_req_json
    }
    '''
    # 3.1 fetch cred def

    # TODO poolu acmak lazim
    cred_def_req = await ledger.build_get_cred_def_request(None, cred_def_ids[0])
    cred_def_resp = await ledger.submit_request(pool_handle, cred_def_req)
    _, cred_def_json = await ledger.parse_get_cred_def_response(cred_def_resp)

    print_ok(cred_def_json)

    cred_req_body = {}

    client_dids = await did.list_my_dids_with_meta(wallet_handle)

    client_dids = json.loads(client_dids)
    client_did = client_dids[0]['did']
    print_warn(f'client did: {client_did}')

    # print_fail(f'{cred_defs[0]}, {type(cred_defs[0])}')

    (cred_req_json, cred_req_metadata_json) = \
        await anoncreds.prover_create_credential_req(wallet_handle, client_did, cred_offer_json, cred_def_json, link_secret_name)
    print_ok('credential request created!')

    cred_req_body['cred_offer_json'] = cred_offer_json
    cred_req_body['cred_req_json'] = cred_req_json
    cred_req_url = f'http://localhost:3000/credrequest'

    cred_req_resp = requests.post(url=cred_req_url, json=cred_req_body)
    cred_req_resp = cred_req_resp.text
    cred_req_resp = json.loads(cred_req_resp)

    print_ok(cred_req_resp)
    # 4. get and store cred

    cred_id = await anoncreds.prover_store_credential(wallet_handle, None, cred_req_metadata_json, cred_req_resp['cred_json'], cred_def_json, None)
    print_ok(cred_id)

    # 5. list cred

    pass


async def list_credentials():
    '''
    list 
    '''

    wallet_config = json.dumps({"id": "client_wallet"})
    wallet_credentials = json.dumps({"key": "very_secret_key"})
    wallet_handle = await wallet.open_wallet(wallet_config, wallet_credentials)

    credentials = await anoncreds.prover_get_credentials(wallet_handle, '{}')
    print_ok(credentials)
    pass


async def init_client():
    '''
    init client indy

    TODO ledgere did'i buradaki seed'i kullanarak ekledim, init scripte tx ile did'i ledgere ekleme
    fonksiyonunu ekle
    '''

    try:
        await pool.set_protocol_version(PROTOCOL_VERSION)
        wallet_config = json.dumps({"id": "client_wallet"})
        wallet_credentials = json.dumps({"key": "very_secret_key"})

        print_warn('creating wallet for client')
        try:
            await wallet.create_wallet(wallet_config, wallet_credentials)
        except IndyError as ex:
            if ex.error_code == ErrorCode.WalletAlreadyExistsError:
                print_fail("wallet already exists  {}".format(wallet_config))

        wallet_handle = await wallet.open_wallet(wallet_config, wallet_credentials)

        client_seed = '000000000000000000000000Client11'
        did_json = json.dumps({'seed': client_seed})
        client_did, client_verkey = await did.create_and_store_my_did(wallet_handle, did_json)
        print_ok(f"client_did: {client_did}, client_verkey: {client_verkey}")

        link_secret_name = 'link_secret'
        link_secret_id = await anoncreds.prover_create_master_secret(wallet_handle,
                                                                     link_secret_name)

    except Exception as e:
        print_fail(e)
        raise e


async def list_dids():
    wallet_config = json.dumps({"id": "client_wallet"})
    wallet_credentials = json.dumps({"key": "very_secret_key"})
    wallet_handle = await wallet.open_wallet(wallet_config, wallet_credentials)
    dids = await did.list_my_dids_with_meta(wallet_handle)
    print_ok(dids)


async def did_auth():
    wallet_config = json.dumps({"id": "client_wallet"})
    wallet_credentials = json.dumps({"key": "very_secret_key"})
    wallet_handle = await wallet.open_wallet(wallet_config, wallet_credentials)
    pool_handle = await pool.open_pool_ledger(config_name='sandbox', config=None)

    dids = await did.list_my_dids_with_meta(wallet_handle)
    # print(type(dids))
    dids = json.loads(dids)
    my_did_verkey = dids[0]['verkey']
    my_did= dids[0]['did']

    print(f"dids: {dids}")
    print(f"my did verkey: {my_did_verkey}")

    req = requests.get('http://localhost:3000/auth/challenge')
    challenge = json.loads(req.text)
    print_ok(f"challenge: {challenge}")

    # 1. get server verkey from ledger

    server_verkey = await did.key_for_did(pool_handle, wallet_handle, str(challenge['sdid']))
    print(f"server_verkey: {server_verkey}")
    print(f"challenge nonce: {challenge['nonce']}")

    # 2. create response

    response = {}
    response['sender_did'] = my_did
    nonce = challenge['nonce']
    msg = await crypto.auth_crypt(wallet_handle, my_did_verkey, server_verkey, nonce.encode('utf-8'))
    msg_b64 = base64.b64encode(msg).decode('ascii')
    response['response_msg'] = msg_b64
    print_ok(f"response {response}")

    # 3. send response

    req = requests.post(url='http://localhost:3000/auth/response', json=response)
    
    # 4. retrive jwt


if __name__ == "__main__":
    # SERVER_HOST = 'localhost'
    # SERVER_PORT = 3000

    parser = argparse.ArgumentParser()
    parser.add_argument('--init', action='store_true', help='init client')
    parser.add_argument('--list-creds', action='store_true',
                        help='list credentials')
    parser.add_argument('--get-cred', action='store_true',
                        help='get cred from server')
    parser.add_argument('--list-dids', action='store_true', help='list dids')
    parser.add_argument('--did-auth', action='store_true',
                        help='did authhentication')

    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    if args.init:
        loop.run_until_complete(init_client())
        pass

    elif args.get_cred:
        loop.run_until_complete(get_credential())
        pass

    elif args.list_creds:
        loop.run_until_complete(list_credentials())
        pass

    elif args.list_dids:
        loop.run_until_complete(list_dids())
        pass

    elif args.did_auth:
        loop.run_until_complete(did_auth())
        pass

    else:
        print_ok("main loop running")
        loop.run_until_complete(main())

    loop.close()
