from sqlalchemy import Column, inspect
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.ext.declarative import as_declarative, declared_attr


@as_declarative()
class Base(object):
    @declared_attr
    def __tablename__(cls) -> str:
        return type.__dict__["__name__"].__get__(cls)

    def __repr__(self):
        # Inspired by flask-sqlalchemy
        identity = inspect(self).identity

        if identity is None:
            pk = f"(transient {id(self)})"
        else:
            pk = ", ".join(str(value) for value in identity)

        return f"<{type(self).__name__} {pk}>"

    id = Column(
        INTEGER(display_width=10, unsigned=True),
        nullable=False,
        autoincrement=True,
        primary_key=True,
    )

    created = Column(INTEGER(display_width=10, unsigned=True), nullable=False)
    last_modified = Column(INTEGER(display_width=10, unsigned=True), nullable=True)
