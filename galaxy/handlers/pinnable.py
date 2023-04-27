#!/usr/bin/env python3

import re

import pylibmc
import redis
import sqlalchemy

from galaxy.models.pinnable import Account, Website

IPNS_RE = re.compile(r"^k51[0-9a-z]{59}$")


class PinnableMixin(object):
    session: sqlalchemy.orm.session.Session
    mc: pylibmc.Client
    r: redis.Redis
    current_user: Account
    now: int

    def get_account(self, address: str):
        account = (
            self.session.query(Account)
            .filter(Account.address == address.lower())
            .first()
        )
        return account

    def create_account(self, address: str):
        account = Account(address=address.lower(), created=self.now())
        self.session.add(account)
        self.session.commit()
        return account

    def verify_website_name(self):
        if "name" in self.request.arguments:
            name = self.get_argument("name").strip()
            name_length = len(name)
        else:
            name = None
            name_length = 0
            self.add_error("Name is required.")
        name = name.lower()
        self.values["website_name"] = name
        if name_length == 62 and name.startswith("k51"):
            if not IPNS_RE.match(name):
                self.add_error("Invalid IPNS provided.")
            return
        if name.endswith(".eth"):
            existing_name = self.get_website(name, account_id=self.current_user.id)
            if existing_name:
                self.add_error("Website name already exists.")
        if name_length > 200:
            self.add_error("Name must be less than 200 characters.")

    def get_website(self, name: str, account_id: int):
        website = (
            self.session.query(Website)
            .filter(Website.name == name)
            .filter(Website.account_id == account_id)
            .first()
        )
        return website

    def get_websites(self, account_id: int):
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

    def create_website(self, name: str):
        website = Website(
            account_id=self.current_user.id, name=name, created=self.now()
        )
        self.session.add(website)
        self.session.commit()
        return website
