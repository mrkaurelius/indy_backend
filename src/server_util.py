"""
indy helper, daha iyi bir isim bulunabilir.
"""

import asyncio
from ctypes import c_longlong
import json
import pprint
import logging
import argparse
import pprint

from indy import pool, ledger, wallet, did
from indy.error import IndyError, ErrorCode, PaymentOperationNotSupportedError

from utils import get_pool_genesis_txn_path, PROTOCOL_VERSION

logging.basicConfig(level=logging.INFO)


async def start_indy(indy_config):
    """
    poola baglanir, walleti acar, handle leriniri return eder

    :return: pool_handle, wallet_handle
    """

    await pool.set_protocol_version(PROTOCOL_VERSION)

    config = indy_config
    wallet_handle, pool_handle = None, None
    try:
        logging.info("Openging pool ledger and wallet")
        pool_handle = await pool.open_pool_ledger(config_name=config["pool_name"], config=None)
        wallet_handle = await wallet.open_wallet(str(config["wallet_config"]), str(config["wallet_credentials"]))
    except IndyError as e:
        logging.error(e.message)

    return int(pool_handle), int(wallet_handle)


async def stop_indy(pool_handle, wallet_handle):
    """
    pool'u ve wallet'i gracefully sekilde kapatir.
    """

    try:
        logging.info("Stopping indy, closing wallet and pool")
        await wallet.close_wallet(wallet_handle)
        await pool.close_pool_ledger(pool_handle)
    except IndyError as e:
        logging.error("Error occured: {}".format(e.message))


async def init_indy():
    """
    her ledgerde bir kere kullanilmali, start_indy ile karistirma
    wallet create eder, serverin didini trust anchor olarak ekler
    yaptigi islerin bir json dosyasina kayit eder, 
    """

    indy_config = {}
    pool_name = 'sandbox'
    indy_config["pool_name"] = pool_name
    genesis_file_path = get_pool_genesis_txn_path(pool_name)
    wallet_config = json.dumps({"id": "server_wallet"})
    wallet_credentials = json.dumps({"key": "very_secret_key"})
    indy_config["wallet_config"] = wallet_config
    indy_config["wallet_credentials"] = wallet_credentials

    try:
        await pool.set_protocol_version(PROTOCOL_VERSION)

        logging.info("Creates a new local pool ledger configuration")
        pool_config = json.dumps({'genesis_txn': str(genesis_file_path)})

        try:
            await pool.create_pool_ledger_config(config_name=pool_name, config=pool_config)
        except IndyError as ex:
            if ex.error_code == ErrorCode.PoolLedgerConfigAlreadyExistsError:
                logging.warning("Pool ledger config already exists")
                pass

        logging.info("Openging pool ledger")
        pool_handle = await pool.open_pool_ledger(config_name=pool_name, config=None)

        logging.info("Creating new secure wallet for server")
        try:
            await wallet.create_wallet(wallet_config, wallet_credentials)
        except IndyError as ex:
            if ex.error_code == ErrorCode.WalletAlreadyExistsError:
                logging.warning(
                    "wallet already exists  {}".format(wallet_config))
                pass

        logging.info("Open wallet and get handle from libindy")
        wallet_handle = await wallet.open_wallet(wallet_config, wallet_credentials)

        steward_seed = '000000000000000000000000Steward1'
        did_json = json.dumps({'seed': steward_seed})
        steward_did, steward_verkey = await did.create_and_store_my_did(wallet_handle, did_json)
        indy_config["steward_did"] = steward_did
        indy_config["steward_verkey"] = steward_verkey
        logging.info('Steward DID: {}, Steward Verkey: {}'.format(
            steward_did, steward_verkey))

        logging.info("Generating and storing trust anchor DID and verkey")
        trust_anchor_seed = '000000000000000ServerTrusteeSeed'
        trust_anchor_did_json = json.dumps({'seed': trust_anchor_seed})
        trust_anchor_did, trust_anchor_verkey = None, None
        try:
            trust_anchor_did, trust_anchor_verkey = await did.create_and_store_my_did(wallet_handle, trust_anchor_did_json)
        except IndyError as e:
            logging.warning('Error occurred: {}'.format(e.message))

        logging.info("Trust anchor seed: {}, Trust anchor DID: {}, Trusf anchor Verkey: {}".format(
            trust_anchor_seed, trust_anchor_did, trust_anchor_verkey))
        indy_config["trust_anchor_seed"] = trust_anchor_seed
        indy_config["trust_anchor_verkey"] = trust_anchor_verkey
        indy_config["trust_anchor_did"] = trust_anchor_did

        # set did metadata
        try:
            await did.set_did_metadata(wallet_handle, trust_anchor_did, "trust anchor did")
            await did.set_did_metadata(wallet_handle, steward_did, "steward did")
        except IndyError as e:
            logging.warning('Error occurred: {}'.format(e.message))

        logging.info("Building NYM request to add Trust Anchor to the ledger")
        nym_transaction_request = await ledger.build_nym_request(submitter_did=steward_did,
                                                                 target_did=trust_anchor_did,
                                                                 ver_key=trust_anchor_verkey,
                                                                 alias=None,
                                                                 role='TRUST_ANCHOR')

        logging.info("NYM transaction request: {}".format(
            json.loads(nym_transaction_request)))
        logging.info("Sending NYM request to the ledger")
        nym_transaction_response = await ledger.sign_and_submit_request(pool_handle=pool_handle,
                                                                        wallet_handle=wallet_handle,
                                                                        submitter_did=steward_did,
                                                                        request_json=nym_transaction_request)
        logging.info("NYM transaction response: {}".format(
            nym_transaction_response))

        with open('indy_config.json', 'w', encoding='utf-8') as f:
            json.dump(indy_config, f, ensure_ascii=False, indent=4)

        # add trust anchor did to wallet

        logging.info("Closing wallet and pool")
        await wallet.close_wallet(wallet_handle)
        await pool.close_pool_ledger(pool_handle)

    except IndyError as e:
        logging.warning('Error occurred: %s' % e.message)



"""
indy server kurulumu icin script
"""
if __name__ == '__main__':
    pp = pprint.PrettyPrinter(indent=4)
    parser = argparse.ArgumentParser()
    parser.add_argument('--init', action='store_true', help='init indy')
    parser.add_argument('--remove-config',
                        action='store_true', help='init indy')
    args = parser.parse_args()
    print(args)

    if args.init:
        print("Indy configi init ediliyor")
        loop = asyncio.get_event_loop()
        loop.run_until_complete(init_indy())
        loop.close()
        print("Indy configi init edildi")
    elif args.remove_config:
        print("Indy configi siliniyor")
        # TODO
        # remove config
    else:
        print("yapacak birsey yok")
