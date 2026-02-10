from neo4j import GraphDatabase,basic_auth
import numpy as np
from sentence_transformers import SentenceTransformer
import os
import json
import pandas as pd
from typing import List,Optional
from sklearn.metrics.pairwise import cosine_similarity
from pydantic import BaseModel
from fastapi import HTTPException

#实体选取相关配置
os.environ["HF_TOKEN"]="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"
ENTITY_VECTOR_FILE=r"query\entity.csv"
COMMUNITY_INFO_FILE=r"community/community_info.json"
TARGET_DIM=128
TOP_N=3
MODEL_NAME="shibing624/text2vec-base-chinese"
SIM_THRESHOLD=0.8

# Neo4j相关配置
NEO4J_URI="bolt://localhost:7687"
NEO4J_USER="neo4j"
NEO4J_PASS="12345678"
TOP_N_TRIPLES=10

#全局变量
model=None
entity_text_vectors={}
community_info={}
isolated_entities=set()
neo4j_driver:Optional[GraphDatabase.driver]=None

def init():
    print(f"初始化开始")
    global model,entity_text_vectors,community_info,neo4j_driver
    print(f"开始加载模型")
    model = SentenceTransformer(MODEL_NAME)
    print(f"模型加载完成")

    print(f"开始加载实体向量")
    load_entity_vectors()

    print(f"开始加载社区信息")
    load_community_info()

    print(f"开始连接Neo4j:{NEO4J_URI}")
    try:
        neo4j_driver=GraphDatabase.driver(NEO4J_URI,auth=basic_auth(NEO4J_USER,NEO4J_PASS))
        neo4j_driver.verify_connectivity()
        print(f"Neo4j连接成功")
    except Exception as e:
        print(f"Neo4j连接失败:{e}")
        raise e

def load_entity_vectors():
    global entity_text_vectors
    if not os.path.exists(ENTITY_VECTOR_FILE):
        raise FileNotFoundError(f"实体向量文件不存在:{ENTITY_VECTOR_FILE}")
    df=pd.read_csv(ENTITY_VECTOR_FILE,encoding="utf-8-sig")

    for i,row in df.iterrows():
        entity_name=row.get("entity_name","").strip()
        text_vec_str=row.get("text_emb","").strip()

        if not entity_name or not text_vec_str:
            continue

        try:
            vec=[float(v) for v in text_vec_str.split(",")]
            vec_np=np.array(vec)
            norm=np.linalg.norm(vec_np)
            if norm > 0:
                vec=vec_np/norm
            entity_text_vectors[entity_name]=vec
        except Exception as e:
            print(f"解析实体{entity_name}向量化失败:{e}")

    print(f"实体向量加载完成，共加载{len(entity_text_vectors)}个向量")

def load_community_info():
    global community_info,isolated_entities
    if not os.path.exists(COMMUNITY_INFO_FILE):
        raise FileNotFoundError(f"社区信息文件不存在:{COMMUNITY_INFO_FILE}")

    with open(COMMUNITY_INFO_FILE,"r",encoding="utf-8-sig") as f:
        # communities=json.load(f)
        raw=json.load(f)

    isolated_entities=set(raw.get("isolated_nodes",[]))

    for id,info in raw.get("communities",{}).items():
        try:
            cid=int(id)
            comm_emb=np.array(info.get("embedding",[]),dtype=np.float32)
            comm_nodes=info.get("nodes",[])
            comm_sum=info.get("summary","")
            if not comm_nodes or len(comm_emb)==0:
                print(f"社区{cid}无节点/无嵌入，跳过")
                continue

            # if len(comm_emb) > TARGET_DIM:
            #     comm_emb=comm_emb[:TARGET_DIM]
            # elif len(comm_emb)<TARGET_DIM:
            #     comm_emb=np.pad(comm_emb,(0,TARGET_DIM-len(comm_emb)),mode="constant")
            norm=np.linalg.norm(comm_emb)
            if norm > 0:
                comm_emb=comm_emb/norm

            valid_nodes=[n for n in comm_nodes if n in entity_text_vectors]
            community_info[cid]={
                "summary":comm_sum,
                "embedding":comm_emb,
                "nodes":valid_nodes
            }
        except Exception as e:
            print(f"社区{cid}信息解析失败:{e}")
    print(f"社区信息加载完成，共加载{len(community_info)}个社区,{len(isolated_entities)}个孤立节点")

