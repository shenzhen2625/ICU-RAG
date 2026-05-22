import os
import requests
import time

# 配置 API 和保存路径
API_URL = "https://wsearch.nlm.nih.gov/ws/query"
XML_DIR = os.path.join("data", "xml")

# 我们关注的核心医学关键词 (系统会根据这些词去查百科)
TARGET_KEYWORDS = [
    "delirium", "confusion", "hallucination", 
    "agitation", "intensive care", "sedation", "encephalopathy"
]

def download_from_api():
    if not os.path.exists(XML_DIR):
        os.makedirs(XML_DIR, exist_ok=True)
        print(f"已创建文件夹: {XML_DIR}")

    print("开始通过 MedlinePlus API 批量获取数据...\n")

    for keyword in TARGET_KEYWORDS:
        print(f"正在检索关键词: '{keyword}'")
        params = {
            "db": "healthTopics",
            "term": keyword,
            "retmax": 20,       # 每个关键词获取前 20 个最相关的疾病词条
            "rettype": "topic"  # 获取包含 FullSummary 的完整结构
        }
        
        try:
            # 发起请求
            response = requests.get(API_URL, params=params, timeout=15)
            response.raise_for_status()
            
            # 保存为 XML 文件
            safe_keyword = keyword.replace(" ", "_")
            file_name = f"api_{safe_keyword}.xml"
            file_path = os.path.join(XML_DIR, file_name)
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(response.text)
                
            print(f"  -> 成功保存: {file_name}")
            
            # 遵守 NLM 官方要求的 API 调用频率限制
            time.sleep(1) 
            
        except Exception as e:
            print(f"  -> 请求失败 [{keyword}]: {e}")

if __name__ == "__main__":
    download_from_api()