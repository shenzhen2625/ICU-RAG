import os
import glob
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

XML_DIR = os.path.join("data", "xml")
OUTPUT_DIR = os.path.join("data", "medline")

# 我们的目标关键词（仅用于过滤非 API 下载的全量文件）
TARGET_KEYWORDS = [
    "delirium", "confusion", "hallucination", 
    "agitation", "intensive care", "sedation", "encephalopathy"
]

# 记录已经保存过的词条，防重
processed_titles = set()

def clean_html(raw_html):
    if not raw_html:
        return ""
    return BeautifulSoup(raw_html, "html.parser").get_text(separator="\n").strip()

def save_topic(title, raw_summary, is_api_file):
    global processed_titles
    if not title or title in processed_titles:
        return 0  
    
    clean_summary = clean_html(raw_summary)
    # 【放宽限制】：只要有超过 10 个字符的内容，我们就保存，绝不放过任何线索！
    if len(clean_summary) < 10:
        return 0

    full_text = f"Title: {title}\n\nSummary:\n{clean_summary}"
    
    # 只有非 API 文件才需要经过关键词严格过滤
    if not is_api_file:
        full_text_lower = full_text.lower()
        if not any(kw in full_text_lower for kw in TARGET_KEYWORDS):
            return 0
    
    # 安全的文件名
    safe_title = "".join(c if c.isalnum() else "_" for c in title)
    file_name = f"topic_{safe_title}.txt"
    file_path = os.path.join(OUTPUT_DIR, file_name)
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(full_text)
        
    processed_titles.add(title) 
    return 1

def parse_and_filter_medline():
    if not os.path.exists(XML_DIR):
        print(f"错误: 未找到 {XML_DIR}。")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    xml_files = glob.glob(os.path.join(XML_DIR, "*.xml"))
    
    if not xml_files:
        print("没有找到 XML 文件。")
        return

    print(f"准备解析 {len(xml_files)} 个 XML 文件...\n")
    total_saved = 0

    for xml_file in xml_files:
        is_api_file = os.path.basename(xml_file).startswith("api_")
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
        except Exception as e:
            print(f" -> 解析失败 {os.path.basename(xml_file)}: {e}")
            continue 

        file_saved = 0
        
        # 【逻辑 1】处理旧大文件
        for topic in root.findall('.//health-topic'):
            title = topic.get('title')
            summary_elem = topic.find('.//full-summary')
            raw_summary = summary_elem.text if summary_elem is not None else ""
            file_saved += save_topic(title, raw_summary, is_api_file)

        # 【逻辑 2】处理 API 文件（带有终极暴力兜底）
        for doc in root.findall('.//document'):
            title_elem = doc.find(".//content[@name='title']")
            if title_elem is not None and title_elem.text:
                title = title_elem.text
                
                # 依次尝试获取：FullSummary -> snippet -> 兜底获取所有文本
                summary = ""
                summary_elem = doc.find(".//content[@name='FullSummary']")
                snippet_elem = doc.find(".//content[@name='snippet']")
                
                if summary_elem is not None and summary_elem.text:
                    summary = summary_elem.text
                elif snippet_elem is not None and snippet_elem.text:
                    summary = snippet_elem.text
                else:
                    # 如果什么特定标签都没有，把该节点下所有的文字粗暴地拼起来！
                    all_contents = doc.findall(".//content")
                    summary = "\n".join([c.text for c in all_contents if c.text])
                    
                file_saved += save_topic(title, summary, is_api_file)
        
        print(f" -> {os.path.basename(xml_file)} 提取了 {file_saved} 个新词条")
        total_saved += file_saved

    print(f"\n全部解析完成！共去重提取了 {total_saved} 个核心医学词条，存入 '{OUTPUT_DIR}'。")

if __name__ == "__main__":
    parse_and_filter_medline()