def get_top_similar(target_emb:np.array,candidate_vectors:dict,top_n:int=3)->List[dict]:
    if not candidate_vectors:
        return []
    names=list(candidate_vectors.keys())
    embeds=np.vstack(list(candidate_vectors.values()))
    similarities=cosine_similarity(target_emb.reshape(1,-1),embeds)[0]

    top=similarities.argsort()[::-1][:top_n]
    return [
        {
            "name":names[i],
            "score":round(similarities[i],4)
        } for i in top
    ]

def entity_match(question:str,entities:List[str]=[])->List[str]:
    """
    如果dify传入了实体，对于实体数组中的每一个实体，分别做文本向量化、匹配最高的三个实体
    如果没有传入实体，将问题本身向量化，对于存储社区信息的json文件中的每一个实体做向量匹配，选取匹配度最高的三个社区，在其中把问题文本向量和实体匹配
    """
    global model,community_info,isolated_entities

    question=question.strip()
    entities=[e.strip() for e in entities if e.strip()]

    # print(f"传入的实体：{entities}")

    if not question:
        return []

    if entities:
        core_entities=set()
        for ent in entities:
            ent_emb=model.encode(ent,convert_to_numpy=True)[:TARGET_DIM]
            # if len(ent_emb)>TARGET_DIM:
            #     ent_emb=ent_emb[:TARGET_DIM]
            # elif len(ent_emb)<TARGET_DIM:
            #     ent_emb=np.pad(ent_emb,(0,TARGET_DIM-len(ent_emb)),mode="constant")
            norm=np.linalg.norm(ent_emb)
            if norm>1e-6:
                ent_emb=ent_emb/norm

            top_similar=get_top_similar(ent_emb,entity_text_vectors,TOP_N)
            # print(f"实体{ent}的相似实体为:{top_similar}")
            for sim_ent in top_similar:
                core_entities.add(sim_ent["name"])
    else:
        question_emb=model.encode(question,convert_to_numpy=True)
        # if len(question_emb)>TARGET_DIM:
        #     question_emb=question_emb[:TARGET_DIM]
        # elif len(question_emb)<TARGET_DIM:
        #     question_emb=np.pad(question_emb,(0,TARGET_DIM-len(question_emb)),mode="constant")
        norm=np.linalg.norm(question_emb)
        if norm>1e-6:
            question_emb=question_emb/norm

        if not community_info:
            return[]

        comm_candidate={cid:info["embedding"] for cid,info in community_info.items()}
        top_comm=get_top_similar(question_emb,comm_candidate,TOP_N)
        top_cid=[int(item["name"]) for item in top_comm]
        # print(f"匹配的社区为:{top_cid}")

        comm_entity_pool=set()
        for cid in top_cid:
            if cid in community_info:
                comm_entity_pool.update(community_info[cid]["nodes"])
        comm_entity_vectors={ent:entity_text_vectors[ent] for ent in comm_entity_pool if ent in entity_text_vectors}
        top_similar=get_top_similar(question_emb,comm_entity_vectors,TOP_N)

        ###处理孤立节点
        need_isolated=False
        min_sim=min(item["score"] for item in top_similar)if top_similar else None

        if(min_sim and min_sim<SIM_THRESHOLD) or not top_similar:
            need_isolated=True

        if need_isolated and isolated_entities:
            iso_vectors={ent:entity_text_vectors[ent] for ent in isolated_entities if ent in entity_text_vectors}
            iso_top=get_top_similar(question_emb,iso_vectors,TOP_N)

            better_iso=[]
            for item in iso_top:
                if item["score"]>min_sim or min_sim is None:
                    better_iso.append(item)

            merged=better_iso+top_similar
            merged=sorted(merged,key=lambda x:x["score"],reverse=True)[:TOP_N]
            top_similar=merged
        core_entities={item["name"] for item in top_similar}
    return list(core_entities)

