import argparse
import asyncio
import json
from json.encoder import JSONEncoder
import logging
import pprint

from hashlib import sha256
from indy import pool, ledger, wallet, did, anoncreds
from indy.error import ErrorCode, IndyError

from schema_util import get_added_schemas, get_schema_defs
from server_util import start_indy, stop_indy
from credential_util import create_gvt_cred_values
from utils import get_indy_config
from utils import open_wallet, get_pool_genesis_txn_path, PROTOCOL_VERSION, print_fail, print_log, get_indy_config, print_ok, print_warn
from utils import print_fail, print_ok, print_warn
from utils import print_server_qr_terminal
from utils import read_minified_json_str
from utils import sha256_digest_hex


async def main():

    pass


if __name__ == "__main__":

    cred_values_json = create_gvt_cred_values("ahmet", "20", "male", "170")
    print(cred_values_json)

    # hash = sha256_digest_hex('deneme')
    # print(hash)

    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(main())
    pass
