import pandas as pd
import numpy as np
import networkx as nx
import sys
import os

# Add the project root directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from src.knowledge_graph.config import load_config
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import leidenalg as la
import igraph as ig
import requests
import argparse
from collections import defaultdict
import random
import matplotlib.pyplot as plt
from collections import Counter
import json
import re

plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']  # 支持中文+英文
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
plt.rcParams['font.family'] = 'sans-serif'

# -----------------------------
# LLM调用（阿里云）
# -----------------------------
def call_llm(model, user_prompt, api_key, system_prompt=None, max_tokens=1000, temperature=0.2, base_url=None):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f"Bearer {api_key}"
    }
    messages = []
    if system_prompt:
        messages.append({'role': 'system', 'content': system_prompt})
    messages.append({'role': 'user', 'content': user_prompt})

    payload = {
        'model': model,
        'messages': messages,
        'max_tokens': max_tokens,
        'temperature': temperature,
        'stream': False
    }

    api_url = f"{base_url.rstrip('/')}/chat/completions"

    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except requests.exceptions.RequestException as e:
        raise Exception(f"LLM 调用失败: {str(e)} | 内容: {response.text if 'response' in locals() else '无响应'}")


# -----------------------------
# 构建图
# -----------------------------
def build_graph(csv_path):
    df = pd.read_csv(csv_path, header=0, encoding="utf-8-sig")
    df.columns = ['subject', 'predicate', 'object']
    G = nx.Graph()
    all_entities = set(df['subject']).union(set(df['object']))
    for entity in all_entities:
        G.add_node(entity, name=entity)
    for _, row in df.iterrows():
        G.add_edge(row['subject'], row['object'], relation=row['predicate'])
    return G, df, all_entities


# -----------------------------
# 文本 embedding
# -----------------------------
print(f"正在准备文本模型")
text_model = SentenceTransformer("shibing624/text2vec-base-chinese")
print(f"模型准备完毕")

def text_vectorize(text, model, dim=128):
    vec = model.encode(text, convert_to_numpy=True)
    if len(vec) > dim:
        vec = vec[:dim]
    elif len(vec) < dim:
        vec = np.pad(vec, (0, dim - len(vec)))
    vec = vec / np.linalg.norm(vec) if np.linalg.norm(vec) != 0 else vec
    return vec


# -----------------------------
# 处理小社区
# -----------------------------
def merge_small_communities(G,community_dict, min_community_size=5):
    community_nodes=defaultdict(list)
    for node, cid in community_dict.items():
        community_nodes[cid].append(node)

    large_community={cid for cid,nodes in community_nodes.items() if len(nodes)>=min_community_size}
    small_community={cid for cid,nodes in community_nodes.items() if len(nodes)<min_community_size}
    print(f"共有{len(community_nodes)}个社区，其中{len(large_community)}个大社区，{len(small_community)}个小社区")

    new_community=dict(community_dict)

    for cid in small_community:
        for node in community_nodes[cid]:
            neighbor_cids=[]
            for nb in G.neighbors(node):
                if nb in community_dict and community_dict[nb] in large_community:
                    # print(nb)
                    neighbor_cids.append(community_dict[nb])
            if neighbor_cids:
                new_community[node]=max(set(neighbor_cids),key=neighbor_cids.count)
            else:
                new_community[node]=-1
    return new_community


# -----------------------------
# Leiden 社区检测
# -----------------------------
def leiden_communities(G, min_community_size=5):
    """
    Args:
        G:图
        resolution:分辨率参数，控制社区划分的精细度，值越大社区越细碎
        min_community_size:最小社区节点数，过滤掉节点数少于该值的小社区
    """
    mapping = {n: i for i, n in enumerate(G.nodes())}
    inv_mapping = {i: n for n, i in mapping.items()}
    edges = [(mapping[u], mapping[v]) for u, v in G.edges()]
    g = ig.Graph(edges=edges, directed=False)

    partition = la.find_partition(g, la.ModularityVertexPartition)
    print('-----------------------------------')
    print(partition)
    print('-----------------------------------')

    sizes={}
    raw_comm={}
    # community_dict = {}
    for idx, community in enumerate(partition):
        sizes[idx]=len(community)
        for node_id in community:
            raw_comm[inv_mapping[node_id]]=idx
        # if len(community) >= min_community_size:
        #     for node_id in community:
        #         community_dict[inv_mapping[node_id]] = idx
        # print(f"社区{idx}节点个数为{len(community)}")

    community_dict=merge_small_communities(G,raw_comm,min_community_size)
    return community_dict


def communities_statistics(community_dict):
    """
    查看社区情况
    Args:
        community_dict: 最终的社区字典 {节点: 社区编号}
    """
    cid2nodes = defaultdict(list)
    for node, cid in community_dict.items():
        cid2nodes[cid].append(node)
    # 打印，查看每个社区有谁
    print("\n" + "="*50)
    print("最终社区节点清单（cid: 节点列表）：")
    print("="*50)
    for cid in sorted(cid2nodes.keys()):
        nodes = sorted(cid2nodes[cid])
        if cid == -1:
            print(f"孤立节点(cid=-1): {nodes}")
        else:
            print(f"社区{cid:2d}: {nodes} (共{len(nodes)}个节点)")
    print("="*50 + "\n")


