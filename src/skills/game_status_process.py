import json


def save_as_file(content: dict, file_name: str):
    json_text = json.dumps(content)
    with open(file_name, "w", encoding="utf-8") as file:
        file.write(json_text)


def read_as_content(file_name: str) -> dict:
    with open(file_name, 'r', encoding="utf-8") as file:
        file_content = file.read()
    game_status = json.loads(file_content)
    return game_status


def get_master_id() -> str:
    game_status = read_as_content("src/skills/game_status.json")
    master_id = game_status.get("master_id")
    if master_id is None:
        return "664648216"
    else:
        return master_id


def get_ban_words() -> list:
    game_status = read_as_content("src/skills/game_status.json")
    ban_words = game_status.get("ban_words")
    if ban_words is None:
        return []
    else:
        return ban_words


def get_field() -> str:
    game_status = read_as_content("src/skills/game_status.json")
    field = game_status.get("field")
    if field is None:
        return "沙勒，老师的办公室"
    else:
        return field


def set_field(field: str):
    game_status = read_as_content("src/skills/game_status.json")
    game_status["field"] = field
    save_as_file(game_status, "src/skills/game_status.json")


def add_death_list(enemy: str):
    game_status = read_as_content("src/skills/game_status.json")
    death_list = game_status.get("death_list")
    if death_list is None:
        death_list = [enemy]
    elif enemy not in death_list:
        death_list.append(enemy)
    game_status["death_list"] = death_list
    save_as_file(game_status, "src/skills/game_status.json")


def clear_death_list():
    game_status = read_as_content("src/skills/game_status.json")
    game_status["death_list"] = []
    save_as_file(game_status, "src/skills/game_status.json")


def donate(amount: int) -> int:
    game_status = read_as_content("src/skills/game_status.json")
    coins = game_status.get("coins")
    if coins is not None:
        coins += amount
    else:
        coins = amount
    game_status["coins"] = coins
    save_as_file(game_status, "src/skills/game_status.json")
    return coins


def get_game_status() -> dict:
    game_status = read_as_content("src/skills/game_status.json")
    if game_status is not None:
        return game_status
    else:
        return {"field": "沙勒，老师的办公室", "master_id": "664648216",
                "death_list": []}


if __name__ == "__main__":
    a = 1

