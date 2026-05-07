from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
import uvicorn

# 导入你已经在 query.py 中写好的链构建函数
from query import build_chain

# 声明一个全局变量，用于在内存中常驻我们的 RAG 链
qa_chain = None

# 使用 lifespan 管理应用的生命周期（在启动时加载模型，关闭时清理）
@asynccontextmanager
async def lifespan(app: FastAPI):
    global qa_chain
    print("====================================")
    print("正在加载向量知识库和 LLM 模型...")
    try:
        qa_chain = build_chain()
        print("✅ 系统初始化完成！RAG API 已就绪。")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
    print("====================================")
    
    yield  # 这里是应用运行的时间段
    
    print("系统关闭，正在清理资源...")



# 初始化 FastAPI 应用
app = FastAPI(
    title="ICU-RAG API",
    description="重症监护临床决策支持系统后台 API",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/", summary="根目录重定向")
async def root():
    return RedirectResponse(url="/docs")

# 定义请求的 JSON 数据格式
class QueryRequest(BaseModel):
    question: str

# 定义响应的 JSON 数据格式
class QueryResponse(BaseModel):
    question: str
    answer: str

# 创建 POST 路由来接收提问
@app.post("/ask", response_model=QueryResponse, summary="向 ICU RAG 助手提问")
async def ask_question(request: QueryRequest):
    # 确保链已经成功加载
    if qa_chain is None:
        raise HTTPException(status_code=503, detail="模型尚未初始化完成，请稍后再试。")
    
    try:
        # 调用 RAG 链获取回答
        # 注意：这里我们使用 invoke 来触发大模型思考
        result = qa_chain.invoke(request.question)
        
        return QueryResponse(
            question=request.question,
            answer=result
        )
    except Exception as e:
        # 如果大模型 API 报错或网络异常，返回 500 错误
        raise HTTPException(status_code=500, detail=f"推理过程发生错误: {str(e)}")

if __name__ == "__main__":
    # 启动服务器，并开启 reload 以便在修改代码时自动重启
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)