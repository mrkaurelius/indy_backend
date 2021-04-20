"""
aiohttp kullanan server modülü
"""

import asyncio
import json
import pprint
import logging

from aiohttp import web
from aiohttp.web_app import Application

from indy import pool, ledger, wallet, did
from indy.error import IndyError, ErrorCode

from indy_helper import start_indy, stop_indy

logging.basicConfig(level=logging.DEBUG)

# kinda globals
pool_handle = None
wallet_handle = None

# load indy config from file
indy_config = None
with open("indy_config.json") as config_json: 
    indy_config = json.load(config_json)
    logging.info("indy_config: {}".format(indy_config))


async def handle(request):
    # name = request.match_info.get('name', "Anonymous")
    # text = "Hello, " + name
    # return web.Response(text=text)
    pass


# gracefull shutdown
async def on_shutdown(app):
    await stop_indy(app["pool_handle"], app["wallet_handle"])


async def on_startup(app):
    print("Starting Indy")
    pool_handle, wallet_handle = await start_indy(indy_config) 
    app["pool_handle"] = pool_handle
    app["wallet_handle"] = wallet_handle
    # print(pool_handle, wallet_handle)
    print(await did.list_my_dids_with_meta(wallet_handle))
    
    # TODO
    # print cred defs


# TODO
# GET /credoffer


# TODO
# POST /credrequest 


# TODO
# GET /cred/<UUID>


if __name__ == '__main__':
    app = web.Application()
    app.add_routes([web.get('/', handle),
                    web.get('/{name}', handle)])

    app.on_shutdown.append(on_shutdown)
    app.on_startup.append(on_startup)
    
    web.run_app(app)