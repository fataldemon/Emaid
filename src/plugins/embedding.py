from sentence_transformers import SentenceTransformer
import os
import faiss
from nonebot import on_command
from nonebot.adapters.red.event import GroupMessageEvent
import pandas as pd
import numpy as np
import pickle

model = SentenceTransformer('moka-ai/m3e-base')

doc_folder = "memory/"
vector_folder = "memory/vector/"
master_id = "664648216"


def read_as_content(file_name: str) -> str:
    with open(doc_folder + file_name, 'r', encoding="utf-8") as file:
        file_content = file.read()
    return file_content


def save_as_file(content: str, file_name: str):
    with open(vector_folder + file_name, "w") as file:
        file.write(content)


# 将faiss的索引index写到文件中，返回文件名
def write_index(index) -> str:
    faiss.write_index(index, vector_folder + 'index.faiss')
    return vector_folder + 'index.faiss'


def generate_vector():
    content = ""
    file_list = os.listdir(doc_folder)
    for file_name in file_list:
        # 读取所有文件内容为字符串
        if file_name != "Put Setting and Knowledge Files Here.txt" and file_name.endswith(".txt"):
            # df = pd.read_csv(doc_folder + file_name, sep="#", header=None, names=["sentence"])
            # print(df)
            # sentences = df["sentence"].tolist()
            content += read_as_content(file_name)
        # 按句号分割为数组
        sentences = content.split("。")
        with open(vector_folder + 'sentences.pkl', 'wb') as f:
            pickle.dump(sentences, f)
        sentence_embeddings = model.encode(sentences)
        # 保存文件内容为向量
        np.save(vector_folder + "embeddings", sentence_embeddings)
        dimension = sentence_embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(sentence_embeddings)
        write_index(index)


def vector_search(question: str, top_k: int) -> str:
    with open(vector_folder + 'sentences.pkl', 'rb') as f:
        sentences = pickle.load(f)
    index = faiss.read_index(vector_folder + 'index.faiss')
    search = model.encode([question])
    accuracy, matches = index.search(search, top_k)
    # 相关性的零点所对应的坐标（该数据内容应为\n，相关性低于这个值的则视为不相关数据）
    rel_zero_point = len(sentences)-1
    print(rel_zero_point)
    print(accuracy, " ", matches)
    result: str = ""
    if rel_zero_point not in matches[0]:
        for i in matches[0]:
            result += sentences[i].strip() + "。"
            print(i, ' ', sentences[i].strip(), " ——正相关数据")
    else:
        for i in matches[0]:
            if i != rel_zero_point:
                result += sentences[i].strip() + "。"
                print(i, ' ', sentences[i].strip(), " ——正相关数据")
            else:
                print(i, ' ', sentences[i].strip(), " ——不相关数据")
                break
    print("搜索结果为：", result)
    return result


refresh_knowledge = on_command("知识消化")
append_knowledge = on_command("追加知识 ")


@refresh_knowledge.handle()
async def refresh(event: GroupMessageEvent):
    if event.senderUin == master_id:
        generate_vector()
        await refresh_knowledge.send("爱丽丝正在复习自己学会的知识...")
    else:
        await refresh_knowledge.send("权限不足")


@append_knowledge.handle()
async def new_knowledge(event: GroupMessageEvent):
    if event.senderUin == master_id:
        info = str(event.message).replace("/追加知识 ", "")

    else:
        await append_knowledge.send("权限不足")






