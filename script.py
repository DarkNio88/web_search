import gradio as gr
import modules.shared as shared
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import NoSuchElementException,TimeoutException
from googlesearch import search
from fake_useragent import UserAgent
from webdriver_manager.firefox  import GeckoDriverManager
import re
import urllib
import html2text

ua = UserAgent()
user_agent = ua.random
print(user_agent)
search_access = True
service = Service(GeckoDriverManager().install())
options = Options()
options.add_argument('headless')
options.add_argument(f'--user-agent={user_agent}')
options.add_argument('--disable-infobars')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--no-sandbox')
options.add_argument('--disable-gpu')
options.add_argument('--ignore-certificate-errors-spki-list')
options.add_argument('--ignore-ssl-errors')
options.add_argument('--log-level=INT')
options.add_argument("disable-blink-features")
options.add_argument("disable-blink-features=AutomationControlled")
options.add_argument("--disable-3d-apis")
options.add_argument("--window-size=1920,1080")
options.add_argument('--remote-debugging-port=9222')

def websearch_results(url):

    driver = webdriver.firefox(service=service,options=options)
    driver.set_page_load_timeout(3)
    html = ""
    output = ""
    h = html2text.HTML2Text()
    
    try:
        driver.get(url)
    except TimeoutException:
        driver.execute_script("window.stop();")
        try:
            h.ignore_links = True
            main_element = driver.find_element(By.CSS_SELECTOR, "[id~='content']")
            html += h.handle(main_element.get_attribute('innerHTML')) if main_element.text else ""
        except NoSuchElementException:
            try:
                content_element = driver.find_element(By.CSS_SELECTOR, "[class~='content']")
                html += h.handle(content_element.get_attribute('innerHTML')) if content_element.text else ""
            except NoSuchElementException:
                try:
                   content_element = driver.find_element(By.TAG_NAME, "main")
                   html += h.handle(content_element.get_attribute('innerHTML')) if content_element.text else ""
                except NoSuchElementException:
                    pass
    except NoSuchElementException as e:
        pass
    
    output = html
    driver.quit()
    return output

def ui():
    global search_access
    checkbox = gr.Checkbox(value=search_access, label="Enable Google Search")
    checkbox.change(fn=update_search_access, inputs=checkbox)
    return checkbox, search_access

def update_search_access(checkbox_value):
    global search_access
    search_access = checkbox_value  # assign the value of the checkbox to the variable
    return search_access, checkbox_value

def input_modifier(user_input, state):
    global search_access
    if search_access:
        search_query = re.search(r'cerca\s+"([^"]+)"', user_input, re.IGNORECASE)

        if search_query:
            query = search_query.group(1)
        elif user_input.lower().startswith("cerca"):
            query = user_input.replace("cerca", "").strip()
        else:
            query = ""

        if not query:
            return user_input
        else:
            shared.processing_message = f"*Ricerca online per {query}*"
            state["context_instruct"] += "La domanda dell'utente è in Domanda dell'utente. I risultati di ricerca pertinenti si trovano nei risultati di ricerca di Google, si tratta di informazioni aggiornate. Sii sincero e segui ciò che viene fornito nei risultati di ricerca di Google. Utilizza i risultati di ricerca di Google nella risposta."
            try:
                search_data = ""
                for result in search(query, num_results=2):
                    search_data += websearch_results(result)     
            except Exception as e:
                # print the type and message of the exception
                print(type(e), e)
                state["context"] += "Informa l'utente che si è verificato un errore"
                pass         
            if search_data=="":
                print("Nessun risultato trovato!")
                state["context"] += "Comunica all'utente che non sono stati trovati risultati"
                user_prompt = f"User question: {user_input}\n la ricerca Google: Nessun risultato trovato!"
            else:
                search_data = search_data[:1024]
                user_prompt = f"User question: {user_input}\n la ricerca Google: {search_data}"
                return user_prompt
    return user_input


def output_modifier(output):
    return output

def bot_prefix_modifier(prefix):
    return prefix
