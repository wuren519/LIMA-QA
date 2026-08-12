import json
import torch
from transformers import AutoTokenizer, AutoModel

# 加载模型
query_tokenizer = AutoTokenizer.from_pretrained("/workspace/code/BriefContext/models/MedCPT-Query-Encoder")
query_model = AutoModel.from_pretrained("/workspace/code/BriefContext/models/MedCPT-Query-Encoder")

doc_tokenizer = AutoTokenizer.from_pretrained("/workspace/code/BriefContext/models/MedCPT-Article-Encoder")
doc_model = AutoModel.from_pretrained("/workspace/code/BriefContext/models/MedCPT-Article-Encoder")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
query_model.to(device)
doc_model.to(device)

def encode_query(query: str):
    """编码查询"""
    with torch.no_grad():
        encoded = query_tokenizer(
            query,
            truncation=True,
            padding=True,
            return_tensors="pt",
            max_length=64
        ).to(device)
        embeds = query_model(**encoded).last_hidden_state[:, 0, :]
    return embeds.cpu()

def encode_snippets(snippets: list):
    """编码一组 snippet 文本"""
    texts = [s["text"] for s in snippets]
    with torch.no_grad():
        encoded = doc_tokenizer(
            texts,
            truncation=True,
            padding=True,
            return_tensors="pt",
            max_length=512
        ).to(device)
        embeds = doc_model(**encoded).last_hidden_state[:, 0, :]
    return embeds.cpu()

def check_litm(original_snippets, reranked_snippets, top_k=3):
    """
    检查是否发生 lost-in-the-middle 问题
    - 如果原始中间片段被重排提到前 top_k，认为发生 LITM
    """
    n = len(original_snippets)
    if n <= 4:  # 太少就不检查
        return False

    middle_indices = list(range(2, n-2))  # 中间区域
    middle_snippets = [original_snippets[i] for i in middle_indices]

    top_snippets = reranked_snippets[:top_k]

    # 判断中间的 snippet 是否跑到前面
    for ms in middle_snippets:
        if ms in top_snippets:
            return True
    return False
# def rerank_question(question: dict):
#     """对单个 question 的 snippets 重排序并检查 LITM"""
#     if not question.get("snippets"):
#         # 没有 snippets 时，保证 lost_in_the_middle = False
#         question["lost_in_the_middle"] = False
#         return question  # 没有 snippets 就跳过

#     query = question["body"]
#     snippets = question["snippets"]

#     # 保存原始顺序到 snippets 字段（不动）
#     # 重排结果放到 snippets_reranked
#     question["snippets_reranked"] = snippets.copy()  

#     # 编码 query 和 snippets
#     q_emb = encode_query(query)  # [1, d]
#     s_embs = encode_snippets(snippets)  # [N, d]

#     # 计算相似度 (内积)
#     scores = torch.matmul(s_embs, q_emb.T).squeeze(1)  # [N]

#     # 根据分数排序
#     sorted_indices = torch.argsort(scores, descending=True).tolist()
#     reranked_snippets = [snippets[i] for i in sorted_indices]

#     # 将重排结果放到 snippets_reranked
#     question["snippets_reranked"] = reranked_snippets

#     # 检查 LITM（使用原始 snippets 和重排结果）
#     litm_flag = check_litm(snippets, reranked_snippets, top_k=3)
#     question["lost_in_the_middle"] = litm_flag

#     return question

def rerank_question(question: dict):
    """对单个 question 的 snippets 重排序并检查 LITM"""
    if not question.get("snippets"):
        # 没有 snippets 时，保证 lost_in_the_middle = False
        question["lost_in_the_middle"] = False
        return question  # 没有 snippets 就跳过

    query = question["body"]
    snippets = question["snippets"]

    # 保存原始顺序
    question["snippets_reranked"] = snippets  

    # 编码 query 和 snippets
    q_emb = encode_query(query)  # [1, d]
    s_embs = encode_snippets(snippets)  # [N, d]

    # 计算相似度 (内积)
    scores = torch.matmul(s_embs, q_emb.T).squeeze(1)  # [N]

    # 根据分数排序
    sorted_indices = torch.argsort(scores, descending=True).tolist()
    reranked_snippets = [snippets[i] for i in sorted_indices]

    # 用重排结果覆盖 snippets
    question["snippets"] = reranked_snippets

    litm_flag = check_litm(snippets, reranked_snippets, top_k=3)
    # litm_flag = check_litm(reranked_snippets, snippets, top_k=3)

    question["lost_in_the_middle"] = litm_flag

    return question

def main(fin, fout):
    with open(fin, "r") as f:
        data = json.load(f)

    for q in data["questions"]:
        q = rerank_question(q)

    with open(fout, "w") as f:
        json.dump(data, f, indent=2)

    print(f"✅ 保存完成: {fout}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, required=True, help="输入 PubMed JSON 文件路径")
    parser.add_argument("--output", type=str, required=True, help="输出文件路径")
    args = parser.parse_args()

    main(args.input, args.output)