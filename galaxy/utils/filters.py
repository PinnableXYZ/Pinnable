def format_genre(genre: str) -> str:
    if "racing" in genre.lower():
        return "Racing"
    if genre.lower() == "rpg":
        return "RPG"
    return genre.title()
