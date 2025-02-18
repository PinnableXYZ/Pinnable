#!/usr/bin/env python3

import time
import uuid
from typing import Any

import pylibmc
import redis
import requests
import sqlalchemy

import config
from galaxy.models.pinnable import Account, CIDObject, Website, WebsiteTaskLog


class PinnableMixin(object):
    session: sqlalchemy.orm.session.Session
    mc: pylibmc.Client
    r: redis.Redis
    current_user: Account
    request: Any
    values: dict[str, Any]

    def get_account(self, address: str):
        account = (
            self.session.query(Account)
            .filter(Account.address == address.lower())
            .first()
        )
        return account

    def get_account_by_id(self, account_id: int):
        account = self.session.query(Account).filter(Account.id == account_id).first()
        return account

    def create_account(self, address: str):
        account = Account()
        account.address = address.lower()
        account.created = int(time.time())
        self.session.add(account)
        self.session.commit()
        return account

    def update_account_websites_order_by(self, account_id: int, order_by: str):
        account = self.get_account_by_id(account_id)
        if account:
            if account.websites_order_by != order_by:
                account.websites_order_by = order_by
                self.session.commit()

    def update_account_objects_order_by(self, account_id: int, order_by: str):
        account = self.get_account_by_id(account_id)
        if account:
            if account.objects_order_by != order_by:
                account.objects_order_by = order_by
                self.session.commit()

    def update_website_subname(self, website_id: int, subname: str):
        website = self.get_website_by_id(website_id)
        if website:
            if website.subname != subname:
                previous_subname = website.subname
                # If previous subname is not empty, delete it from Namestone
                if previous_subname is not None and len(previous_subname) > 0:
                    self.delete_subname(previous_subname)
                website.subname = subname
                if website.last_known_cid:
                    # Write CID to Namestone
                    self.update_website_subname_cid(website.id)
            self.session.commit()

    def update_website_subname_cid(self, website_id: int):
        # TODO: move this method to Website model's instance method
        website = self.get_website_by_id(website_id)
        if website:
            if website.subname and website.last_known_cid:
                namestone_api = "https://namestone.xyz/api/public_v1/set-name"
                headers = {"Authorization": config.namestone_api_token}
                data = {
                    "domain": config.namestone_domain,
                    "name": website.subname,
                    "address": website.account.address,
                    "contenthash": "ipfs://" + website.last_known_cid,
                }
                requests.post(namestone_api, headers=headers, json=data, timeout=30)

    def delete_subname(self, subname: str):
        # Delete subname from Namestone
        namestone_api = "https://namestone.xyz/api/public_v1/delete-name"
        headers = {"Authorization": config.namestone_api_token}
        data = {"domain": config.namestone_domain, "name": subname}
        requests.post(namestone_api, headers=headers, json=data, timeout=30)

    def get_website(self, name: str, account_id: int):
        website = (
            self.session.query(Website)
            .filter(Website.name == name)
            .filter(Website.account_id == account_id)
            .first()
        )
        return website

    def get_website_by_subname(self, subname: str):
        website = self.session.query(Website).filter(Website.subname == subname).first()
        return website

    def get_websites(self, account_id: int, order_by: str = "name"):
        if order_by == "pinned":
            # order by last pinned
            websites = (
                self.session.query(Website)
                .filter(Website.account_id == account_id)
                .order_by(Website.last_pinned.desc())
                .all()
            )
        elif order_by == "created":
            # order by created
            websites = (
                self.session.query(Website)
                .filter(Website.account_id == account_id)
                .order_by(Website.created.desc())
                .all()
            )
        elif order_by == "size":
            # order by size
            websites = (
                self.session.query(Website)
                .filter(Website.account_id == account_id)
                .order_by(Website.size.desc())
                .all()
            )
        else:
            # order by name
            websites = (
                self.session.query(Website)
                .filter(Website.account_id == account_id)
                .order_by(Website.name.asc())
                .all()
            )
        return websites

    def get_website_by_id(self, website_id: int):
        website = self.session.query(Website).filter(Website.id == website_id).first()
        return website

    def get_website_by_pin_api_uuid(self, pin_api_uuid: str):
        website = (
            self.session.query(Website)
            .filter(Website.pin_api_uuid == pin_api_uuid)
            .first()
        )
        return website

    def create_website(self, name: str):
        website = Website()
        website.account_id = self.current_user.id
        website.pin_api_uuid = str(uuid.uuid4())
        website.name = name
        website.created = int(time.time())
        self.session.add(website)
        self.session.commit()
        return website

    def delete_website_by_id(self, website_id: int) -> bool:
        website = self.get_website_by_id(website_id)
        if website:
            self.session.delete(website)
            self.session.commit()
            return True
        return False

    def delete_website_tasklogs_by_website_id(self, website_id: int):
        self.session.query(WebsiteTaskLog).filter(
            WebsiteTaskLog.website_id == website_id
        ).delete()
        self.session.commit()

    def get_website_tasklog_later_than_id(self, website_id: int, last_log_id: int):
        a_log = (
            self.session.query(WebsiteTaskLog)
            .filter(WebsiteTaskLog.website_id == website_id)
            .filter(WebsiteTaskLog.id > last_log_id)
            .order_by(WebsiteTaskLog.id.asc())
            .first()
        )
        return a_log

    def get_objects(self, account_id: int, order_by: str = "name"):
        if order_by == "id":
            # order by id
            objects = (
                self.session.query(CIDObject)
                .filter(CIDObject.account_id == account_id)
                .order_by(CIDObject.id.asc())
                .all()
            )
        elif order_by == "pinned":
            # order by created
            objects = (
                self.session.query(CIDObject)
                .filter(CIDObject.account_id == account_id)
                .order_by(CIDObject.created.desc())
                .all()
            )
        elif order_by == "size":
            # order by size
            objects = (
                self.session.query(CIDObject)
                .filter(CIDObject.account_id == account_id)
                .order_by(CIDObject.size.desc())
                .all()
            )
        else:
            # order by name
            objects = (
                self.session.query(CIDObject)
                .filter(CIDObject.account_id == account_id)
                .order_by(CIDObject.filename.asc())
                .all()
            )
        return objects

    def get_object_by_uuid(self, uuid: str):
        obj = (
            self.session.query(CIDObject).filter(CIDObject.object_uuid == uuid).first()
        )
        return obj

    def delete_object_by_uuid(self, object_uuid: str) -> bool:
        o = self.get_object_by_uuid(object_uuid)
        if o:
            # unpin from IPFS
            # TODO: check if any other objects are using the same CID
            if o.cid:
                try:
                    resp = requests.post(
                        f"{config.ipfs_server}/api/v0/pin/rm?arg={o.cid}",
                        timeout=30,
                    )
                    print(f"IPFS API status code: {resp.status_code}")
                    print(f"Unpinned {o.cid} from IPFS: {resp.text}")
                except Exception as e:
                    print(f"Failed to unpin {o.cid} from IPFS: {e}")
            if o.cid_thumb:
                try:
                    resp = requests.post(
                        f"{config.ipfs_server}/api/v0/pin/rm?arg={o.cid_thumb}",
                        timeout=30,
                    )
                    print(f"IPFS API status code: {resp.status_code}")
                    print(f"Unpinned {o.cid_thumb} from IPFS: {resp.text}")
                except Exception as e:
                    print(f"Failed to unpin {o.cid_thumb} from IPFS: {e}")
            self.session.delete(o)
            self.session.commit()
            return True
        return False