def recall_triples(entity_list:List[str])->List[dict]:
    global neo4j_driver
    # if not entity_list or not neo4j_driver:
    #     print(f"entity_list/neo4j_driver 无效")
    #     return []
    # if not entity_list:
    #     print(f"entity_list无效")
    #     return []
    # if not neo4j_driver:
    #     print(f"neo4j_driver 无效")
    #     return []
    cypher="""
    with $entity_list as name_list
    match (n:Entity) where n.name in name_list
    with collect(n) as query_nodes
    unwind query_nodes as start_node
    
    match path=(start_node)-[*1..1]-(end:Entity)
    where start_node <> end
    
    return distinct
      start_node.name as head,
      [r in relationships(path) | type (r)] as rel_chain,
      end.name as tail,
      length(path) as hop_count,
      apoc.text.join([node in nodes(path)|node.name],'->') as node_path,
      apoc.text.join([r in relationships(path)|type(r)],'->') as rel_path
    order by hop_count asc,start_node.name asc      
    """
    try:
        with neo4j_driver.session() as session:
            result=session.run(
                cypher,
                entity_list=entity_list
            )
            triples=[]
            for r in result:
                triple={
                    "head":r["head"],
                    "tail":r["tail"],
                    "hop_count":r["hop_count"],
                    "node_path":r["node_path"]
                }
                if r["hop_count"]==1:
                    triple["rel"]=r["rel_chain"][0]
                else:
                    triple["rel_chain"]=r["rel_chain"]
                    triple["rel_path"]=r["rel_path"]
                triples.append(triple)
            # print(f"Neo4j路径召回完成：实体数{len(entity_list)}，路径{len(triples)}条")
            return triples
    except Exception as e:
        print(f"neo4j召回三元组失败:{e}")
        return[]

def rank_triples(question:str,triples:List[dict],top_n:int=TOP_N_TRIPLES)->List[dict]:
    global model
    # print(f"rank_triples{triples}")
    if not question or not triples:
        return []
    question_emb=model.encode(question,convert_to_numpy=True)
    # if len(question_emb)>TARGET_DIM:
    #     question_emb=question_emb[:TARGET_DIM]
    # elif len(question_emb)<TARGET_DIM:
    #     question_emb=np.pad(question_emb,(0,TARGET_DIM-len(question_emb)),mode="constant")
    norm=np.linalg.norm(question_emb)
    if norm>1e-6:
        question_emb=question_emb/norm

    triple_sim_list=[]
    for triple in triples:
        try:
            text=f"{triple['head']} {triple['rel']} {triple['tail']}"
            # print(text)
            t_emb=model.encode(text,convert_to_numpy=True)
            # if len(t_emb)>TARGET_DIM:
            #     t_emb=t_emb[:TARGET_DIM]
            # elif len(t_emb)<TARGET_DIM:
            #     t_emb=np.pad(t_emb,(0,TARGET_DIM-len(t_emb)),mode="constant")
            norm=np.linalg.norm(t_emb)
            if norm>1e-6:
                t_emb=t_emb/norm
            sim=cosine_similarity(question_emb.reshape(1,-1),t_emb.reshape(1,-1))[0][0]
            triple_sim_list.append({"triple":triple,"similarity":sim})
        except Exception as e:
            print(f"计算路径相似度失败:{e}")
            continue
    triple_sim_list.sort(key=lambda x:x["similarity"],reverse=True)
    return [item["triple"] for item in triple_sim_list[:top_n]]

def format_llm_prompt(triples:List[dict])->str:
    if not triples:
        return f"未检索到相关知识图谱信息，请直接回答。"
    prompt="【知识图谱相关信息】\n"
    for idx,triple in enumerate(triples,1):
        prompt+=f"{idx}. {triple['head']} {triple['rel']} {triple['tail']}\n"
    prompt+=f"\n【回答要求】\n基于以上事实回答，逻辑清晰、语言简洁，无相关信息请注明。"
    return prompt

if __name__=="__main__":
    init()
