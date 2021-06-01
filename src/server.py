"""
aiohttp kullanan server modülü

Notlar
- jsonlari indy ye vermeden once anlayacagi hale getir.
"""

import pyqrcode
import asyncio
import json
import pprint
import logging
import secrets
import base64
import jwt

from aiohttp import web
from aiohttp.web_app import Application
from aiohttp.web_response import Response, json_response

from indy import anoncreds, crypto, pool, ledger, wallet, did
from indy.error import IndyError, ErrorCode

from utils import get_indy_config, print_server_qr_terminal
from utils import print_fail, print_warn, print_ok

from server_util import start_indy, stop_indy
from credential_util import create_gvt_cred_values_json, get_cred_defs
from schema_util import get_added_schemas


logging.basicConfig(level=logging.INFO)

indy_config = get_indy_config()


# gracefull shutdown
async def on_shutdown(app):
    await stop_indy(app["pool_handle"], app["wallet_handle"])


async def on_startup(app):
    print("Starting Indy")
    pool_handle, wallet_handle = await start_indy(indy_config)
    app["pool_handle"] = pool_handle
    app["wallet_handle"] = wallet_handle

    print_ok(f"dids: {await did.list_my_dids_with_meta(wallet_handle)}")
    print_ok(f"schemas: {get_added_schemas()}")
    print_ok(f"cred defs: {get_cred_defs()}")


def handle_available_creds(request):
    """
    GET /availablecreds
    returns `cred_defs_json`

    Hangi tip cred'in verilebileceğini döndürür. State'e gerek yok.
    Verebilecegi tum credentiallerin idlerini JSON array seklinde döndürür.
    """
    available_creds = get_cred_defs()
    return web.json_response(json.loads(available_creds))


async def handle_cred_offer(request):
    """
    GET /credoffer/<cred_def_id>
    returns `cred_offer_json`

    gelen cred def id ye gore cred offer olusturur ve geri doner
    """
    # TODO check if valid cred ref
    cred_def_id = request.match_info['cred_def_id']

    print_ok(cred_def_id)
    cred_offer_ret = {}
    cred_offer = await anoncreds.issuer_create_credential_offer(app['wallet_handle'], cred_def_id)

    print_ok(cred_offer)

    cred_offer_ret['cred_offer_json'] = cred_offer
    print_ok(cred_offer_ret)

    return web.json_response(cred_offer_ret)


# TODO
async def handle_cred_request(request):
    """
    POST /credrequest
    body'de `cred_req_json` bulunmasi gerekir.
    returns: issued credential


    cred_req_json'u kullanarak credentiali olusturur ve json yapisi icinde geri doner.
    """

    post_body = await request.read()
    post_body = json.loads(post_body)

    cred_req_json = post_body['cred_req_json']
    cred_offer_json = post_body['cred_offer_json']
    print_ok(f'cred_request_json {cred_req_json}')
    print_ok('issuing credential')

    demo_cred_values = create_gvt_cred_values_json(
        'ahmet', '23', 'male', '172')
    print_ok(f'cred values: {demo_cred_values}')

    cred_json, _, _ = await anoncreds.issuer_create_credential(app['wallet_handle'], cred_offer_json, cred_req_json, demo_cred_values, None, None)
    print_ok(f'cred_json: {cred_json}')

    cred_req_ret = {}
    cred_req_ret['cred_json'] = cred_json
    return web.json_response(cred_req_ret)




async def handle_auth_challenge(request):
    '''
    challenge, qr daki veri
    {
        "nonce": "deneme_nonce",
        "s_did": "server_did",
    }
    callback yapmaya gerek yok challenge in nereye gidecegi belli

    GET /auth/challenge
        - challenge jsonu doner. ve terminalde bastirir
    '''

    print_warn("handle auth challenge starting")
    challenge = {}
    print_ok(indy_config['steward_did'])
    challenge['sdid'] = indy_config['steward_did']

    # 1. generate nonce
    nonce = secrets.token_hex(16)
    print_ok(f"nonce: {nonce}, len: {len(nonce)}")
    challenge['nonce'] = nonce
    app['nonces'][nonce] = False

    qr = pyqrcode.create(json.dumps(challenge), version=8)
    print(qr.terminal(quiet_zone=1))

    return json_response(challenge)
     



async def handle_auth_response(request):
    '''
    responese
    {
        sender_did: "sender did"
        reponse_msg: "authencrypted_base64 encoded message"
    }

    POST /auth/response
        - ozhan agent hazirladigi response' i buraya gonderir
        - daha sonra kullanmak uzere jwt tokenini alir.
    '''

    print_warn("handle auth response starting")
    wallet_handle = app['wallet_handle']
    pool_handle = app['pool_handle']

    # 1. parse request

    post_body = await request.read()
    response = json.loads(post_body)
    print_warn(post_body)
    client_did = response['sender_did']

    # client_fetched_verkey = await did.key_for_did(pool_handle, wallet_handle, client_did)
    response_msg_b64 = response['response_msg']
    response_msg = base64.b64decode(response_msg_b64)

    # 2. validate/decrypt auth encrypt message

    steward_did = indy_config['steward_did']
    steward_verkey = await did.key_for_local_did(wallet_handle, steward_did)
    print_warn(f"steward verkey: {steward_verkey}")

    client_fetched_verkey, msg = await crypto.auth_decrypt(wallet_handle, steward_verkey, response_msg)
    print_ok(f"client_fetched_verkey: {client_fetched_verkey}")
    print_ok(f"msg: {msg}")
    nonce = msg.decode('utf-8')

    if nonce in app['nonces']:
        print_ok('nonce gecerli jwt donuluyor')

        # 4. generate jwt with hs256 
        payload = {'iss': 'did:sov:' + client_did}
        print_ok(f"payload: {payload}")
        encoded_jwt = jwt.encode(payload, 'secret', algorithm="HS256")
        print_ok(f"jwt: {encoded_jwt}")

        # 5. return jwt with jwe
        jwt_jwe = await crypto.pack_message(wallet_handle, encoded_jwt, [client_fetched_verkey], steward_verkey)
        print(jwt_jwe)

        # 6. create and return response
        jwt_resp = {}
        jwt_resp['jwe'] = jwt_jwe.decode('utf-8')
        print_ok(f"jwt \n{json.dumps(jwt_resp)}")
        return Response(text=jwt_jwe.decode('utf-8'))

    else:
        print_fail('nonce yok! unauth donuluyor')
        return web.Response(status=401)



if __name__ == '__main__':
    PORT = 3000

    routes = []
    routes.append(web.get('/availablecreds', handle_available_creds))
    routes.append(web.get('/credoffer/{cred_def_id}', handle_cred_offer))
    routes.append(web.post('/credrequest', handle_cred_request))
    routes.append(web.get('/auth/challenge', handle_auth_challenge))
    routes.append(web.post('/auth/response', handle_auth_response))

    app = web.Application()
    app.add_routes(routes)
    app['issued_credentials'] = {}
    app['nonces'] = {}

    app.on_shutdown.append(on_shutdown)
    app.on_startup.append(on_startup)

    web.run_app(app, port=PORT)
