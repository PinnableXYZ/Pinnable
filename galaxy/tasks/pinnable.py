#!/usr/bin/env python3

import time
import uuid

import redis
import requests
from rq import Queue
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from web3 import Web3

import config
from galaxy.models.pinnable import Account, Website, WebsiteTaskLog
from galaxy.utils.filters import format_bytes

engine = create_engine(config.database_url, pool_size=20, max_overflow=40)
Session = scoped_session(sessionmaker(bind=engine))
r = redis.Redis(host=config.redis_host, port=config.redis_port, db=0)
q = Queue("pinnable", connection=r, default_timeout=1800)


def resolve_address(account_id: int):
    session = Session()
    account = session.query(Account).filter(Account.id == account_id).first()
    if account is None:
        print(f"😖 Account (id={account_id}) not found")
        session.close()
        return
    api_request = f"https://api.ensideas.com/ens/resolve/{account.address}"
    try:
        resp = requests.get(api_request, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            if "name" in data and len(data["name"]) > 0:
                ens = data["name"]
                print(f"🌐 Resolved {account.address} to ENS: {ens}")
                if account.ens != ens:
                    account.ens = ens
                    session.commit()
            if "avatar" in data and len(data["avatar"]) > 0:
                avatar = data["avatar"]
                print(f"🧞‍♂️ {account.address} has avatar: {avatar}")
                if account.avatar != avatar:
                    account.avatar = avatar
                    session.commit()
            return
        print(f"😖 Failed to resolve {account.address} to ENS")
    except Exception as e:
        print(e)
        print(f"😖 Failed to resolve {account.address} to ENS")


def check_account(account_id: int):
    session = Session()
    account = session.query(Account).filter(Account.id == account_id).first()
    if account is None:
        print(f"😖 Account (id={account_id}) not found")
        session.close()
        return
    if account.address is None:
        print(f"😖 Account (id={account_id}) has no address")
        session.close()
        return
    # Check if the account has any Planetable tokens in the JBTokenStore:
    # 0x6FA996581D7edaABE62C15eaE19fEeD4F1DdDfE7
    # projectId 471

    q.enqueue(resolve_address, account_id)

    try:
        # Set up the Ethereum provider
        provider = (
            "https://ethereum.publicnode.com"  # Replace with your Infura Project ID
        )
        w3 = Web3(Web3.HTTPProvider(provider))

        # Token contract and Ethereum address
        JBTokenStore_address = Web3.to_checksum_address(
            "0x6FA996581D7edaABE62C15eaE19fEeD4F1DdDfE7"
        )
        eth_address = Web3.to_checksum_address(account.address)

        # ABI for the JBTokenStore balanceOf function
        token_store_abi = [
            {
                "constant": True,
                "inputs": [
                    {"name": "_holder", "type": "address"},
                    {"name": "_projectId", "type": "uint256"},
                ],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function",
            }
        ]

        # Create contract instance
        JBTokenStore_contract = w3.eth.contract(
            address=JBTokenStore_address, abi=token_store_abi
        )

        # Fetch the token balance for projectId 471 (https://juicebox.money/@pinnable)
        balance = JBTokenStore_contract.functions.balanceOf(eth_address, 471).call()

        dwb_balance = balance / 10**18
        print(f"⭐️ Token balance for address {eth_address}: {dwb_balance}")

        account.dwb_balance = dwb_balance
        account.last_checked = int(time.time())
        session.commit()
    except Exception as e:
        print(e)
        print(f"🥲 Failed to check token balance for address {eth_address}")

    session.close()


def check_website(website_id: int):
    session = Session()
    website = session.query(Website).filter(Website.id == website_id).first()
    if website is None:
        print(f"Website (id={website_id}) not found")
        session.close()
        return
    if website.pin_api_uuid is None or len(website.pin_api_uuid) == 0:
        website.pin_api_uuid = str(uuid.uuid4())
        session.commit()
    if website.kind == "ENS":
        # Try resolve the ENS name with IPFS API
        api_request = f"{config.ipfs_server}/api/v0/resolve?arg=/ipns/{website.name}&recursive=false"  # noqa
        print(f"POST: {api_request}")
        try:
            resp = requests.post(api_request, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                if "Path" in data:
                    path = data["Path"]
                    print(f"🌐 Resolved ENS name {website.name} to IPFS path: {path}")
                    if path.startswith("/ipns/"):
                        ipns = path[6:]
                        if ipns.endswith("/"):
                            ipns = ipns[:-1]
                        if website.last_known_ipns != ipns:
                            tasklog = WebsiteTaskLog()
                            tasklog.website_id = website.id
                            tasklog.event = "Resolved to IPNS"
                            tasklog.icon = "network"
                            tasklog.ipns = ipns
                            tasklog.created = int(time.time())
                            session.add(tasklog)

                            website.last_known_ipns = ipns
                        website.last_checked = int(time.time())
                    session.commit()
                    if website.last_pinned is None:
                        # Pin the website
                        q.enqueue(pin_website, website.id)
                    else:
                        if website.seconds_since(website.last_pinned) > 60:
                            # Pin the website
                            q.enqueue(pin_website, website.id)
                else:
                    tasklog = WebsiteTaskLog()
                    tasklog.website_id = website.id
                    tasklog.event = f"Failed to resolve ENS name: {website.name}"
                    tasklog.icon = "questionmark.circle.fill"
                    tasklog.created = int(time.time())
                    session.add(tasklog)
                    session.commit()
                    print(f"😖 Failed to resolve ENS name: {website.name}")
            else:
                tasklog = WebsiteTaskLog()
                tasklog.website_id = website.id
                tasklog.event = f"😖 Failed to resolve ENS name: {website.name}"
                tasklog.icon = "questionmark.circle.fill"
                tasklog.created = int(time.time())
                session.add(tasklog)
                session.commit()
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
                    print(
                        f"💾 Size of {website.name} / {website.last_known_cid}: {format_bytes(website.size)}"  # noqa
                    )
        except Exception as e:
            print(e)
    session.close()


def pin_website(website_id: int):
    session = Session()
    website = session.query(Website).filter(Website.id == website_id).first()
    if website is None:
        print(f"😖 Website (id={website_id}) not found")
        session.close()
        return
    # call ipfs pin add
    pin_request = f"{config.ipfs_server}/api/v0/pin/add?arg={website.ipfs_path}"
    print(f"🪃  POST: {pin_request}")
    try:
        resp = requests.post(pin_request, timeout=120)
        if resp.status_code == 200:
            data = resp.json()
            if "Pins" in data:
                # Website is pinned
                cid = data["Pins"][0]
                cid_tasklog = None
                if website.last_known_cid != cid:
                    print(f"📌 Pinned {website.name} to {cid}")
                    recent_tasklog = (
                        session.query(WebsiteTaskLog)
                        .filter(
                            WebsiteTaskLog.website_id == website.id,
                            WebsiteTaskLog.event == "Pinned",
                            WebsiteTaskLog.cid == cid,
                        )
                        .order_by(WebsiteTaskLog.created.desc())
                        .first()
                    )
                    if recent_tasklog is None:
                        tasklog = WebsiteTaskLog()
                        tasklog.website_id = website.id
                        tasklog.event = "Pinned"
                        tasklog.icon = "checkmark.circle.fill"
                        tasklog.cid = cid
                        tasklog.created = int(time.time())
                        session.add(tasklog)
                        cid_tasklog = tasklog
                    else:
                        recent_tasklog.created = int(time.time())
                        cid_tasklog = recent_tasklog

                    website.last_known_cid = cid
                    website.last_pinned = int(time.time())
                else:
                    print(f"😚 {website.name} is already pinned to {cid}")
                    website.last_pinned = int(time.time())
                session.commit()
                stat_request = f"{config.ipfs_server}/api/v0/files/stat?arg=/ipfs/{website.last_known_cid}"  # noqa
                resp = requests.post(stat_request, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    if "CumulativeSize" in data:
                        website.size = data["CumulativeSize"]
                        if cid_tasklog:
                            cid_tasklog.size = website.size
                        session.commit()
            else:
                # Not pinned
                pass
    except Exception as e:
        print(e)
    session.close()
