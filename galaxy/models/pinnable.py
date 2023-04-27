import math

import sqlalchemy as sa
from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.mysql import BIGINT, CHAR, DOUBLE, INTEGER, TEXT, TINYINT
from sqlalchemy.orm import relationship
from tornado_sqlalchemy import SQLAlchemy

from config import database_url
from galaxy.utils.models import Base

db = SQLAlchemy(url=database_url)

ONE_GIGA_BYTE = 1_073_741_824


class Account(Base):
    __table_arts__ = (
        sa.Index("address", "address", unique=True),
        {"comment": "Account"},
    )
    address = Column(String(128), nullable=False, unique=True)
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
    def quota(self) -> dict:
        if hasattr(self, "_quota"):
            return self._quota

        quota = {}
        quota["total_websites"] = 0
        quota["total_size"] = 0

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

        self._quota = quota
        return self._quota

    @property
    def used_quota(self) -> dict:
        quota = {}
        quota["used_websites"] = 0
        quota["used_size"] = 0

        quota["used_websites"] = len(self.websites)

        used_size = 0

        for website in self.websites:
            used_size = used_size + website.size

        quota["used_size"] = used_size
        return quota


class Website(Base):
    __table_arts__ = (
        sa.Index("account_name", "account_id", "name", unique=True),
        sa.Index("account_id", "account_id"),
        {"comment": "Website"},
    )
    account_id = Column(INTEGER(display_width=10, unsigned=True), nullable=False)
    account = relationship(
        "Account",
        back_populates="websites",
        primaryjoin="Account.id == foreign(Website.account_id)",
    )
    name = Column(String(200), nullable=False, unique=True)
    last_known_ipns = Column(String(128), nullable=True)
    last_known_cid = Column(String(128), nullable=True)
    size = Column(BIGINT(unsigned=True), nullable=True, default=0)
    last_checked = Column(INTEGER(display_width=10, unsigned=True), nullable=True)
    last_pinned = Column(INTEGER(display_width=10, unsigned=True), nullable=True)

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
            return f"https://{self.name}.limo"
        elif self.kind == "IPNS":
            return f"https://ipfs.io/ipns/{self.name}"
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
