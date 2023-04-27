def format_genre(genre: str) -> str:
    if "racing" in genre.lower():
        return "Racing"
    if genre.lower() == "rpg":
        return "RPG"
    return genre.title()


def format_bytes(value: int) -> str:
    value = float(value)
    if value > 1024:
        if value > 1048576:
            if value > 1073741824:
                return "%(value).2f GB" % {"value": (value / 1073741824.0)}
            else:
                return "%(value).2f MB" % {"value": (value / 1048576.0)}
        else:
            return "%(value).2f KB" % {"value": (value / 1024.0)}
    else:
        return str(int(value)) + " B"


def format_tokens(value: float) -> str:
    return f"{value:,.2f}"
