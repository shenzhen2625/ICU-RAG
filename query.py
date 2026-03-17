from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.chat_models import ChatTongyi

from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

from prompt import ICU_PROMPT
from config import *


def load_vector():

    embeddings = DashScopeEmbeddings(
        model=EMBEDDING_MODEL,
        dashscope_api_key=DASHSCOPE_API_KEY
    )

    vector_store = FAISS.load_local(
        VECTOR_STORE_PATH,
        embeddings,
        allow_dangerous_deserialization=True
    )

    return vector_store


def build_chain():

    vector_store = load_vector()

    retriever = vector_store.as_retriever(search_kwargs={"k": 5})

    llm = ChatTongyi(
        model_name=LLM_MODEL,
        dashscope_api_key=DASHSCOPE_API_KEY,
        temperature=0
    )

    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | ICU_PROMPT
        | llm
        | StrOutputParser()
    )

    return chain


def query_rag(question):

    vector_store = load_vector()

    retriever = vector_store.as_retriever(
        search_type="mmr", 
        search_kwargs={"k": 5, "fetch_k": 20} # 先取出20个最相关的，再从中挑选5个差异最大的
    )

    docs = retriever.invoke(question)

    print("\nRetrieved Documents:\n")

    for i, doc in enumerate(docs):

        print("SOURCE:", doc.metadata)
        print(doc.page_content[:300])
        print("-----")

    chain = build_chain()

    result = chain.invoke(question)

    return result


if __name__ == "__main__":

    while True:

        q = input("\nICU Question: ")

        if q == "exit":
            break

        answer = query_rag(q)

        print("\nAnswer:\n", answer)

#python -m pip install pymupdf langchain-core langchain-community langchain-text-splitters faiss-cpu dashscope beautifulsoup4 trafilatura requests pypdf