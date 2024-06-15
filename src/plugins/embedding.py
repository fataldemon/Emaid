from sentence_transformers import SentenceTransformer
import os
import faiss
from nonebot import on_command
from nonebot.adapters.red.event import GroupMessageEvent
import spacy
import numpy as np
import pickle
from src.skills.game_status_process import get_master_id

# model = SentenceTransformer('moka-ai/m3e-base')
model = SentenceTransformer('DMetaSoul/Dmeta-embedding')
nlp = spacy.load("zh_core_web_trf")

doc_folder = "memory/"
vector_folder = "memory/vector/"
master_id = get_master_id()


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
    # 按换行符分割为段落
    paragraphs = content.split("\n")

    # sentences = []
    tags = []
    tags_map = {}
    for i in range(len(paragraphs)):
        paragraph = paragraphs[i]
        # 对注解进行解析
        if "##" in paragraph:
            tag_list = paragraph.split("##")
            paragraphs[i] = tag_list[0]
            tag_list = tag_list[1:]
            print(tag_list)
            for tag in tag_list:
                tag = tag.strip()
                if tag not in tags:
                    tags.append(tag)
                    tags_map[tag] = [i]
                else:
                    tags_map[tag].append(i)
    print(tags_map)
    # 搜索时将注解与段落并列，制造出搜索材料，并以搜索材料为基准生成向量
    search_materials = paragraphs + tags
    with open(vector_folder + 'tags_map.pkl', 'wb') as f:
        pickle.dump(tags_map, f)
    with open(vector_folder + 'materials.pkl', 'wb') as f:
        pickle.dump(search_materials, f)
    #     # 用spacy分割为句子
    #     doc = nlp(paragraphs[i])
    #     sentences += [sent.text for sent in doc.sents]
    # with open(vector_folder + 'sentences.pkl', 'wb') as f:
    #     pickle.dump(sentences, f)

    with open(vector_folder + 'paragraphs.pkl', 'wb') as f:
        pickle.dump(paragraphs, f)
    # 生成向量
    search_embeddings = model.encode(search_materials)
    # 保存文件内容为向量
    np.save(vector_folder + "srch_embeddings", search_embeddings)
    dimension = search_embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(search_embeddings)
    write_index(index)


def vector_search(question: str, top_k: int) -> list:
    print("开始读取文件")
    with open(vector_folder + 'materials.pkl', 'rb') as f:
        materials = pickle.load(f)
    with open(vector_folder + 'tags_map.pkl', 'rb') as f:
        tags_map = pickle.load(f)
    index = faiss.read_index(vector_folder + 'index.faiss')
    print("读取文件结束，开始embedding编码")
    search = model.encode([question])
    print("编码结束，开始向量搜索")
    accuracy, matches = index.search(search, 10)
    print("编码结束，向量搜索完成")
    print(accuracy, " ", matches)
    result = []
    result_index_list = []
    for i in matches[0]:
        answer = materials[i].strip()
        if tags_map.get(answer) is None:
            if i not in result_index_list:
                result_index_list.append(i)
            print('编号', i)
        else:
            for j in tags_map.get(answer):
                print('定位到tag：', answer, '编号', j)
                if j not in result_index_list:
                    result_index_list.append(j)
    for k in range(top_k):
        result.append(materials[result_index_list[k]].strip())
    # print("搜索结果为：", result)  # 抛弃最后一个换行符
    return result


refresh_knowledge = on_command("知识消化")
append_knowledge = on_command("追加知识 ")


@refresh_knowledge.handle()
async def refresh(event: GroupMessageEvent):
    if event.senderUin in master_id:
        generate_vector()
        await refresh_knowledge.send("爱丽丝正在复习自己学会的知识...")
    else:
        await refresh_knowledge.send("权限不足")


@append_knowledge.handle()
async def new_knowledge(event: GroupMessageEvent):
    if event.senderUin in master_id:
        info = str(event.message).replace("/追加知识 ", "")

    else:
        await append_knowledge.send("权限不足")






