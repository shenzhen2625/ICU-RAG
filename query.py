from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import SystemMessage, HumanMessage

from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

from prompt import ICU_PROMPT
from config import *

def load_vector():
    print("正在加载医疗 Embedding 模型和向量库，请稍候...")
    
    model_name = "pritamdeka/S-PubMedBert-MS-MARCO" 
    embeddings = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={'device': 'cpu'}, 
        encode_kwargs={'normalize_embeddings': True}
    )

    vector_store = FAISS.load_local(
        VECTOR_STORE_PATH,
        embeddings,
        allow_dangerous_deserialization=True
    )
    print("向量库加载完毕！")
    return vector_store

def build_chain(vector_store):
    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 15}
    )

    llm = ChatTongyi(
        model_name=LLM_MODEL,
        dashscope_api_key=DASHSCOPE_API_KEY,
        temperature=0
    )

    # 构建 RAG 链
    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | ICU_PROMPT
        | llm
        | StrOutputParser()
    )

    return chain, retriever

# 翻译模块
def translate_query_if_needed(query: str, llm: ChatTongyi) -> str:
    """
    判断并翻译：利用 LLM 直接判断语种。如果是英文直接返回，如果是中文则翻译为医学英文。
    """
    system_prompt = (
        "You are an expert medical translator for an ICU Clinical Decision Support System. "
        "Rule 1: If the user's input is entirely in English, output it EXACTLY as it is. "
        "Rule 2: If the input contains Chinese or other languages, translate it into precise, professional medical English suitable for PubMed keyword retrieval. "
        "Rule 3: ONLY output the final English text. Do not add any explanations, introductory words, quotes, or markdown formatting."
    )
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=query)
    ]
    
    response = llm.invoke(messages)
    return response.content.strip()

if __name__ == "__main__":
    global_vector_store = load_vector()
    qa_chain, global_retriever = build_chain(global_vector_store)

    translator_llm = ChatTongyi(
        model_name=LLM_MODEL,
        dashscope_api_key=DASHSCOPE_API_KEY,
        temperature=0 
    )

    print("\n" + "="*50)
    print("ICU 谵妄 RAG 助手已启动！(输入 'exit' 退出)")
    print("="*50)

    while True:
        q = input("\nICU Question: ")

        if q.lower() == "exit":
            break

        print("\n正在检测语种并处理提问...")
        english_q = translate_query_if_needed(q, translator_llm)

        if english_q != q:
            print(f"已将中文提问转化为英文检索词: {english_q}")

        print("\n正在从医学知识库中检索...")
        docs = global_retriever.invoke(english_q)
        for i, doc in enumerate(docs):
            # 获取 metadata，如果没有 source 则显示 Unknown
            source = doc.metadata.get('source', 'Unknown source')
            clean_source = source.replace("topic_", "").replace(".txt", "")
            
            print(f"[{i+1}] 来源: {clean_source}")
            print(f"内容截取: {doc.page_content[:150]}...\n" + "-"*30)

        print("\n正在生成诊断建议...")
        answer = qa_chain.invoke(english_q)

        print("\n最终回答:\n", answer)