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
from galaxy.models.pinnable import Account, NFTOwnership, Website, WebsiteTaskLog
from galaxy.utils.filters import format_bytes

engine = create_engine(
    config.database_url, pool_size=20, max_overflow=40, isolation_level="READ COMMITTED"
)
Session = scoped_session(sessionmaker(bind=engine))
r = redis.Redis(host=config.redis_host, port=config.redis_port, db=0)
q = Queue("pinnable", connection=r, default_timeout=1800)


def test_clean_up(website_id: int):
    session = Session()
    website = session.query(Website).filter(Website.id == website_id).first()
    if website is not None:
        event = f"Failed to resolve ENS name: {website.name}"
        tasklog = (
            session.query(WebsiteTaskLog)
            .filter(
                WebsiteTaskLog.website_id == website.id, WebsiteTaskLog.event == event
            )
            .all()
        )
        for log in tasklog:
            print(f"🧹 Cleaning up {website.name} - {log.event}")


def clean_up():
    session = Session()
    websites = session.query(Website).all()

    deleted_duplicated_resolved_to_ipns = 0
    deleted_duplicated_pinned = 0
    deleted_failed_to_resolve_ens = 0

    for website in websites:
        print(f"🧹 Cleaning up logs for {website.name}")
        pinned = []
        resolved_to_ipns = []
        logs = (
            session.query(WebsiteTaskLog)
            .filter(WebsiteTaskLog.website_id == website.id)
            .all()
        )
        for log in logs:
            event = str(log.event)

            # Resolved to IPNS
            if "Resolved to IPNS" in event:
                if log.ipns not in resolved_to_ipns:
                    # print(f"🌐 Resolved {website.name} to {log.ipns}")
                    resolved_to_ipns.append(log.ipns)
                else:
                    print(f"😚 {website.name} is already resolved to {log.ipns}")
                    session.delete(log)
                    session.commit()
                    deleted_duplicated_resolved_to_ipns += 1

            # Pinned
            if log.event == "Pinned":
                if log.cid not in pinned:
                    # print(f"📌 Pinned {website.name} to {log.cid}")
                    pinned.append(log.cid)
                else:
                    print(f"😚 {website.name} is already pinned to {log.cid}")
                    session.delete(log)
                    session.commit()
                    deleted_duplicated_pinned += 1

            # Failed to resolve ENS name
            if "Failed to resolve ENS name" in event:
                session.delete(log)
                session.commit()
                deleted_failed_to_resolve_ens += 1

    print("🧹 Cleaned up WebsiteTaskLogs")

    print("Deleted duplicated `Resolve to IPNS`:", deleted_duplicated_resolved_to_ipns)
    print("Deleted duplicated `Pinned`:", deleted_duplicated_pinned)
    print("Deleted `Failed to resolve ENS name`:", deleted_failed_to_resolve_ens)

    session.close()


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
        provider = "https://eth.llamarpc.com"
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
        print(f"⭐️ DWB balance for address {eth_address}: {dwb_balance}")

        account.dwb_balance = dwb_balance

        # Check ENS token balance

        ens_token_address = Web3.to_checksum_address(
            "0xc18360217d8f7ab5e7c516566761ea12ce7f9d72"
        )
        ens_abi = [
            {
                "constant": True,
                "inputs": [{"name": "account", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "", "type": "uint256"}],
                "type": "function",
            }
        ]
        ens_contract = w3.eth.contract(address=ens_token_address, abi=ens_abi)

        ens_balance = ens_contract.functions.balanceOf(eth_address).call() / 10**18
        print(f"🔮 ENS balance for address {eth_address}: {ens_balance}")

        aave_ens_token_address = Web3.to_checksum_address(
            "0x545bD6c032eFdde65A377A6719DEF2796C8E0f2e"
        )
        aave_ens_contract = w3.eth.contract(address=aave_ens_token_address, abi=ens_abi)
        aave_ens_balance = (
            aave_ens_contract.functions.balanceOf(eth_address).call() / 10**18
        )
        print(f"🔮 AAVE ENS balance for address {eth_address}: {aave_ens_balance}")

        account.ens_balance = ens_balance + aave_ens_balance

        account.last_checked = int(time.time())
        session.commit()
    except Exception as e:
        print(e)
        print(f"🥲 Failed to check token balance for address {eth_address}")

    # Check if this address has any qualifying NFTs
    nft_collections = NFTOwnership.collab_nft_collections()
    for contract_address in nft_collections:
        collection_name = nft_collections[contract_address]
        token_ids = get_nft_token_ids(contract_address, account.address)
        for token_id in token_ids:
            chain = "ethereum"
            token = (
                session.query(NFTOwnership)
                .filter(
                    NFTOwnership.chain == chain,
                    NFTOwnership.contract == contract_address,
                    NFTOwnership.token_id == token_id,
                )
                .first()
            )
            if token is None:
                token = NFTOwnership()
                token.account_id = account.id
                token.chain = chain
                token.contract = contract_address
                token.token_id = token_id
                token.created = int(time.time())
                token.last_checked = int(time.time())
                session.add(token)
                session.commit()
            else:
                token.account_id = account.id
                token.last_checked = int(time.time())
                session.commit()
            print(f"🎨 Found {collection_name} #{token_id} for Account #{account.id}")

            image_url = get_nft_image_url(contract_address, token_id)
            if image_url is not None:
                token.image_url = image_url
                session.commit()
            else:
                print(
                    f"🥲 Failed to get image url for token {contract_address}-{token_id}"
                )

    session.close()


