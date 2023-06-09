import math

import sqlalchemy as sa
from sqlalchemy import Column, String
from sqlalchemy.dialects.mysql import BIGINT, DOUBLE, INTEGER
from sqlalchemy.orm import relationship
from tornado_sqlalchemy import SQLAlchemy
from web3 import Web3

from config import database_url, ipfs_gateway
from galaxy.utils.models import Base

engine_options = {"pool_size": 10, "max_overflow": 20, "pool_recycle": 3600}

db = SQLAlchemy(url=database_url, engine_options=engine_options)

ONE_GIGA_BYTE = 1_073_741_824


class Account(Base):
    __tablename__ = "Account"
    __table_arts__ = (
        sa.Index("address", "address", unique=True),
        {"comment": "Account"},
    )
    address = Column(String(128), nullable=False, unique=True)
    ens = Column(String(255), nullable=True, unique=False)
    avatar = Column(String(2048), nullable=True, unique=False)
    chain_id = Column(
        INTEGER(display_width=10, unsigned=True), nullable=False, default=1
    )
    dwb_balance = Column(DOUBLE, nullable=True, default=0)
    last_checked = Column(INTEGER(display_width=10, unsigned=True), nullable=True)
    websites = relationship(
        "Website",
        back_populates="account",
        primaryjoin="Account.id == foreign(Website.account_id)",
    )

    @property
    def display_name(self) -> str:
        if self.ens is not None:
            return self.ens
        return self.address[:6] + "..." + self.address[-4:]

    @property
    def quota(self) -> dict:
        _quota = getattr(self, "_quota", None)
        if _quota is not None:
            return _quota

        quota = {}
        quota["total_websites"] = 0
        quota["total_size"] = 0
        quota["used_websites"] = 0
        quota["used_size"] = 0

        if self.dwb_balance == 0:
            return quota

        if self.dwb_balance == 50:
            quota["total_websites"] = 2
            quota["total_size"] = 5 * ONE_GIGA_BYTE
            return quota

        if self.dwb_balance == 100:
            quota["total_websites"] = 5
            quota["total_size"] = 10 * ONE_GIGA_BYTE
            return quota

        if self.dwb_balance == 250:
            quota["total_websites"] = 25
            quota["total_size"] = 25 * ONE_GIGA_BYTE
            return quota

        quota["total_websites"] = math.ceil(self.dwb_balance / 10)
        quota["total_size"] = math.ceil(self.dwb_balance / 10) * ONE_GIGA_BYTE

        quota["used_websites"] = len(self.websites)

        used_size = 0

        for website in self.websites:
            used_size = used_size + (website.size or 0)

        quota["used_size"] = used_size

        self._quota = quota
        return quota

    @property
    def checksum_address(self):
        return Web3.to_checksum_address(self.address)

    @property
    def can_add_more(self) -> bool:
        if self.quota["total_websites"] == 0:
            return False
        if self.quota["used_websites"] >= self.quota["total_websites"]:
            return False
        return True

    @property
    def has_avatar(self) -> bool:
        if self.avatar is None:
            return False
        elif len(self.avatar) == 0:
            return False
        return True


class Website(Base):
    __tablename__ = "Website"
    __table_arts__ = (
        sa.Index("account_name", "account_id", "name", unique=True),
        sa.Index("pin_api_uuid", "pin_api_uuid", unique=True),
        sa.Index("account_id", "account_id"),
        {"comment": "Website"},
    )
    account_id = Column(INTEGER(display_width=10, unsigned=True), nullable=False)
    account = relationship(
        "Account",
        back_populates="websites",
        primaryjoin="Account.id == foreign(Website.account_id)",
    )
    pin_api_uuid = Column(String(36), nullable=False, unique=True)
    name = Column(String(200), nullable=False, unique=True)
    last_known_ipns = Column(String(128), nullable=True)
    last_known_cid = Column(String(128), nullable=True)
    size = Column(BIGINT(unsigned=True), nullable=True)
    last_checked = Column(INTEGER(display_width=10, unsigned=True), nullable=True)
    last_pinned = Column(INTEGER(display_width=10, unsigned=True), nullable=True)
    tasklogs = relationship(
        "WebsiteTaskLog",
        back_populates="website",
        primaryjoin="Website.id == foreign(WebsiteTaskLog.website_id)",
        order_by="desc(WebsiteTaskLog.created)",
    )

    @property
    def kind(self):
        if self.name.endswith(".eth"):
            return "ENS"
        elif self.name.startswith("k51"):
            return "IPNS"
        else:
            return "Unknown Kind"

    @property
    def url(self):
        if self.kind == "ENS":
            return f"{ipfs_gateway}/ipns/{self.name}"
        elif self.kind == "IPNS":
            return f"{ipfs_gateway}/ipns/{self.name}"
        else:
            return None

    @property
    def ipfs_path(self):
        if self.kind == "ENS":
            return f"/ipns/{self.name}"
        elif self.kind == "IPNS":
            return f"/ipns/{self.name}"
        else:
            return None


class WebsiteTaskLog(Base):
    __tablename__ = "WebsiteTaskLog"
    __table_arts__ = (
        sa.Index("website_id", "website_id"),
        {"comment": "Website Task Log"},
    )
    website_id = Column(INTEGER(display_width=10, unsigned=True), nullable=False)
    website = relationship(
        "Website",
        back_populates="tasklogs",
        primaryjoin="Website.id == foreign(WebsiteTaskLog.website_id)",
    )
    event = Column(String(4000), nullable=False)
    icon = Column(String(128), nullable=True)
    ipns = Column(String(128), nullable=True)
    cid = Column(String(128), nullable=True)
    size = Column(BIGINT(unsigned=True), nullable=True)