# -----------------------------
# 选取度数最多的k个节点
# -----------------------------
def top_degree_nodes(G,nodes,k=15):
    subG=G.subgraph(nodes)
    return sorted(subG.degree(), key=lambda x: x[1], reverse=True)[:k]


# -----------------------------
# 选取出现频次最高的k个关系
# -----------------------------
def top_relations(G,nodes,k=8):
    relations = []
    for u, v in G.subgraph(nodes).edges():
        if "relation" in G[u][v]:
            relations.append(G[u][v]["relation"])
    print(f"关系清单：{Counter(relations).most_common(k)}")
    return Counter(relations).most_common(k)


# -----------------------------
# 选取max_path条路径（三节点俩关系）
# -----------------------------
def sample_paths(G,nodes,max_paths=3):
    subG=G.subgraph(nodes)
    paths=[]
    node_list=list(subG.nodes())

    for u in node_list[:10]:
        for v in subG.neighbors(u):
            for w in subG.neighbors(v):
                if u!=w:
                    r1=subG[u][v].get("relation","")
                    r2=subG[v][w].get("relation","")
                    paths.append(f"{u}->{r1}->{v}->{r2}->{w}")
                if len(paths)>=max_paths:
                    return  paths
    print(paths)
    return paths


# -----------------------------
# 社区总结(LLM生成)
# -----------------------------
def generate_community_summaries_llm(G, community_dict, llm_model, api_key, base_url):
    communities=defaultdict(list)
    for node,cid in community_dict.items():
        if cid>=0:
            communities[cid].append(node)

    summaries={}
    for cid,nodes in communities.items():
        top_nodes=top_degree_nodes(G,nodes,k=15)
        top_rels=top_relations(G,nodes,k=8)
        paths=sample_paths(G,nodes,max_paths=3)

        prompt=f"""
你正在分析一个知识图谱中的【一个社区子图】。
该社区代表一个相对独立的知识领域，请你抽象总结该社区的【主题语义】。
【1】该社区中最核心的实体：
{chr(10).join([f"-{n[0]}" for n in top_nodes])}
【2】该社区中最常见的关系类型
{chr(10).join([f"-{r[0]}({c}次)" for r,c in top_rels])}
【3】该社区中典型结构路径
{chr(10).join([f"-{p}" for p in paths])}

请完成：
1.用1-2句话概括该社区的【领域主题】
2.说明主要关注的对象和业务方向
要求：
-使用中文回答
-不超过100字
-偏“领域描述”，用于语义检索
"""
        summary=call_llm(
            model=llm_model,
            user_prompt=prompt,
            system_prompt="你是知识图谱社区语义总结专家",
            api_key=api_key,
            base_url=base_url,
            temperature=0.2,
            max_tokens=150
        )

        summaries[cid]=summary.strip()
        print(f"社区{cid}主题：{summary}")
    return summaries


# -----------------------------
# 社区总结嵌入
# -----------------------------
def embed_summaries(summaries, model):
    summary_emb = {}
    for cid, text in summaries.items():
        summary_emb[cid] = text_vectorize(text, model)
    return summary_emb


def save_community_info(
        community_dict,
        community_summaries,
        community_embeddings,
        output_file="community_info.json"
):
    communities=defaultdict(list)
    isolated_nodes=[]
    for node,cid in community_dict.items():
        if cid>=0:
            communities[cid].append(node)
        else:
            isolated_nodes.append(node)
    data={
        "communities":{},
        "isolated_nodes":isolated_nodes
    }
    for cid in communities:
        data["communities"][cid]={
            "summary":community_summaries[cid],
            "embedding":community_embeddings[cid].tolist(),
            "nodes":communities[cid]
        }

    with open(output_file, "w", encoding="utf-8-sig") as f:
        json.dump(data,f,ensure_ascii=False, indent=2)

    print(f"社区信息保存完毕: {output_file},社区数={len(communities)},孤立节点数={len(isolated_nodes)}")



if __name__ == "__main__":
    print("开始执行社区检测")
    parser = argparse.ArgumentParser(description='Community Information Summary')
    parser.add_argument('--config', type=str, default='config.toml', help='Path to configuration file')
    args = parser.parse_args()
    
    # Resolve config file path relative to project root
    if not os.path.isabs(args.config):
        config_path = os.path.join(project_root, args.config)
    else:
        config_path = args.config
    
    config = load_config(config_path)
    print(f"配置文件加载完毕: {args.config}")

    csv_path = r"data\knowledge_graph.csv"
    
    llm_model = config["llm"]["model"]
    api_key = config["llm"]["api_key"]
    base_url = config["llm"]["base_url"]

    G, df, all_entities = build_graph(csv_path)
    print(f"Graph构建完成，节点数={len(G.nodes())}, 边数={len(G.edges())}")

    # Leiden 社区检测
    community_dict = leiden_communities(G, min_community_size=5)
    print(f"检测到 {len(set(community_dict.values()))} 个社区")

    communities_statistics(community_dict)

    #LLM生成社区summary
    summaries = generate_community_summaries_llm(G, community_dict, llm_model, api_key, base_url)
    print("LLM 社区 summary 生成完成")

    # Summary embedding
    summary_emb = embed_summaries(summaries, text_model)
    print("社区 summary embedding 完成")

    save_community_info(community_dict, summaries, summary_emb)

