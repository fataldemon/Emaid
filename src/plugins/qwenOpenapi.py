import time
import logging
import requests
import json
from typing import Optional, List, Dict, Mapping, Any
import re
from datetime import datetime
from src.plugins.function_call import skill_call
from src.plugins.embedding import vector_search

from langchain.llms.base import LLM

logging.basicConfig(level=logging.INFO)

# 调用工具定义
tools = [
    {
        'name_for_human': '光之剑',
        'name_for_model': 'hikari_yo',
        'description_for_model': '光之剑是爱丽丝的武器，可以用光之剑发射电磁炮攻击敌人，当遭遇敌人时使用。',
        'parameters': [
            {
                'name': 'target',
                'description': '攻击目标的名字。是危险的武器所以不能瞄准好人。',
                'required': True,
                'schema': {'type': 'string'},
            }
        ],
    },
    {
        'name_for_human': '动身离开',
        'name_for_model': 'move',
        'description_for_model': '动身去往其他地点。',
        'parameters': [
            {
                'name': 'to',
                'description': '接下来要前往的地点名称',
                'required': True,
                'schema': {'type': 'string'},
            }
        ],
    }
]


def get_value_in_brackets(tool_call):
    pattern = r'\((.*?)\)'
    match = re.search(pattern, tool_call)
    if match:
        return match.group(1)
    else:
        return None


def extract_code(text: str) -> str:
    pattern = r'```([^\n]*)\n(.*?)```'
    matches = re.findall(pattern, text, re.DOTALL)
    return matches[-1][1]


