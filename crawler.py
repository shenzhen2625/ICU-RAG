import requests
import trafilatura
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
import time

DATA_DIR = "data/web"
os.makedirs(DATA_DIR, exist_ok=True)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

urls = [
    "https://www.who.int/health-topics/sepsis",
    "https://www.who.int/health-topics/respiratory-distress"
    # Deranged Physiology (极其硬核的澳洲 ICU 专科医学笔记，非常适合 RAG，纯文本为主)
    "https://derangedphysiology.com/main/core-topics-intensive-care/mechanical-ventilation-0",
    "https://derangedphysiology.com/main/core-topics-intensive-care/sepsis-and-infection",

    # Life in the Fast Lane (LITFL - 全球知名的急诊与重症博客)
    "https://litfl.com/sepsis-management-and-resuscitation/",
    "https://litfl.com/acute-respiratory-distress-syndrome-ards/",

    # 维基百科医学版块 (极其稳定，结构化好，适合作为基础医学定义库)
    "https://en.wikipedia.org/wiki/Sepsis",
    "https://en.wikipedia.org/wiki/Mechanical_ventilation",
    
    # MDCalc (临床评分系统说明，如 SOFA score，适合临床决策辅助)
    "https://www.mdcalc.com/calc/691/sofa-score-for-sepsis"
]

def get_sub_links(base_url, max_links=5):
    """提取主页面下的同域名次级链接"""
    print(f"Extracting sub-links from: {base_url}")
    try:
        r = requests.get(base_url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        links = set()
        base_domain = urlparse(base_url).netloc
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            full_url = urljoin(base_url, href)
            # 只保留同域名的链接（避免爬到外部网站）
            if urlparse(full_url).netloc == base_domain:
                links.add(full_url)
                
        return list(links)[:max_links] # 限制爬取数量避免过多
    except Exception as e:
        print(f"Error extracting links from {base_url}: {e}")
        return []

def fetch_page(url):
    print("Fetching:", url)
    try:
        r = requests.get(url, headers=headers, timeout=15)
        # 使用 trafilatura 提取正文内容（去除导航栏、广告等无关HTML）
        text = trafilatura.extract(r.text)
        return text
    except Exception as e:
        print("Error fetching:", e)
        return None

def save_doc(text, name):
    if not text: return
    path = os.path.join(DATA_DIR, name + ".txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

def crawl():
    for i, base_url in enumerate(urls):
        # 1. 爬取主页面
        main_text = fetch_page(base_url)
        if main_text:
            save_doc(main_text, f"site_{i}_main")
        
        # 2. 获取并爬取次级页面
        sub_links = get_sub_links(base_url)
        for j, sub_url in enumerate(sub_links):
            time.sleep(1) # 礼貌爬取，防止被封
            sub_text = fetch_page(sub_url)
            if sub_text:
                save_doc(sub_text, f"site_{i}_sub_{j}")

if __name__ == "__main__":
    crawl()