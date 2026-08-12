import json
from copy import deepcopy

# ====== 配置路径 ======
input_path = "E:\edge_download\pre-check\\12b-Batch4-Phase-B-deepseek-32b-top-3-n-1.json"
output_path = "E:\edge_download\pre-check\\12b-Batch4-Phase-B-deepseek-32b-top-3-n-1-fixed_factoid.json"

with open(input_path, "r", encoding="utf-8") as f:
    data = json.load(f)

new_data = deepcopy(data)

fixed_cnt = 0

for q in new_data.get("questions", []):
    if q.get("type") != "factoid":
        continue

    exact = q.get("exact_answer")

    # 只处理形如 [[A, B, C]] 的情况
    if (
        isinstance(exact, list)
        and len(exact) == 1
        and isinstance(exact[0], list)
        and len(exact[0]) > 1
    ):
        q["exact_answer"] = [[ans] for ans in exact[0]]
        fixed_cnt += 1

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(new_data, f, ensure_ascii=False, indent=2)

print(f"✅ Done. Fixed {fixed_cnt} factoid questions.")
print(f"📄 Saved to: {output_path}")