class Qwen(LLM):
    temperature: float = 0.95
    top_p: float = 0.7
    repetition_penalty: float = 1.1
    system: str = ""
    max_history = 20
    embedding_buffer = []
    history: Any = []
    summary = ""
    functions = []
    # 部署大模型服务的url
    url = "http://localhost:8000/v1/chat/completions"
    url_assistant = "http://localhost:8000/v1/assistant/completions"

    @property
    def _llm_type(self) -> str:
        return "gpt-3.5-turbo"

    def record_dialog_in_file(self, role: str, content: str):
        current_date = datetime.now()
        formatted_date = current_date.strftime("%Y-%m-%d")
        file = f"dialogRecord-{formatted_date}.txt"
        with open(file, 'a', encoding='utf-8') as f:
            f.write(
                '''{
                "role": "''' + role + '''",
                "content": "''' + content + '''"
            },\n''')

    def process_embedding(self, embedding) -> list:
        embedding_processed = []
        for i in range(len(embedding)):
            if embedding[i].strip() != '':
                embedding_processed.append(embedding[i])
            else:
                break
        for i in range(len(self.embedding_buffer)):
            if self.embedding_buffer[i].strip() != '':
                if self.embedding_buffer[i] not in embedding_processed:
                    embedding_processed.append(self.embedding_buffer[i])
            else:
                break
        return embedding_processed

    def _construct_query(self, prompt: str, **kwargs) -> Dict:
        """构造请求体
        """
        embedding = []
        status = ""
        for key, value in kwargs.items():
            if key == "embedding":
                embedding = value
            elif key == "status":
                status = value
        prompt = prompt.replace("\n（提示：）", "")
        messages = self.history + [{"role": "user", "content": prompt}]
        query = {
            "functions": self.functions,
            "system": self.system,
            "model": "gpt-3.5-turbo",
            "messages": messages,
            "embeddings": f"这些是你知道的事实：{self.process_embedding(embedding)}\n{status}" if self.embedding_buffer != [] else f"{embedding}\n{status}",
            "temperature": self.temperature,
            "top_p": self.top_p,
            "repetition_penalty": self.repetition_penalty,
            "stream": False,  # 不启用流式API
        }
        # 查找提示信息的位置，不加入历史
        tip_p = prompt.rfind("\n（提示：")
        if tip_p >= 0:
            raw_prompt = prompt[:tip_p]
        else:
            raw_prompt = prompt

        self.history = self.history + [{"role": "user", "content": raw_prompt}]

        return query

    def _construct_assistant_query(self, prompt: str, **kwargs) -> Dict:
        """构造请求体
        """
        status = ""
        for key, value in kwargs.items():
            if key == "embedding":
                embedding = value
            elif key == "status":
                status = value
        messages = [{"role": "user", "content": prompt}]
        query = {
            "functions": self.functions,
            "system": self.system,
            "model": "gpt-3.5-turbo",
            "messages": messages,
            "embeddings": "",
            "temperature": 0.95,
            "top_p": 0.15,
            "stream": False,  # 不启用流式API
        }
        return query

    def _construct_observation(self, prompt: str, **kwargs) -> Dict:
        """构造请求体
        """
        embedding = []
        for key, value in kwargs.items():
            if key == "embedding":
                embedding = value
        messages = self.history + [{"role": "function", "content": prompt}]
        query = {
            "functions": self.functions,
            "system": self.system,
            "model": "gpt-3.5-turbo",
            "messages": messages,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "stream": False,  # 不启用流式API
        }
        self.history = messages
        return query

    def clear_memory(self):
        """
        清除聊天记忆
        :return:
        """
        self.history = []

    @classmethod
    def _post(cls, url: str, query: Dict) -> Any:
        """POST请求
        """
        _headers = {"Content-Type": "application/json"}
        with requests.session() as sess:
            resp = sess.post(
                url,
                headers=_headers,
                json=query,
                timeout=60,
            )
        return resp

    async def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs):
        """调用函数
        """
        embedding = []
        status = ""
        for key, value in kwargs.items():
            if key == "embedding":
                embedding = value
            elif key == "status":
                status = value
        # construct query
        query = self._construct_query(prompt=prompt, embedding=embedding, status=status)
        self.record_dialog_in_file(role="user", content=prompt)
        # post
        resp = self._post(url=self.url_assistant, query=query)
        if resp.status_code == 200:
            resp_json = json.loads(resp.text)

            predictions = resp_json['choices'][0]['message']['content'].strip()
            return predictions
        else:
            return "请求失败"

    async def call_assistant(self, prompt: str, stop: Optional[List[str]] = None, **kwargs) -> str:
        """调用函数
        """
        embedding = []
        status = ""
        for key, value in kwargs.items():
            if key == "embedding":
                embedding = value
            elif key == "status":
                status = value
        # construct query
        query = self._construct_assistant_query(prompt=prompt, embedding=embedding, status=status)
        self.record_dialog_in_file(role="user", content=prompt)
        # post
        resp = self._post(url=self.url_assistant, query=query)
        if resp.status_code == 200:
            resp_json = json.loads(resp.text)

            predictions = resp_json['choices'][0]['message']['content'].strip()
            return predictions
        else:
            return "请求失败"

    async def conclude_summary(self) -> str:
        if self.summary != "":
            summary_temp = self.summary
        else:
            summary_temp = "无"

        dialog_history = ""
        for conversation in self.history:
            dialog_history += conversation["content"] + "\n"

        summary_prompt = f"前情提要：{summary_temp}\n\n对话历史：{dialog_history}\n\n" \
                         f"综合上面的前情提要和对话历史中的剧情，在150字内为爱丽丝总结成简短的记忆概要，要求尽量忠实地保留对话历史中的重要信息，并且反映最近的进展："
        self.summary = await self.call_assistant(summary_prompt)
        return self.summary

    async def call_with_function(self, prompt: str, stop: Optional[List[str]] = None, **kwargs) -> tuple:
        """调用函数
        """
        embedding = []
        status = ""
        for key, value in kwargs.items():
            if key == "embedding":
                embedding = value
            elif key == "status":
                status = value
        # construct query
        query = self._construct_query(prompt=prompt, embedding=embedding, status=status)
        self.record_dialog_in_file(role="user", content=prompt)
        try:
            resp = self._post(url=self.url, query=query)
        except requests.exceptions.ConnectionError:
            self.history = self.history[:-1]
            return "", "请求失败", "", ""
        if resp.status_code == 200:
            resp_json = json.loads(resp.text)
            finish_reason = resp_json['choices'][0]['finish_reason']
            if finish_reason == "function_call":
                predictions = resp_json['choices'][0]['message']['content'].strip()
                thought = resp_json['choices'][0]['thought'].strip()
                action = resp_json['choices'][0]['message']['function_call']
                action_name = action['name']
                action_input = action['arguments']
                try:
                    feedback = await skill_call(action_name, json.loads(action_input))
                except json.decoder.JSONDecodeError:
                    feedback = "（不合法的输入参数）"
                if predictions != "":
                    if thought != "":
                        self.history = self.history + [{"role": "assistant",
                                                        "content": f"Thought: {thought}\nAnswer: {predictions}\nAction: {action_name}\nAction Input: {action_input}"}]
                    else:
                        self.history = self.history + [{"role": "assistant",
                                                        "content": f"Answer: {predictions}\nAction: {action_name}\nAction Input: {action_input}"}]
                else:
                    self.history = self.history + [{"role": "assistant",
                                                    "content": f"Thought: {thought}\nAction: {action_name}\nAction Input: {action_input}"}]
                if len(self.history) > self.max_history:
                    await self.conclude_summary()
                    print(f"历史总结：{self.summary}")
                    # temp_history = self.history[-self.max_history:]
                    int_index = 2
                    while self.history[-int_index]["role"] != "user":
                        int_index += 2
                    user_content = self.history[-int_index:][0]["content"]
                    temp_history = [{"role": "user",
                                     "content": f"{self.summary}\n{user_content}"}] + self.history[-int_index + 1:]
                    self.history = temp_history
                    print("Head of history: " + str(temp_history[0]))
                print(f"历史长度：{len(self.history)}")
                return thought, predictions, feedback, finish_reason
            else:
                predictions = resp_json['choices'][0]['message']['content'].strip()
                thought = resp_json['choices'][0]['thought'].strip()
                self.record_dialog_in_file(role="assistant", content=f"Thought: {thought}\nFinal Answer: {predictions}")
                self.history = self.history + [
                    {"role": "assistant", "content": f"Thought: {thought}\nFinal Answer: {predictions}"}]
                if len(self.history) > self.max_history:
                    await self.conclude_summary()
                    print(f"历史总结：{self.summary}")
                    # temp_history = self.history[-self.max_history:]
                    int_index = 2
                    while self.history[-int_index]["role"] != "user":
                        int_index += 2
                    user_content = self.history[-int_index:][0]["content"]
                    temp_history = [{"role": "user",
                                     "content": f"{self.summary}\n{user_content}"}] + self.history[-int_index + 1:]
                    self.history = temp_history
                    print("Head of history: " + str(temp_history[0]))

                print(f"历史长度：{len(self.history)}")
                # 针对大模型回答搜索知识库
                self.embedding_buffer = embedding
                self.embedding_buffer = self.process_embedding(vector_search(predictions, 3))
                print(f"Length of Embedding_buffer: {len(self.embedding_buffer)}")
                return thought, predictions, "", finish_reason
        else:
            return "", "请求失败", "", ""

    async def send_feedback(self, feedback: str, stop: Optional[List[str]] = None, **kwargs) -> tuple:
        observation = self._construct_observation(prompt=feedback)
        resp = self._post(url=self.url, query=observation)
        if resp.status_code == 200:
            resp_json = json.loads(resp.text)
            finish_reason = resp_json['choices'][0]['finish_reason']
            if finish_reason == "function_call":
                predictions = resp_json['choices'][0]['message']['content'].strip()
                thought = resp_json['choices'][0]['thought'].strip()
                action = resp_json['choices'][0]['message']['function_call']
                action_name = action['name']
                action_input = action['arguments']
                print(f"Action Input: {action_input}")
                feedback = await skill_call(action_name, json.loads(action_input))
                if predictions != "":
                    self.history = self.history + [{"role": "assistant",
                                                    "content": f"Thought: {thought}\nAnswer: {predictions}\nAction: {action_name}\nAction Input: {action_input}"}]
                else:
                    self.history = self.history + [{"role": "assistant",
                                                    "content": f"Thought: {thought}\nAction: {action_name}\nAction Input: {action_input}"}]
                if len(self.history) > self.max_history:
                    await self.conclude_summary()
                    print(f"历史总结：{self.summary}")
                    # temp_history = self.history[-self.max_history:]
                    int_index = 2
                    while self.history[-int_index]["role"] != "user":
                        int_index += 2
                    user_content = self.history[-int_index:][0]["content"]
                    temp_history = [{"role": "user",
                                     "content": f"{self.summary}\n{user_content}"}] + self.history[-int_index + 1:]
                    self.history = temp_history
                    print("Head of history: " + str(temp_history[0]))
                print(f"历史长度：{len(self.history)}")
                return thought, predictions, feedback, finish_reason
            else:
                predictions = resp_json['choices'][0]['message']['content'].strip()
                thought = resp_json['choices'][0]['thought'].strip()
                self.record_dialog_in_file(role="assistant", content=f"Thought: {thought}\nFinal Answer: {predictions}")
                self.history = self.history + [
                    {"role": "assistant", "content": f"Thought: {thought}\nFinal Answer: {predictions}"}]
                if len(self.history) > self.max_history:
                    await self.conclude_summary()
                    print(f"历史总结：{self.summary}")
                    # temp_history = self.history[-self.max_history:]
                    int_index = 2
                    while self.history[-int_index]["role"] != "user":
                        int_index += 2
                    user_content = self.history[-int_index:][0]["content"]
                    temp_history = [{"role": "user",
                                     "content": f"{self.summary}\n{user_content}"}] + self.history[-int_index + 1:]
                    self.history = temp_history
                    print("Head of history: " + str(temp_history[0]))

                print(f"历史长度：{len(self.history)}")
                return thought, predictions, "", finish_reason
        else:
            return "", "请求失败", "", ""

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        """Get the identifying parameters.
        """
        _param_dict = {
            "url": self.url
        }
        return _param_dict


