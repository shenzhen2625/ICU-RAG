# ICU-RAG 工程 Makefile

# 声明伪目标，防止与同名文件冲突
.PHONY: install build run clean help

# 默认执行 help
default: help

# 安装通义千问大模型和本地PDF处理所需的依赖
install:
	pip install langchain langchain-community faiss-cpu dashscope pypdf tiktoken

# 读取 data/ 目录下的 ICU 指南和病历，并构建 FAISS 向量索引
build:
	python build_index.py

# 启动 RAG 查询脚本，进行 ICU 查房问答
run:
	python query.py

# 清理 Python 缓存和生成的 FAISS 向量数据库（当您需要重新构建索引时使用）
clean:
	rm -rf __pycache__
	rm -rf faiss_index

# 打印帮助信息
help:
	@echo "================================================="
	@echo "          ICU-RAG 医疗问答系统 Makefile          "
	@echo "================================================="
	@echo "可用命令:"
	@echo "  make install - 安装项目所需的所有 Python 依赖"
	@echo "  make build   - 读取 data/ 下的 PDF 文件并构建 FAISS 向量索引"
	@echo "  make run     - 启动 RAG 查询脚本 (query.py)"
	@echo "  make clean   - 清理缓存和已生成的 faiss_index 文件夹"
	@echo "  make help    - 显示此帮助信息"
	@echo "================================================="