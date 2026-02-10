import os
import numpy as np
import pandas as pd
import networkx as nx
from node2vec import Node2Vec
from scipy.linalg import orthogonal_procrustes
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import json
import csv

os.environ["HF_TOKEN"]="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"

JSON_INPUT_PATH= r"../knowledge_graph.json"
CSV_OUTPUT_FOLDER=r"D:\neo4j\neo4j-community-4.4.46\import"

csv_path=r"D:\neo4j\neo4j-community-4.4.46\import\knowledge_graph.csv"
save_path=r"C:\Users\Qiao\Desktop\吉安电子\ai-knowledge-graph-main\query\entity.csv"


def json_to_csv(json_path, csv_folder):
    """
    Convert JSON knowledge graph data to CSV format.
    Args:
        json_path: Path to JSON file containing triples data
        csv_path: Path to save the CSV file
    """
    json_basename=os.path.basename(json_path)
    json_filename=os.path.splitext(json_basename)[0]
    csv_full_path=os.path.join(csv_folder,json_filename+".csv")

    try:
        with open(json_path,'r',encoding='utf-8-sig') as f:
            data=json.load(f)
        print(f"成功读取JSON文件")
    except FileNotFoundError:
        print(f"未找到JSON文件")

    try:
        with open(csv_full_path,"w",encoding="utf-8-sig",newline="") as f:
            writer=csv.writer(f)
            writer.writerow(['subject','predicate','object'])
            row_count=0
            for item in data:
                if all(key in item for key in ['subject','predicate','object']):
                    subject=item['subject'].strip()
                    predicate=item['predicate'].strip()
                    object=item['object'].strip()

                    if subject and predicate and object:
                        writer.writerow([subject,predicate,object])
                        row_count+=1
        print(f"成功生成csv文件，共写入{row_count}条有效三元组")
    except Exception as e:
        print(f"生成csv文件失败：{e}")

def build_graph():
    df=pd.read_csv(csv_path,header=0,encoding="utf-8-sig")
    df.columns=['subject','predicate','object']
    G=nx.Graph()
    #添加节点
    all_entities=set(df['subject']).union(set(df['object']))
    for entity in all_entities:
        G.add_node(entity,name=entity)
    #添加边
    for _,row in df.iterrows():
        G.add_edge(row['subject'],row['object'],relation=row['predicate'])

    entity_to_id={v:k for k,v in enumerate(all_entities)}
    all_relations=list(set(df['predicate'].tolist()))
    relation_to_id={v:k for k,v in enumerate(all_relations)}

    triples_id=[]
    for _,row in df.iterrows():
        s_id=entity_to_id[row['subject']]
        p_id=relation_to_id[row['predicate']]
        o_id=entity_to_id[row['object']]
        triples_id.append([s_id,p_id,o_id])
    return G,df,entity_to_id,relation_to_id,triples_id,all_entities

# def node2vec(G):
#     node2vec=Node2Vec(
#         graph=G,
#         dimensions=128,
#         walk_length=30,
#         num_walks=150,
#         p=1,
#         q=1,
#         workers=8,
#         seed=42,
#         temp_folder=None,
#         quiet=False
#     )
#     model=node2vec.fit(
#         window=5,
#         min_count=1
#     )
#
#     entity_emb={}
#     for entity in G.nodes():
#         emb=model.wv[entity]
#         emb=emb/np.linalg.norm(emb) if np.linalg.norm(emb) != 0 else emb
#         entity_emb[entity]=emb.tolist()
#
#     return entity_emb

def text_vectorize(text,model):
    text_emb=model.encode(text,convert_to_numpy=True)
    if len(text_emb)>128:
        text_emb=text_emb[:128]
    elif len(text_emb)<128:
        text_emb=np.pad(text_emb,(0,128-len(text_emb)))
    text_emb=text_emb/np.linalg.norm(text_emb) if np.linalg.norm(text_emb) != 0 else text_emb
    return text_emb

# def align_vectors(emb,text_emb):
#     mat=np.array(list(emb.values()))
#     text_mat=np.array(text_emb)
#
#     common_entities = list(set(emb.keys()) & set(text_emb.keys()))
#     node2vec_mat = np.array([emb[ent] for ent in common_entities])
#     text_mat = np.array([text_emb[ent] for ent in common_entities])
#
#     # Procrustes对齐：将mat映射到text_mat的空间
#     R, _ = orthogonal_procrustes(node2vec_mat, text_mat)
#     aligned_node2vec_mat = node2vec_mat @ R
#
#     aligned_node2vec_embs = {}
#     for i, ent in enumerate(common_entities):
#         aligned_node2vec_embs[ent] = aligned_node2vec_mat[i].tolist()
#
#     return aligned_node2vec_embs

# def calculate_similarity(aligned_emb,text_emb):
#     similarity_dict={}
#     for ent,emb in aligned_emb.items():
#         sim=cosine_similarity([emb],[text_emb])[0][0]
#         similarity_dict[ent]=sim
#     sorted_sim=sorted(similarity_dict.items(),key=lambda x:x[1],reverse=True)
#     return sorted_sim

def vec_to_str(vec):
    return ','.join([f"{v:.8f}" for v in vec])

# def str_to_vec(vec_str):
#     return np.array([float(v) for v in vec_str.split(',')])


if __name__=="__main__":
    print(f"开始导入三元组")
    json_to_csv(JSON_INPUT_PATH, CSV_OUTPUT_FOLDER)
    print(f"三元组成功导入import文件夹")

    print("开始构建知识图谱")
    G,df,entity_to_id,relation_to_id,triples_id,all_entities=build_graph()
    print(f"知识图谱构建完成：实体数={len(G.nodes())},关系数={len(G.edges())}")

    # entity_emb=node2vec(G)
    # print(f"Node2Vec训练完成，生成{len(entity_emb)}个实体嵌入向量")

    text_model=SentenceTransformer("shibing624/text2vec-base-chinese")
    print("文本向量化模型加载完成")

    text_embs={}
    for ent in all_entities:
        text_embs[ent]=text_vectorize(ent,text_model).tolist()
    print(f"实体文本向量化完成")

    # aligned_embs=align_vectors(entity_emb,text_embs)
    # print("实体向量对齐完成")

    # emb_df=pd.DataFrame.from_dict(entity_emb,orient='index')
    # emb_df.reset_index(inplace=True)
    # emb_df.columns=['entity_name']+[f"entity_emb_{i}" for i in range(128)]
    # emb_df.to_csv(save_path,index=False,encoding="utf-8-sig")
    # print(f"实体向量已保存到{save_path}")

    save_data = []
    # for ent in all_entities:
    #     if ent in text_embs and ent in aligned_embs:
    #         save_data.append({
    #             "entity_name": ent,
    #             "text_emb": vec_to_str(text_embs[ent]),
    #             "aligned_emb": vec_to_str(aligned_embs[ent])
    #         })

    for ent in all_entities:
        if ent in text_embs:
            save_data.append({
                "entity_name": ent,
                "text_emb": vec_to_str(text_embs[ent])
            })

    final_df = pd.DataFrame(save_data)
    final_df.to_csv(save_path, index=False, encoding="utf-8-sig")
    print(f"\n存储实体名、文本向量到：{save_path}")
    print(f"最终CSV列数：{len(final_df.columns)}，行数：{len(final_df)}")
