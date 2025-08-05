from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
import json
import os

HUGGINGFACE_EMBEDDING_MODEL = HuggingFaceEmbeddings()
JSON_FILE_PATH = "data/mah_bank_cleaned_loan_data.json"

if not os.path.exists(JSON_FILE_PATH):
    raise FileNotFoundError("Cleaned loan data file not found.")

cleaned_documents = json.load(open(JSON_FILE_PATH))

# comment if you are using other json data
cleaned_documents = [f"{doc['page_url']}: {doc['data']}" for doc in cleaned_documents]

splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
docs = splitter.create_documents(cleaned_documents)

FAISS_DB = FAISS.from_documents(docs, HUGGINGFACE_EMBEDDING_MODEL)
FAISS_DB.save_local("data/faiss_index")
print(f"[+] FAISS index file saved successfully")
