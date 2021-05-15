"""
aiohttp kullanan server modülü

Notlar
- jsonlari indy ye vermeden once anlayacagi hale getir.
"""

from re import A
import pyqrcode
import asyncio
import json
import pprint
import logging

from aiohttp import web
from aiohttp.web_app import Application

from indy import anoncreds, pool, ledger, wallet, did
from indy.error import IndyError, ErrorCode
from requests.api import post

from utils import get_indy_config
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
    # await anoncreds.issuer_create_credential(app['wallet_handle'], c )
    cred_req_ret = {}
    cred_req_ret['cred_json'] = cred_json
    return web.json_response(cred_req_ret)


if __name__ == '__main__':
    PORT = 3000

    # load server_qr.json from file and show qr on terminal

    routes = []
    routes.append(web.get('/availablecreds', handle_available_creds))
    routes.append(web.get('/credoffer/{cred_def_id}', handle_cred_offer))
    routes.append(web.post('/credrequest', handle_cred_request))

    app = web.Application()
    app.add_routes(routes)
    app['issued_credentials'] = {}

    app.on_shutdown.append(on_shutdown)
    app.on_startup.append(on_startup)

    web.run_app(app, port=PORT)
