import requests
import os
from dotenv import load_dotenv

load_dotenv()

LLAMA_INVOKE_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
LLAMA_ACCESS_TOKEN = os.getenv("LLAMA_ACCESS_TOKEN")
LLAMA_REQUEST_HEADERS = {
    "Authorization": f"Bearer {LLAMA_ACCESS_TOKEN}",
    "Accept": "application/json"
}
GEN_PROMPT = """
Write a shortest possible output for the given QUESTION with respect to he below mentioned relevant DETAILS.
QUESTION = {question}
DETAILS = {details}

output should be in the following JSON format:
{"answer": ""}
"""
CLEAN_DATA_PROMPT = """
Write a text format with good grammer showing all the json data in paragraphs.
inputs_data = {input_text}

output should be in the following format:
{"cleaned_data": ""}
"""
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/104.0.5112.101 Safari/537.36"
}
TAB_IDS_MAPPING = {
    "Features & Benefits": "tab-fb",
    "Documents Required": "tab-dr",
    "Interest Rates": "tab-ir",
    "EMI Calculator": "tab-emi",
    "Eligibility": "tab-elig",
    # "FAQs": "tab-faq"
}
MAIN_DOMAIN = "https://bankofmaharashtra.in"
MB_SITEMAP = "https://bankofmaharashtra.in/sitemap.xml"


def llama_api_call(prompt, temperature=1, max_tokens=1000, top_p=1, model="meta/llama-3.3-70b-instruct",\
                   response_format=None, timeout=30):
    results = ""
    messages = [{"role": "user", "content": prompt}]
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "frequency_penalty": 0.00,
        "presence_penalty": 0.00,
        "stream": False,
    }
    if response_format is not None:
        payload["response_format"] = response_format
    try:
        response = requests.post(LLAMA_INVOKE_URL, headers=LLAMA_REQUEST_HEADERS, json=payload, timeout=timeout)
        if response.status_code == 200:
            comp = response.json()
            results = comp.get("choices", [{}])[0].get("message", {}).get("content", "")
            if not results:
                results = comp
        else:
            results = response.text
    except Exception as e:
        print(f"Error occurred in llama_api_call: {e}")
    return results
