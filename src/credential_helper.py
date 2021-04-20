"""
Indy SDK crendential helper.

Notlar:
credential definitionlarini ledgere eklemekte zorluk cekiyorum.
Zaten credential definition'u ledgerde olmak zorunda degil.
"""

import asyncio
import json
import pprint
import logging

from indy import pool, ledger, wallet, did, anoncreds
from indy.error import ErrorCode, IndyError
from indy_helper import start_indy, stop_indy

from utils import open_wallet, get_pool_genesis_txn_path, PROTOCOL_VERSION, print_log

logging.basicConfig(level=logging.DEBUG)

# load indy config
indy_config = None
with open("indy_config.json") as config_json:
    indy_config = json.load(config_json)
    logging.info("indy_config: {}".format(indy_config))

pool_handle, wallet_handle = None, None


# TODO logify 
# TODO indy ledger error handling
# TODO parameterise
# Baya oynama yaptim bastan gozden gecir.

async def add_credential_definition():
    """
    ledgere scheme ekler, issuera credential definitionu ekler.
    mukerrer calistiginda UnauthorizedClientRequest hatasi veriyor
    """

    steward_did = indy_config["steward_did"]
    trust_anchor_did = indy_config["trust_anchor_did"]
    logging.info("trust anchor did {}, steward did: {}".format(trust_anchor_did, steward_did))

    schema = {
        'name': 'gvt',
        'version': '1.0',
        'attributes': '["age", "sex", "height", "name"]'
    }
    issuer_schema_id, issuer_schema_json = await anoncreds.issuer_create_schema(steward_did,
                                                                                schema['name'],
                                                                                schema['version'],
                                                                                schema['attributes'])
    print_log('Schema: ')
    pprint.pprint(issuer_schema_json)

    # 9.
    print_log('\n9. Build the SCHEMA request to add new schema to the ledger\n')
    schema_request = await ledger.build_schema_request(steward_did, issuer_schema_json)
    print_log('Schema request: ')
    pprint.pprint(json.loads(schema_request))

    # 10.
    print_log('\n10. Sending the SCHEMA request to the ledger\n')
    schema_response = \
        await ledger.sign_and_submit_request(pool_handle,
                                             wallet_handle,
                                             steward_did,
                                             schema_request)
    print_log('Schema response:')
    pprint.pprint(json.loads(schema_response))

    # credential definition
    print_log('\n11. Creating and storing Credential Definition using anoncreds as Trust Anchor, for the given Schema\n')
    cred_def_tag = 'TAG1'
    cred_def_type = 'CL'
    cred_def_config = json.dumps({"support_revocation": False})

    (cred_def_id, cred_def_json) = \
        await anoncreds.issuer_create_and_store_credential_def(wallet_handle,
                                                               trust_anchor_did,
                                                               issuer_schema_json,
                                                               cred_def_tag,
                                                               cred_def_type,
                                                               cred_def_config)
    print_log('Credential definition: ')
    pprint.pprint(json.loads(cred_def_json))
    print(cred_def_id)

    cred_def_ids = []
    cred_def_ids.append(cred_def_id)

    with open('cred_defs.json', 'w', encoding='utf-8') as f:
        json.dump(cred_def_ids, f, ensure_ascii=False, indent=4)
    
    # TODO
    # publish credential definition to ledger
    # calistiramadim.
    # cred_def_data = json.loads(cred_def_json)
    # cred_def_data_str = json.dumps(cred_def_data)
    # cred_def_request = await ledger.build_cred_def_request(trust_anchor_did, cred_def_data_str)
    # cred_def_res = await ledger.sign_and_submit_request(pool_handle, wallet_handle, trust_anchor_did, cred_def_request)
    # print(cred_def_res)

# TODO
# open server wallet and list credential offers
# indy cli ile wallet incelenebilir.
async def list_cred_offers(arg):
    pass



# TODO
# clify
if __name__ == '__main__':
    print("Starting Indy")
    loop = asyncio.get_event_loop()
    pool_handle, wallet_handle = loop.run_until_complete(
        start_indy(indy_config))

    # add credential definition
    loop.run_until_complete(add_credential_definition())

    print("Stoping Indy")
    loop.run_until_complete(stop_indy(pool_handle, wallet_handle))
