import time

import arrow
from sqlalchemy import Column, inspect
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.ext.declarative import as_declarative


@as_declarative()
class Base(object):
    def __repr__(self):
        # Inspired by flask-sqlalchemy
        identity = inspect(self).identity

        if identity is None:
            pk = f"(transient {id(self)})"
        else:
            pk = ", ".join(str(value) for value in identity)

        return f"<{type(self).__name__} {pk}>"

    def to_dict(self):
        d = {}
        for column in self.__table__.columns:
            field = getattr(self, column.name)
            if field is not None:
                d[column.name] = field
            else:
                d[column.name] = None
        return d

    def humanize_time(self, ts, tz="US/Pacific"):
        return arrow.get(ts).to(tz).format("h:mm A · MMM D, YYYY ZZZ")

    def seconds_since(self, ts: int):
        return int(time.time()) - ts

    id = Column(
        INTEGER(display_width=10, unsigned=True),
        nullable=False,
        autoincrement=True,
        primary_key=True,
    )

    created = Column(INTEGER(display_width=10, unsigned=True), nullable=False)
    last_modified = Column(INTEGER(display_width=10, unsigned=True), nullable=True)
