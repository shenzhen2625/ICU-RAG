import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.document_loaders import PyMuPDFLoader, TextLoader, DirectoryLoader

from config import *
import trafilatura
import time

headers = {"User-Agent": "Mozilla/5.0"}

def fetch_and_extract(url):
    """下载并提取文本内容"""
    downloaded = trafilatura.fetch_url(url)
    return trafilatura.extract(downloaded) if downloaded else None

def load_urls_with_subpages(max_subpages=3):
    """从 urls.txt 动态读取并爬取（包含次级页面）"""
    docs = []
    url_file = os.path.join(DATA_DIR, "urls.txt")
    if not os.path.exists(url_file):
        return docs

    with open(url_file, "r", encoding="utf-8") as f:
        urls = [x.strip() for x in f.readlines() if x.strip()]

    for base_url in urls:
        print("Dynamic Fetching Main:", base_url)
        text = fetch_and_extract(base_url)
        if text:
            docs.append(Document(page_content=text, metadata={"source": base_url}))
        
        # 获取次级页面
        try:
            r = requests.get(base_url, headers=headers, timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            base_domain = urlparse(base_url).netloc
            links = set()
            for a in soup.find_all('a', href=True):
                full_url = urljoin(base_url, a['href'])
                if urlparse(full_url).netloc == base_domain:
                    links.add(full_url)
            
            for i, sub_url in enumerate(list(links)[:max_subpages]):
                print(f"Dynamic Fetching Sub ({i+1}):", sub_url)
                sub_text = fetch_and_extract(sub_url)
                if sub_text:
                    docs.append(Document(page_content=sub_text, metadata={"source": sub_url}))
                time.sleep(1)
        except Exception as e:
            print(f"Failed to fetch subpages for {base_url}: {e}")

    return docs

def load_web_txts():
    """专门解析爬虫保存在 data/web/ 里的 txt 文件"""
    web_dir = os.path.join(DATA_DIR, "web")
    if not os.path.exists(web_dir):
        return []
    # 使用 DirectoryLoader 批量加载 txt，并指定编码
    loader = DirectoryLoader(web_dir, glob="**/*.txt", loader_cls=TextLoader, loader_kwargs={'autodetect_encoding': True})
    return loader.load()

def load_pdfs():
    docs = []
    path = os.path.join(DATA_DIR, "pdf")
    
    # 如果文件夹不存在，自动创建并提示
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
        print(f"已自动创建文件夹: {path}. 暂无PDF文件可加载。")
        return docs

    # 遍历并使用 PyMuPDF 读取每个 PDF
    for filename in os.listdir(path):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(path, filename)
            print(f"Loading PDF: {filename}")
            try:
                loader = PyMuPDFLoader(pdf_path)
                docs.extend(loader.load())
            except Exception as e:
                print(f"解析 PDF 失败 [{filename}]: {e}")
                
    return docs

def load_cases():
    docs = []
    case_dir = os.path.join(DATA_DIR, "cases")
    if not os.path.exists(case_dir):
        return docs
    for f in os.listdir(case_dir):
        if f.endswith(".txt"):
            loader = TextLoader(os.path.join(case_dir, f), encoding="utf-8")
            docs.extend(loader.load())
    return docs

def build_index():
    print("Loading documents...")
    docs = []
    
    docs.extend(load_urls_with_subpages())
    docs.extend(load_web_txts()) # 现在可以正确解析 web 文件夹了
    docs.extend(load_pdfs())
    docs.extend(load_cases())

    print("Total docs before splitting:", len(docs))

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
    )
    split_docs = splitter.split_documents(docs)
    print("Chunks after splitting:", len(split_docs))

    embeddings = DashScopeEmbeddings(
        model=EMBEDDING_MODEL,
        dashscope_api_key=DASHSCOPE_API_KEY
    )

    vector_store = FAISS.from_documents(split_docs, embeddings)
    vector_store.save_local(VECTOR_STORE_PATH)
    print("Vector DB saved.")

if __name__ == "__main__":
    build_index()