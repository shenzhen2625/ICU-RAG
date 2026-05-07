# ICU-RAG: 重症监护临床决策支持系统

## 项目简介

ICU-RAG 是一个基于检索增强生成 (Retrieval-Augmented Generation, RAG) 技术的重症监护 (Intensive Care Unit) 临床决策支持系统。该系统通过爬取权威医学网站的数据，构建向量索引，并提供基于大语言模型的智能查询接口，帮助医疗专业人员快速获取相关临床信息和决策支持。

## 主要功能

- **数据爬取**: 自动爬取 WHO、Deranged Physiology、LITFL、Wikipedia、MDCalc 等权威医学网站的 ICU 相关内容。
- **向量索引构建**: 使用 FAISS 和 DashScope 嵌入模型构建高效的向量索引。
- **智能查询**: 基于 LangChain 和通义千问大模型，提供精准的临床问题解答。
- **REST API**: 提供 FastAPI 构建的 RESTful API 接口，便于集成到其他系统中。

## 项目结构

```
ICU-RAG/
├── api.py              # FastAPI 应用主文件
├── build_index.py      # 向量索引构建脚本
├── config.py           # 配置文件
├── crawler.py          # 网页爬虫脚本
├── prompt.py           # 提示模板
├── query.py            # RAG 查询链构建
├── Makefile            # 构建脚本
├── readme.md           # 项目说明文档
├── data/               # 数据目录
│   ├── urls.txt        # URL 列表
│   ├── pdf/            # PDF 文件目录
│   └── web/            # 网页文本数据
└── vector_store/       # 向量存储目录
    └── index.faiss     # FAISS 向量索引
```

## 安装与配置

### 环境要求

- Python 3.8+
- pip

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置 API 密钥

在 `config.py` 文件中设置你的 DashScope API 密钥：

```python
DASHSCOPE_API_KEY = "your_dashscope_api_key_here"
```

## 使用方法

### 使用 Makefile 快速操作

项目提供了 Makefile 来简化常见操作。你可以使用以下命令：

- **安装依赖**:
  ```bash
  make install
  ```

- **构建向量索引**:
  ```bash
  make build
  ```

- **启动查询脚本**:
  ```bash
  make run
  ```

- **清理缓存和索引**:
  ```bash
  make clean
  ```

- **查看帮助**:
  ```bash
  make help
  ```

### 手动操作步骤

如果你不使用 Makefile，可以按照以下步骤手动操作：

#### 1. 数据爬取

运行爬虫脚本抓取数据：

```bash
python crawler.py
```

#### 2. 构建向量索引

运行索引构建脚本：

```bash
python build_index.py
```

#### 3. 启动 API 服务

启动 FastAPI 服务：

```bash
python api.py
```

服务将在 `http://localhost:8000` 启动，你可以访问 `http://localhost:8000/docs` 查看 API 文档。

#### 4. 查询示例

使用 curl 发送查询请求：

```bash
curl -X POST "http://localhost:8000/query" \
     -H "Content-Type: application/json" \
     -d '{"question": "什么是败血症？"}'
```

## API 接口

### POST /query

查询 ICU 相关问题。

**请求体:**

```json
{
  "question": "string"
}
```

**响应:**

```json
{
  "question": "string",
  "answer": "string"
}
```

## 技术栈

- **后端框架**: FastAPI
- **向量数据库**: FAISS
- **嵌入模型**: DashScope Text Embedding
- **大语言模型**: 通义千问 (Qwen)
- **框架**: LangChain
- **数据处理**: BeautifulSoup, Trafilatura
