# 题库数据生成脚本

从 CRAC 官方题库 PDF 生成 `data/bank.json` 与 `data/bank.js`。

```bash
# 1) 解压官方题库包
unzip ham-bank.zip -d bank/

# 2) 解析四份 PDF -> merged_raw.json
python3 parse_bank.py

# 3) 提取 53 张附图并映射到题号 -> images/
python3 extract_images.py

# 4) 生成 data/bank.json
python3 build_data.py

# 5) 生成 data/bank.js（让 file:// 双击也能用）
cd ../data && python3 -c "
import json
d=json.load(open('bank.json'))
open('bank.js','w',encoding='utf-8').write('window.BANK = '+json.dumps(d,ensure_ascii=False,separators=(',',':'))+';')
"
```

依赖：`pdfplumber`、`pypdf`（`pip install pdfplumber pypdf`），以及系统的 `pdftotext`。
