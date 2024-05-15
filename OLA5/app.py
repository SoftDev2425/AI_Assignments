from flask import Flask, request, render_template, jsonify
import os
import pandas as pd
import torch
import myloadlib
import myutils
from myloadlib import loadDir, loadFile, loadWiki, loadYoutube, readAPI
from myutils import chunkDocs, wordCloud
from langchain.llms import Ollama
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.embeddings import HuggingFaceEmbeddings
import importlib

app = Flask(__name__)

# Reload custom modules to ensure any changes are reflected
importlib.reload(myloadlib)
importlib.reload(myutils)

# Initialize global variables
documents = []
vectordb = None

# Function to load and process documents
def process_documents(files):
    global documents
    documents = []

    for file in files:
        docs = myloadlib.loadFile(file)
        documents.extend(docs)

    return documents

# Function to create embeddings and vector store
def create_vector_store(documents):
    global vectordb

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

# Route for home page
@app.route('/')
def home():
    return render_template('index.html')

# Route to handle file upload and question input
@app.route('/ask', methods=['POST'])
def ask():
    if 'files' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    files = request.files.getlist('files')
    question = request.form.get('question')


    if not question:
        return jsonify({'error': 'No question provided'}), 400

    # Process uploaded files
    documents = process_documents(files)
    create_vector_store(documents)

    # Initialize the LLM model
    llm = Ollama(model="mistral", callback_manager = CallbackManager([StreamingStdOutCallbackHandler()]))

    # Build prompt template
    template = """Use the following pieces of context to answer the question at the end. 
    If you don't know the answer, just say that you don't know, don't try to make up an answer. 
    Use five sentences maximum. Keep the answer as concise as possible. 
    Always say "thanks for asking!" at the end of the answer. 

    {context}

    Question: {question}

    Helpful Answer:
    """

    prompt = PromptTemplate.from_template(template)

    # Create the RetrievalQA chain
    chain = RetrievalQA.from_chain_type(
        llm,
        retriever=vectordb.as_retriever(),
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt}
    )

    # Ask the question
    result = chain({"query": question})
    answer = result["result"]

    return jsonify({'answer': answer})

if __name__ == '__main__':
    app.run(debug=True)
