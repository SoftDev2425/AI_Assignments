import sys
import os
import importlib
import myloadlib
import myutils
from langchain.llms import Ollama
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.embeddings import HuggingFaceEmbeddings

# Ensure your custom modules are reloaded
importlib.reload(myloadlib)
importlib.reload(myutils)

def process_documents(file_paths):
    documents = []
    for file_path in file_paths:
        docs = myloadlib.loadFile(file_path)
        documents.extend(docs)
    return documents

def create_vector_store(documents):
    splits = myutils.chunkDocs(documents, 350)
    model_name = "sentence-transformers/all-mpnet-base-v2"
    model_kwargs = {'device': 'cpu'}
    encode_kwargs = {'normalize_embeddings': False}

    embeddings = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs
    )

    persist_directory = './data/chroma/'

    vectordb = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory=persist_directory
    )
    vectordb.persist()
    return vectordb

def ask_question(vectordb, question):
    llm = Ollama(model="mistral", callback_manager=CallbackManager([StreamingStdOutCallbackHandler()]))

    template = """Use the following pieces of context to answer the question at the end. 
    If you don't know the answer, just say that you don't know, don't try to make up an answer. 
    Use five sentences maximum. Keep the answer as concise as possible. 
    Always say "thanks for asking!" at the end of the answer. 

    {context}

    Question: {question}

    Helpful Answer:
    """

    prompt = PromptTemplate.from_template(template)
    chain = RetrievalQA.from_chain_type(
        llm,
        retriever=vectordb.as_retriever(),
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt}
    )

    result = chain({"query": question})
    return result["result"]

if __name__ == "__main__":
    file_paths = sys.argv[1:-1]
    question = sys.argv[-1]

    documents = process_documents(file_paths)
    vectordb = create_vector_store(documents)
    answer = ask_question(vectordb, question)

    print(answer)