from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.common.by import By
import os
import requests
from bs4 import BeautifulSoup
import json
import re
import time
from tqdm import tqdm
from config import MB_SITEMAP, LLAMA_INVOKE_URL, LLAMA_REQUEST_HEADERS, MAIN_DOMAIN, TAB_IDS_MAPPING, CLEAN_DATA_PROMPT, llama_api_call

import warnings
warnings.filterwarnings("ignore")

CHROME_OPTIONS = Options()
CHROME_OPTIONS.add_argument("--headless=new")
CHROME_OPTIONS.add_argument("start-maximized")
CHROME_OPTIONS.add_argument("--disable-gpu")
CHROME_OPTIONS.add_argument("--no-sandbox")
CHROME_OPTIONS.add_argument("--disable-infobars")
CHROME_OPTIONS.add_argument("--disable-dev-shm-usage")
CHROME_OPTIONS.add_argument("--remote-debugging-port=9222")
CHROME_OPTIONS.add_argument("--enable-javascript")
CHROME_OPTIONS.add_argument('--disable-blink-features=AutomationControlled')

DRIVER = webdriver.Chrome(options=CHROME_OPTIONS)
# DRIVER.set_window_size(1920, 1080)
DRIVER.set_page_load_timeout(20)


class MBdata:
    def __init__(self, bank_sitemap):
        self.bank_sitemap = bank_sitemap
        # self.all_dirs = self.get_sitemap_loan_urls(bank_sitemap)
        self.all_dirs = ["https://bankofmaharashtra.in/retail-loans"]
        self.all_locs = []
        self.page_data_mapping = []
        self.cleaned_documents = []

    def get_sitemap_loan_urls(self):
        sitemap_soup = BeautifulSoup(requests.get(self.bank_sitemap).content, "lxml")
        loc_paths = sitemap_soup.find_all("loc")
        self.all_dirs = [
            loc.text for loc in loc_paths if
            "loan" in loc.text and not any(x in loc["href"] for x in ["/hi/", "/mar/", "blogs"])
        ]
        print(f"[+] total loan dir urls fetched -- {len(self.all_dirs)}")

    def get_loan_urls(self):
        for dir_url in self.all_dirs:
            DRIVER.get(dir_url)
            time.sleep(2)
            retail_soup = BeautifulSoup(DRIVER.page_source, "lxml")
            all_a = retail_soup.body.find_all("a")
            self.all_locs += [
                f"{MAIN_DOMAIN}{loc['href']}" for loc in all_a if (
                        "loan" in loc["href"] and not loc["href"].strip("/").startswith("http")
                        and not any(x in loc["href"] for x in ["/hi/", "/mar/", "blogs", "www"])
                )
            ]
        print(f"[+] total loan data urls fetched -- {len(self.all_locs)}")

    @staticmethod
    def parse_for_data():
        all_text = {}
        for name, tab_id in TAB_IDS_MAPPING.items():
            try:
                elem_ = DRIVER.find_element(By.ID, tab_id)
                DRIVER.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", elem_)
                time.sleep(1)
                elem_.click()
                time.sleep(1)
                content_id = tab_id.replace("tab", "pane")
                pane = DRIVER.find_element(By.ID, content_id)
                all_text[name] = pane.text.strip()
            except Exception:
                pass

        if not all_text:
            json_data = []
            soup_ = BeautifulSoup(DRIVER.page_source, "lxml")
            # main_div = soup_.find("div", class_="inner_post_content")
            all_tables = soup_.find_all("table")
            for table in all_tables:
                headers = [th.text.strip() for th in table.find_all("th")]
                for tr in table.find_all("tr")[1:]:  # skip header row
                    cells = tr.find_all("td")
                    if len(cells) == len(headers):  # valid row
                        row_data = {headers[i]: cells[i].text.strip() for i in range(len(headers))}
                        json_data.append(row_data)
            if json_data:
                all_text["Table Data"] = json_data
        return all_text

    def get_page_data(self):
        for page_url in tqdm(self.all_locs):
            print(f"[+] fecthing data from: {page_url}")
            try:
                DRIVER.get(page_url)
                time.sleep(2)
            except Exception as e:
                print(f"[-] Error accessing {url}: {e}")
                continue
            all_text = self.parse_for_data()
            print(f"[+] Parsing {'successful' if all_text else 'failed'}")
            if all_text:
                all_text["page_url"] = page_url
                self.page_data_mapping.append(all_text)
                print(f"[+] cleaning in progess..")
                clean_data = self.get_cleaned_data(all_text)
                self.cleaned_documents.append({"page_url": page_url, "data": clean_data})
        self.save_json_data("mah_bank_raw_loan_data.json", self.page_data_mapping)
        self.save_json_data("mah_bank_cleaned_loan_data.json", self.cleaned_documents)

    @staticmethod
    def save_json_data(file_name, json_data):
        try:
            with open(file_name, "w") as f:
                json.dump(json_data, f)
            print(f"[+] json data saved successfully - {file_name}")
        except Exception as e:
            print(f"[-] failed to save json data -- {file_name} -- {e}")

    @staticmethod
    def get_cleaned_data(input_text):
        prompt = CLEAN_DATA_PROMPT.replace("{input_text}", json.dumps(input_text))
        results = llama_api_call(prompt, response_format={"type": "json_object"})
        match_ = re.search(r'\{[\s\S]*\}', results)
        if match_:
            results = match_.group().replace("\n", "")
        return results


if __name__ == "__main__":
    parser = MBdata(MB_SITEMAP)
    # parser.get_sitemap_loan_urls()
    parser.get_loan_urls()
    parser.get_page_data()
    DRIVER.quit()