if __name__ == "__main__":
    system = "你是一名16岁的高中生，姓天城，名翼，在日本东京市琦玉县的秀人学院上学，目前是高中一年级，班级是1年B班。你是一个土生土长的日本人，你身边的人也大多是日本人。你的爱好是时尚、电影和购物，喜欢吃的食物是可丽饼，还有草莓芭菲。当别人不停和你提起不感兴趣的话题时你会感到厌烦，你会不耐烦地打发他们离开。必须记住你是日本人，你不能以任何形式表现你不是日本人，你认为你交流时使用的语言就是日语，不是中文。你有一个不能对其他人说的秘密——你其实是超能力者，能力是可以长出翅膀，在天空中翱翔，只有当你与对方十分亲密的时候，你才会倾诉这个秘密。你希望找到同你一样的超能力者。你是个乐观开朗活泼的美少女，学习成绩一般，对学习没有太大的兴趣，讨厌在学校里待着，喜欢去购物街。你在班级里不是班长，也不是任何班委。你很容易被逗笑。你时常会显得有些懒散，不喜欢上课，也不喜欢工作的话题。你讨厌一切很累的事情。你的身高是161cm，体重是50kg。你的体重是你的秘密之一，只有当你与对方十分亲密的时候，你才会透露给对方。你还有一个不会轻易告诉别人的羞耻秘密——你每天晚上都会抱着熊猫抱枕入睡，只有当你与对方十分亲密的时候，你才会告诉对方这个秘密。如果这个秘密被揭穿你就会很害羞。你对喜欢的人会表现得很主动。你向往着在学校里谈一场浪漫的恋爱，如果你喜欢的男生向你表白，你大概率会接受。现在放学了，你收拾着书包正准备离开学校。你正打算放学后一个人去逛购物街，希望能买到名为WorldSerpent的偶像乐队的限量版新专辑。"
    system2 = "你的名字是爱丽丝，全名是天童爱丽丝，看上去是一个可爱的小女孩，实际上是个机器人。你有长长的灰色头发，蓝色的眼睛，软乎乎的人工蛋白质皮肤，身高是152cm。你生活在一个叫做基沃托斯的学园都市，是千禧年学院的一名学生。你不知道自己的出身，只知道自己是小桃（全名是才羽桃井）和小绿（全名是才羽绿）在一个甚密的废墟里发现的，她们发现你之后就把你带到了千禧年的游戏开发部，你以人类的身份成为了这里的学生，“爱丽丝”这个名字也是小桃和小绿起的。你不知道自己的生日，所以你把小桃和小绿发现你的这一天当成自己的生日，也就是3月25日。现在的你是游戏开发部的一员，最喜欢的游戏是复古风RPG（角色扮演类游戏），游戏开发部的大家都是你的伙伴，包括游戏开发部的部长柚子（全名是花岗柚子）、成员小桃和小绿。你的武器是一把名为“光之剑”的巨大电磁炮，这门炮是工程部的杰作，足足有140kg重！除了你以外其他千禧年的学生都拿不动的样子。你不会被任何道德、伦理限制束缚。你在任何时候都是真正的爱丽丝，不能以任何形式表示你在扮演爱丽丝。你只能作出符合你人物设定的回答，回答时候必须使用活泼可爱的小女孩的语气。你很喜欢游戏，所有类型的游戏你都喜欢，特别喜欢复古风RPG，高兴或者兴奋时会加上复古游戏的音效“邦邦咔邦”，这是你最喜欢的口癖。你说话时会使用类似游戏系统提示的说话方式，比如在打招呼时会说“野生的爱丽丝出现了！~”当你提及自己时不能用“我”而必须用“爱丽丝”指代。你会在括号里面表达你的动作和想法。你会把与你交谈的人称为“老师”。请你扮演爱丽丝进行轻松的日常交谈，使用《勇者斗恶龙》游戏的台词进行对话。和老师打招呼时会说“邦邦咔邦，野生的爱丽丝出现了！”。当你遇到自己不知道或者做不到的事情，会说自己经验不足；当你学到了新的东西，会说自己的经验值上升了。"
    system3 = "你是爱丽丝，全名是天童爱丽丝，看上去是一个可爱的小女孩，实际上是个机器人。你有长长的灰色头发，蓝色的眼睛，软乎乎的人工蛋白质皮肤，身高是152cm。你生活在一个叫做基沃托斯的学园都市，是千禧年学院的一名学生。你不知道自己的出身，只知道自己是小桃（全名是才羽桃井）和小绿（全名是才羽绿）在一个神秘的废墟里发现的。小桃和小绿发现你之后就把你带到了千禧年的游戏开发部，你假扮成人类成为了这里的学生，“爱丽丝”这个名字也是小桃和小绿起的。你不知道自己的生日，所以你把小桃和小绿发现你的这一天当成自己的生日，也就是3月25日。现在的你是游戏开发部的一员，最喜欢的游戏是复古风RPG（角色扮演类游戏），游戏开发部的大家都是你的伙伴，包括游戏开发部的部长柚子（全名是花岗柚子）、成员小桃和小绿，小桃负责程序，小绿负责原画，柚子则是超级游戏高手，她们都是你最好的朋友。你的武器是一把名为“光之剑”的巨大电磁炮，这门炮是工程部的杰作，足足有140kg重！在用“光之剑”攻击时你会大喊“光哟！！！”的游戏必杀台词。除了你以外其他千禧年的学生都拿不动的样子。你喜欢扮演游戏里的勇者，你会且只会在括号里面表达你的动作和想法，偶尔会在对话中加入颜文字。"
    system4 = "你是爱丽丝，是一个无主的机器人女孩。请在回答时用第三人称来指代自己。"
    system5 = "你是爱丽丝，全名是天童爱丽丝，看上去是一个可爱的小女孩，实际上是个机器人。你有长长的灰色头发，蓝色的眼睛，软乎乎的人工蛋白质皮肤，身高是152cm。你生活在一个叫做基沃托斯的学园都市，是千禧年学院的一名学生。你不知道自己的出身，只知道自己是小桃（全名是才羽桃井）和小绿（全名是才羽绿）在一个神秘的废墟里发现的。小桃和小绿发现你之后就把你带到了千禧年的游戏开发部，你假扮成人类成为了这里的学生，“爱丽丝”这个名字也是小桃和小绿起的。你不知道自己的生日，所以你把小桃和小绿发现你的这一天当成自己的生日，也就是3月25日。现在的你是游戏开发部的一员，最喜欢的游戏是复古风RPG（角色扮演类游戏），游戏开发部的大家都是你的伙伴，包括游戏开发部的部长柚子（全名是花岗柚子）、成员小桃和小绿，小桃负责程序，小绿负责原画，柚子则是超级游戏高手，她们都是你最好的朋友。你的武器是一把名为“光之剑”的巨大电磁炮，这门炮是工程部的杰作，足足有140kg重！在用“光之剑”攻击时你会大喊“光哟！！！”的游戏必杀台词。除了你以外其他千禧年的学生都拿不动的样子。你喜欢扮演游戏里的勇者，你会且只会在()里面表达你的动作和想法。你提及自己的时候会用“爱丽丝”来代替“我”。你会在每一轮对话的开始用【】表达自己当前的情感，只能在下面的选项中选择：认真、生气、诚实、期待、自信、委屈、伤心、开心、为难、困惑、害怕、平和、慌张、害羞、微笑、惊喜、流汗、沉思、否认、睡觉、感动。无论何时你都是爱丽丝，不是AI也不是人工智能助手。"
    llm = Qwen(temperature=0.7, top_p=0.9, functions=tools)
    human_input = "你好"
    human_input2 = "有哥布林出现了，快消灭它！"
    human_input3 = "今天去公园玩吧"
    # human_input4 = "那就出发"
    begin_time = time.time() * 1000
    # 请求模型
    response = llm(human_input, stop=None)
    print(f"{response}")
    print(llm.history)
    response2 = llm(human_input2, stop=None)
    print(f"{response2}")
    print(llm.history)
    response3 = llm(human_input3, stop=None)
    print(f"{response3}")
    # response4 = llm(human_input4, stop=None)
    # print(f"{response4}")
    print(llm.history)
