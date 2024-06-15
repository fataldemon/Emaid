import requests
import time
import jwt
from PIL import Image
import base64


api_key = "a1118ed6d2054308060ca13ca9d20151.YCELx80j8e7TXu9r"


def generate_base64(image_path: str):
    image = Image.open(image_path)
    image_data = image.tobytes()
    base64_data = base64.b64encode(image_data)
    return base64_data


def generate_token(apikey: str, exp_seconds: int):
    try:
        id, secret = apikey.split(".")
    except Exception as e:
        raise Exception("invalid apikey", e)

    payload = {
        "api_key": id,
        "exp": int(round(time.time() * 1000)) + exp_seconds * 1000,
        "timestamp": int(round(time.time() * 1000)),
    }

    return jwt.encode(
        payload,
        secret,
        algorithm="HS256",
        headers={"alg": "HS256", "sign_type": "SIGN"},
    )

def send_zhipu_api():
    token = generate_token(api_key, 60)
    model = "glm-4v"
    image_b64 = generate_token("D:\\QQ\\PersonalData\\2367513895\\nt_qq\\nt_data\\Emoji\\emoji-recv\\2024-01\\Ori\\544408ce5e8e03f5142552823a98046e.jpg", 60)
    message = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "请详细描述出图片里的内容"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_b64
                    }
                }
            ]
        }
    ]
    query = {
        "model": model,
        "messages": message,
        "temperature": 0.9,
        "top_p": 0.15,
        "stream": False,  # 不启用流式API
    }
    _headers = {"Content-Type": "application/json", "Authorization": token}
    with requests.session() as sess:
        resp = sess.post(
            "https://open.bigmodel.cn/api/paas/v4/chat/completions&api_key=",
            headers=_headers,
            json=query,
            timeout=60
        )
    print(resp.status_code)
    if resp.status_code == 200:
        print(resp.content)

if __name__ == "__main__":
    send_zhipu_api()
