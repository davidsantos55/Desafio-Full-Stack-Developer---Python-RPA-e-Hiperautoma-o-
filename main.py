import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
from datetime import datetime
import ctypes
from time import sleep
import json
import os
from upload_drive_planilha import processar
import base64

class Main:
    def start(self):
        uc.TARGET_VERSION = "134"
        opts = uc.ChromeOptions()
        opts.add_argument("--headless")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_argument("--window-size=1920,1080")
        opts.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
        self.driver = uc.Chrome(version_main=134, options=opts)
        self.wait = WebDriverWait(self.driver, 20)
        u32 = ctypes.windll.user32
        w, h = u32.GetSystemMetrics(0), u32.GetSystemMetrics(1)
        self.driver.set_window_position(0, 0)
        self.driver.set_window_size(w, h)
        self.driver.get("https://portaldatransparencia.gov.br/pessoa-fisica/busca/lista?pagina=1&tamanhoPagina=10")
        sleep(5)

    def carregar_dados(self):
        with open("config.json", encoding="utf8") as f:
            self.pessoas = json.load(f).get("pessoas", [])

    def salvar_resultado(self, dado):
        os.makedirs("resultado", exist_ok=True)
        cpf_limpo = dado.get("cpf", "").replace(".", "").replace("-", "").replace("*", "").strip()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_arquivo = f"resultado/{cpf_limpo}_{timestamp}.json"
        with open(nome_arquivo, "w", encoding="utf-8") as f:
            json.dump(dado, f, indent=4, ensure_ascii=False)


    def capturar_de_imagem(self, caminho):
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        self.driver.save_screenshot(caminho)
        with open(caminho, "rb") as f:
            return base64.b64encode(f.read()).decode()  

    def rejeitar_cookies(self):
        try:
            btn = self.wait.until(EC.element_to_be_clickable((By.ID, "accept-minimal-btn")))
            btn.click()
        except:
            pass

    def buscar_pessoa(self, valor):
        self.rejeitar_cookies()
        c = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#termo")))
        c.click(); c.clear(); c.send_keys(valor); c.send_keys(Keys.ENTER)
        self.driver.execute_script("window.scrollBy(0,600)"); sleep(2)
        try:
            l = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#resultados .link-busca-nome")))
            l.click(); sleep(2)
        except:
            return
        self.dados_pessoa(valor)

    def extrair_tabela_consulta(self):
        self.rejeitar_cookies()
        dados = []

        try:
            self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#lista, section.dados-detalhados div.br-table table" + " tr")))
            tabela = self.driver.find_element(By.CSS_SELECTOR, "#lista, section.dados-detalhados div.br-table table")
            if tabela.tag_name.lower() == "div":
                tabela = tabela.find_element(By.TAG_NAME, "table")
            linhas = tabela.find_elements(By.TAG_NAME, "tr")
            if not linhas:
                return dados
            headers = [th.text.strip()
                    for th in linhas[0].find_elements(By.TAG_NAME, "th")]
            for tr in linhas[1:]:
                tds = tr.find_elements(By.TAG_NAME, "td")
                if not tds:
                    continue
                registro = {}
                for i, td in enumerate(tds):
                    key = headers[i] if i < len(headers) else f"col_{i}"
                    registro[key] = td.text.strip()
                dados.append(registro)

        except TimeoutException:pass
        except NoSuchElementException as e:pass  
        except Exception as e:pass
        return dados
        

    def buscar_detalhe(self):
        try:
            btn = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.br-button.secondary.mt-3')))
            btn.click(); sleep(2)
        except:pass


    def dados_pessoa(self, valor):
        self.rejeitar_cookies()
        sec = self.driver.find_element(By.CSS_SELECTOR, "section.dados-tabelados")
        mapa = {}
        for s in sec.find_elements(By.TAG_NAME, "strong"):
            rot = s.text.strip()
            try:
                txt = s.find_element(By.XPATH, "following-sibling::span").text.strip()
            except:
                txt = ""
            mapa[rot] = txt
        btn_rr = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-controls="accordion-recebimentos-recursos"]')))
        btn_rr.click(); sleep(1)
        nome_arquivo = f"evidencias/{valor}.png"
        img_b64 = self.capturar_de_imagem(nome_arquivo)
        titulo_rr, valor_rr = "", ""
        try:
            acc = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#accordion-recebimentos-recursos .box-ficha__resultados')))
            titulo_rr = acc.find_element(By.TAG_NAME, "strong").text.strip()
            valor_rr = acc.find_element(By.CSS_SELECTOR, "#gastosDiretos, table tbody tr td:last-child").text.split(":")[-1].strip()
        except:pass
           
        r = {
            "busca": valor,
            "nome": mapa.get("Nome",""),
            "cpf": mapa.get("CPF",""),
            "localidade": mapa.get("Localidade",""),
            "recebimentos": {"titulo": titulo_rr, "valor": valor_rr},
            "screenshot": img_b64
        }

        self.buscar_detalhe()
        consultas = self.extrair_tabela_consulta()
        r["consultas"] = consultas
        self.salvar_resultado(r)
        self.driver.get("https://portaldatransparencia.gov.br/pessoa-fisica/busca/lista?pagina=1&tamanhoPagina=10")
        sleep(3)

    def main(self):
        self.start()
        self.carregar_dados()
        while self.pessoas:
            p = self.pessoas.pop(0)
            print(f"➡ Buscando: {p}")
            self.buscar_pessoa(p)
            sleep(2)

if __name__ == "__main__":
    Main().main()
    processar()
