#!/usr/bin/env python3

import time

import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from web3 import Web3

import config
from galaxy.models.pinnable import Account, Website

engine = create_engine(config.database_url, pool_size=20, max_overflow=40)
Session = scoped_session(sessionmaker(bind=engine))


def check_account(account_id: int):
    session = Session()
    account = session.query(Account).filter(Account.id == account_id).first()
    if account is None:
        print(f"Account (id={account_id}) not found")
        session.close()
        return
    if account.address is None:
        print(f"Account (id={account_id}) has no address")
        session.close()
        return
    # Check if the account has any tokens with dwb contract:
    # 0x36787480031d8760815b961a5D689B505E8f6cB7

    try:
        # Set up the Ethereum provider
        provider = (
            "https://ethereum.publicnode.com"  # Replace with your Infura Project ID
        )
        w3 = Web3(Web3.HTTPProvider(provider))

        # Token contract and Ethereum address
        token_contract_address = Web3.to_checksum_address(
            "0x36787480031d8760815b961a5D689B505E8f6cB7"
        )
        eth_address = Web3.to_checksum_address(account.address)

        # ABI for the ERC20 standard (minimal version)
        erc20_abi = [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function",
            }
        ]

        # Create contract instance
        token_contract = w3.eth.contract(address=token_contract_address, abi=erc20_abi)

        # Fetch the token balance
        balance = token_contract.functions.balanceOf(eth_address).call()

        dwb_balance = balance / 10**18
        print(f"Token balance for address {eth_address}: {dwb_balance}")

        account.dwb_balance = dwb_balance
        account.last_checked = int(time.time())
        session.commit()
    except Exception as e:
        print(f"Failed to check token balance for address {eth_address}")

    session.close()


def check_website(website_id: int):
    session = Session()
    website = session.query(Website).filter(Website.id == website_id).first()
    if website is None:
        print(f"Website (id={website_id}) not found")
        session.close()
        return
    if website.kind == "ENS":
        # Try resolve the ENS name with IPFS API
        api_request = f"{config.ipfs_server}/api/v0/resolve?arg=/ipns/{website.name}&recursive=false"
        print(f"POST: {api_request}")
        try:
            resp = requests.post(api_request, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                if "Path" in data:
                    path = data["Path"]
                    print(f"Resolved ENS name {website.name} to IPFS path: {path}")
                    if path.startswith("/ipns/"):
                        website.last_known_ipns = path[6:]
                        website.last_checked = int(time.time())
                    session.commit()
                else:
                    print(f"Failed to resolve ENS name: {website.name}")
        except Exception as e:
            print(e)
    if website.last_known_cid is not None:
        api_request = (
            f"{config.ipfs_server}/api/v0/files/stat?arg=/ipfs/{website.last_known_cid}"
        )
        print(f"POST: {api_request}")
        try:
            resp = requests.post(api_request, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                if "CumulativeSize" in data:
                    website.size = data["CumulativeSize"]
                    website.last_checked = int(time.time())
                    session.commit()
                    print(f"Size of {website.name} / {website.last_known_cid}: {website.size}")
        except Exception as e:
            print(e)
    session.close()


def pin_website(website_id: int):
    session = Session()
    website = session.query(Website).filter(Website.id == website_id).first()
    if website is None:
        print(f"Website (id={website_id}) not found")
        session.close()
        return
    # call ipfs pin add
    pin_request = f"{config.ipfs_server}/api/v0/pin/add?arg={website.ipfs_path}"
    try:
        resp = requests.post(pin_request, timeout=3600)
        if resp.status_code == 200:
            data = resp.json()
            if "Pins" in data:
                # Website is pinned
                cid = data["Pins"][0]
                website.last_known_cid = cid
                website.last_pinned = int(time.time())
                session.commit()
            else:
                # Not pinned
                pass
    except Exception as e:
        print(e)
    session.close()
