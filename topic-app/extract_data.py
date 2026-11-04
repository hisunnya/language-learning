"""从 Excel 提取数据，生成 topics.js 供网页使用"""
import json
from openpyxl import load_workbook

wb = load_workbook('/workspace/初中生每日话题.xlsx')
ws = wb.active

topics = []
categories_set = set()
for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True), 1):
    if not row[0]:
        continue
    num, cat, topic, hint = row
    categories_set.add(cat)
    topics.append({
        "id": int(num),
        "category": cat,
        "topic": topic,
        "hint": hint,
    })

# 写 JS 文件
js = "// 从 Excel 自动生成\n"
js += f"export const TOPICS = {json.dumps(topics, ensure_ascii=False, indent=2)};\n\n"
js += f"export const CATEGORIES = {json.dumps(sorted(categories_set), ensure_ascii=False, indent=2)};\n"
js += f"export const TOTAL = {len(topics)};\n"

with open('/workspace/topic-app/topics.js', 'w', encoding='utf-8') as f:
    f.write(js)

print(f"已写入 {len(topics)} 个话题，{len(categories_set)} 个分类")
print(f"分类: {sorted(categories_set)}")
