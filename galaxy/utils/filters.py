def format_genre(genre: str) -> str:
    if "racing" in genre.lower():
        return "Racing"
    if genre.lower() == "rpg":
        return "RPG"
    return genre.title()


def format_bytes(value: int) -> str:
    val = float(value)
    if val > 1024:
        if val > 1048576:
            if val > 1073741824:
                return "%(value).2f GB" % {"value": (val / 1073741824.0)}
            else:
                return "%(value).2f MB" % {"value": (val / 1048576.0)}
        else:
            return "%(value).2f KB" % {"value": (val / 1024.0)}
    else:
        return str(value) + " B"


def format_tokens(value: float) -> str:
    return f"{value:,.2f}"
