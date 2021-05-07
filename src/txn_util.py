"""
indy txn helper scripts, ledgerdegi txleri buradan gelistirlecek scriptler ile taramak mumkun, suan oncelik degil.
cred defler ve schemalar buradan cekilerbilir.w
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


indy_config = get_indy_config()
pool_handle = None
wallet_handle = None

async def main():
    pool_handle, wallet_handle = await start_indy(indy_config)   

    request = await ledger.build_get_txn_request(None, None, 1)
    print(request)
    response = await ledger.submit_request(pool_handle, request)
    parsed = json.loads(response)
    pp.pprint(parsed)

    await stop_indy(pool_handle, wallet_handle)

if __name__ == "__main__":
    pp = pprint.PrettyPrinter(indent=4)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
