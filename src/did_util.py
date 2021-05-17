"""
Indy SDK DID helper.

# TODO
"""

import argparse
import asyncio

# TODO

async def add_did_to_ledger(seed):
    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--add-did', help='add did to ledger')
    args = parser.parse_args()
    loop = asyncio.get_event_loop()