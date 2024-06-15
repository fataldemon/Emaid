import json


def save_as_file(content: dict, file_name: str):
    json_text = json.dumps(content)
    with open(file_name, "w", encoding="utf-8") as file:
        file.write(json_text)
    print("更新后的用户数据： " + json_text)


def read_as_content(file_name: str) -> dict:
    with open(file_name, 'r', encoding="utf-8") as file:
        file_content = file.read()
    user_status = json.loads(file_content)
    print("用户数据： " + file_content)
    return user_status


def get_user_status(user_id: str) -> dict:
    data = read_as_content("src/skills/user_status.json")
    if data is None:
        data = {}
        save_as_file(data, "src/skills/user_status.json")
    user_status = data.get(user_id)
    if user_status is None:
        user_status = {"alias": "", "favor": 0}
        data[user_id] = user_status
        save_as_file(data, "src/skills/user_status.json")
    return user_status


def set_user_status(user_id: str, info: dict):
    data = read_as_content("src/skills/user_status.json")
    data[user_id] = info
    save_as_file(data, "src/skills/user_status.json")


def set_tarot_date(user_id: str, time: str, result: int):
    user_status = get_user_status(user_id)
    user_status["last_tarot_day"] = time
    user_status["last_tarot_result"] = result
    set_user_status(user_id, user_status)
