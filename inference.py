import re
import json
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from config import GEN_PROMPT, llama_api_call

embedding_model = HuggingFaceEmbeddings()
FAISS_DB = FAISS.load_local("data/faiss_index", embedding_model, allow_dangerous_deserialization=True)


def chat_agent():
    while True:
        question = input('question : ')
        if question == 'exit':
            print('Thank you!! \n Terminating Chat Agent')
            break

        res = FAISS_DB.similarity_search(question)
        if not res:
            print("answer: No relevant documents found.")
            continue
        prompt = GEN_PROMPT.replace("{question}", question).replace(
            "{details}", ". ".join([res[x].page_content for x in range(2)]))
        results = llama_api_call(prompt, response_format={"type": "json_object"}, timeout=120)
        try:
            match_ = re.search(r'\{[\s\S]*\}', results)
            json_str = match_.group().replace("\n", "").replace("\t", "")
            data = json.loads(json_str)
            answer = data.get("answer", data)
        except Exception as e:
            print(f"failed to load -- {e}")
            answer = results
        print(f"answer: {answer}")


if __name__ == "__main__":
    chat_agent()