def get_nft_image_url(contract_address, token_id):
    base_url = f"https://api.opensea.io/api/v2/chain/ethereum/contract/{ contract_address }/nfts/{ token_id }"  # noqa
    headers = {"X-API-KEY": config.opensea_api_key}
    print(f"GET: {base_url}")

    response = requests.get(base_url, headers=headers, timeout=30)

    if response.status_code == 200:
        data = response.json()
        if "nft" in data and len(data["nft"]) > 0 and "image_url" in data["nft"]:
            return data["nft"]["image_url"]
    else:
        print(f"😖 Response failed: {response.status_code} - {response.text}")
    return None


def get_nft_token_ids(contract_address: str, wallet_address: str):
    nft_collections = NFTOwnership.collab_nft_collections()
    collection_name = nft_collections[contract_address.lower()]
    # Initialize Web3
    w3 = Web3(Web3.HTTPProvider("https://mainnet.gateway.tenderly.co"))
    contract_address = Web3.to_checksum_address(contract_address)

    # Define the filter parameters
    wallet_address_padded = wallet_address[2:]  # Remove '0x'
    wallet_address_padded = (
        "0" * (64 - len(wallet_address_padded)) + wallet_address_padded
    )
    wallet_address_padded = "0x" + wallet_address_padded  # Add '0x' back

    filter_params = {
        "fromBlock": "earliest",
        "toBlock": "latest",
        "address": contract_address,
        "topics": [None, None, wallet_address_padded],
    }

    # Get logs
    logs = w3.eth.get_logs(filter_params)
    print(f"🔎 Found {len(logs)} NFT transfer logs in {collection_name}")

    token_ids = []

    # Extract token IDs from logs
    for log in logs:
        if "topics" in log and len(log["topics"]) > 3:
            hex_str = log["topics"][3].hex()
            token_id = int(hex_str, 16)  # Convert hexadecimal to integer
            token_ids.append(token_id)

    return token_ids


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
    if website.kind == "IPNS":
        # Try resolve the IPNS name with IPFS API
        api_request = f"{config.ipfs_server}/api/v0/resolve?arg=/ipns/{website.name}&recursive=false"  # noqa
        print(f"POST: {api_request}")
        try:
            resp = requests.post(api_request, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                if "Path" in data:
                    path = data["Path"]
                    print(f"🌐 Resolved IPNS name {website.name} to IPFS path: {path}")
                    if path.startswith("/ipfs/"):
                        cid = path[6:]
                        if cid.endswith("/"):
                            cid = cid[:-1]
                        if website.last_known_ipns != website.name:
                            website.last_known_ipns = website.name
                        website.last_checked = int(time.time())
                    session.commit()
        except Exception as e:
            print(e)
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
                            create_tasklog_resolved_to_ipns(website.id, ipns)
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
                    create_tasklog_failed_to_resolve_ens(website.id)
            else:
                create_tasklog_failed_to_resolve_ens(website.id)
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


def create_tasklog_failed_to_resolve_ens(website_id: int):
    session = Session()
    website = session.query(Website).filter(Website.id == website_id).first()
    if website is None:
        print(f"😖 Website (id={website_id}) not found")
        session.close()
        return
    event = f"Failed to resolve ENS name: {website.name}"
    tasklog = (
        session.query(WebsiteTaskLog)
        .filter(WebsiteTaskLog.website_id == website.id, WebsiteTaskLog.event == event)
        .first()
    )
    if tasklog is None:
        tasklog = WebsiteTaskLog()
        tasklog.website_id = website.id
        tasklog.event = event
        tasklog.icon = "questionmark.circle.fill"
        tasklog.created = int(time.time())
        session.add(tasklog)
        session.commit()
        print(f"🧞‍♂️ Created task log for {website.name} - {event}")
    else:
        tasklog.created = int(time.time())
        session.commit()
        print(f"♻️ Task log found for {website.name} - {event}")
    session.close()


def create_tasklog_resolved_to_ipns(website_id: int, ipns: str):
    session = Session()
    website = session.query(Website).filter(Website.id == website_id).first()
    if website is None:
        print(f"😖 Website (id={website_id}) not found")
        session.close()
        return
    event = "Resolved to IPNS"
    tasklog = (
        session.query(WebsiteTaskLog)
        .filter(
            WebsiteTaskLog.website_id == website.id,
            WebsiteTaskLog.event == event,
            WebsiteTaskLog.ipns == ipns,
        )
        .order_by(WebsiteTaskLog.created.desc())
        .first()
    )
    if tasklog is None:
        tasklog = WebsiteTaskLog()
        tasklog.website_id = website.id
        tasklog.event = event
        tasklog.icon = "network"
        tasklog.ipns = ipns
        tasklog.created = int(time.time())
        session.add(tasklog)
        session.commit()
        print(f"🌐 Created task log for {website.name} - {event} - {ipns}")
    else:
        tasklog.created = int(time.time())
        session.commit()
        print(f"♻️ Task log found for {website.name} - {event} - {ipns}")
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
                    session.expire_all()
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
                        print(f"🈳 Task log not found for {website.name} - {cid}")
                        tasklog = WebsiteTaskLog()
                        tasklog.website_id = website.id
                        tasklog.event = "Pinned"
                        tasklog.icon = "checkmark.circle.fill"
                        tasklog.cid = cid
                        tasklog.created = int(time.time())
                        session.add(tasklog)
                        cid_tasklog = tasklog
                    else:
                        print(
                            f"♻️ A recent task log is found for {website.name} - {cid}"
                        )
                        recent_tasklog.created = int(time.time())
                        cid_tasklog = recent_tasklog

                    website.last_known_cid = cid
                    website.last_pinned = int(time.time())

                    if website.subname is not None:
                        q.enqueue(update_website_subname_cid, website.id, cid)

                    q.enqueue(fetch_website_info, website.id)
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


def fetch_website_info(website_id: int):
    session = Session()
    website = session.query(Website).filter(Website.id == website_id).first()
    if website is None:
        print(f"😖 Website (id={website_id}) not found")
        session.close()
        return
    if website.last_known_cid is not None:
        # fetch avatar.png
        avatar_request = (
            f"{config.ipfs_objects_gateway}/ipfs/{website.last_known_cid}/avatar.png"
        )
        resp = requests.get(avatar_request, timeout=30)
        if resp.status_code == 200:
            website.image_url = f"/ipfs/{website.last_known_cid}/avatar.png"
            session.commit()
        # fetch planet.json
        info_request = f"{config.ipfs_objects_gateway}/ipfs/{website.last_known_cid}/planet.json"  # noqa
        resp = requests.get(info_request, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            if "name" in data:
                if website.title != data["name"]:
                    print(
                        f"📝 Updated website title for {website.name} to {data['name']}"
                    )
                    website.title = data["name"]
            session.commit()
    session.close()


def update_website_subname_cid(website_id: int, cid: str):
    session = Session()
    website = session.query(Website).filter(Website.id == website_id).first()
    if website is None:
        print(f"😖 Website (id={website_id}) not found")
        session.close()
        return
    if website.subname is not None and website.subname != "":
        # Write CID to Namestone
        subname = website.subname
        address = website.account.address
        cid = cid
        namestone_api = "https://namestone.xyz/api/public_v1/set-name"
        headers = {"Authorization": config.namestone_api_token}
        data = {
            "domain": config.namestone_domain,
            "name": subname,
            "address": address,
            "contenthash": "ipfs://" + cid,
        }
        try:
            requests.post(namestone_api, headers=headers, json=data, timeout=30)
        except Exception as e:
            print("🗿 Namestone API error: ", e)
    session.close()


def prewarm_cid(cid: str):
    # Prewarm the CID
    for gateway in config.prewarm_gateways:
        prewarm_request = f"{gateway}/ipfs/{cid}"
        print(f"🔥 Prewarming {prewarm_request}")
        try:
            resp = requests.get(prewarm_request, timeout=30)
            if resp.status_code == 200:
                print(f"🔥 Prewarmed {prewarm_request}")
            else:
                print(f"😖 Failed to prewarm {prewarm_request}")
        except Exception as e:
            print(e)
            print(f"😖 Failed to prewarm {prewarm_request}")
