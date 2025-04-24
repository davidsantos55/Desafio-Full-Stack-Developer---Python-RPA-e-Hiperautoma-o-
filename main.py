from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import ctypes
from time import sleep
import json
import os
from upload_drive_planilha import processar
import base64

class Main:
    def __init__(self):
        self.driver = None

    def start(self):
        opts = Options()
        opts.add_argument("--headless")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--window-size=1920,1080")
        opts.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=opts
        )

        self.wait = WebDriverWait(self.driver, 20)
        u32 = ctypes.windll.user32
        w, h = u32.GetSystemMetrics(0), u32.GetSystemMetrics(1)
        self.driver.set_window_position(0, 0)
        self.driver.set_window_size(w, h)
        self.driver.get("https://portaldatransparencia.gov.br/pessoa-fisica/busca/lista?pagina=1&tamanhoPagina=10")
        sleep(5)

    def finalizar(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

    def carregar_dados(self):
        with open("config.json", encoding="utf8") as arquivo:
            self.pessoas = json.load(arquivo).get("pessoas", [])

    def salvar_resultado(self, resultado, nome_arquivo_json):
        os.makedirs("resultado", exist_ok=True)
        with open(nome_arquivo_json, "w", encoding="utf-8") as arquivo:
            json.dump(resultado, arquivo, indent=4, ensure_ascii=False)

    def capturar_de_imagem(self, caminho):
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        self.driver.save_screenshot(caminho)
        with open(caminho, "rb") as arquivo:
            return base64.b64encode(arquivo.read()).decode()

    def rejeitar_cookies(self):
        try:
            btn = self.wait.until(EC.element_to_be_clickable((By.ID, "accept-minimal-btn")))
            btn.click()
        except:
            pass

    def realizar_busca_por_nome(self, valor):
        self.rejeitar_cookies()
        campo = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#termo")))
        campo.click()
        campo.clear()
        campo.send_keys(valor)
        campo.send_keys(Keys.ENTER)
        self.driver.execute_script("window.scrollBy(0,600)")
        sleep(2)

        try:
            link = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#resultados .link-busca-nome")))
            link.click()
            sleep(2)
            self.coletar_dados_da_pessoa(valor)
            print(f"[SUCESSO] Dados coletados com sucesso para: {valor}")
        except TimeoutException:
            erro = {
                "busca": valor,
                "erro": "Não foi possível retornar os dados no tempo de resposta solicitado."
            }
            self.salvar_resultado(erro, f"resultado/{valor}.json")
            print(f"[ERRO - CPF] Timeout: {valor}")
        except NoSuchElementException:
            erro = {
                "busca": valor,
                "erro": "Foram encontrados 0 resultados para o termo informado."
            }
            self.salvar_resultado(erro, f"resultado/{valor}.json")
            print(f"[ERRO - Nome] Nenhum resultado para: {valor}")
        except Exception as e:
            erro = {
                "busca": valor,
                "erro": f"Erro inesperado: {str(e)}"
            }
            self.salvar_resultado(erro, f"resultado/{valor}.json")
            print(f"[FALHA] Erro inesperado com '{valor}': {str(e)}")

    def extrair_tabela_consulta(self):
        self.rejeitar_cookies()
        dados = []
        try:
            self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#lista, section.dados-detalhados div.br-table table tr")))
            tabela = self.driver.find_element(By.CSS_SELECTOR, "#lista, section.dados-detalhados div.br-table table")
            if tabela.tag_name.lower() == "div":
                tabela = tabela.find_element(By.TAG_NAME, "table")
            linhas = tabela.find_elements(By.TAG_NAME, "tr")
            if not linhas:
                return dados
            headers = [th.text.strip() for th in linhas[0].find_elements(By.TAG_NAME, "th")]
            for tr in linhas[1:]:
                tds = tr.find_elements(By.TAG_NAME, "td")
                if not tds:
                    continue
                registro = {}
                for i, td in enumerate(tds):
                    key = headers[i] if i < len(headers) else f"col_{i}"
                    registro[key] = td.text.strip()
                dados.append(registro)
        except:
            pass
        return dados

    def abrir_detalhes_da_pessoa(self):
        try:
            btn = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.br-button.secondary.mt-3')))
            btn.click()
            sleep(2)
        except:
            pass

    def coletar_dados_da_pessoa(self, valor):
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

        cpf_limpo = mapa.get("CPF", valor).replace(".", "").replace("-", "").replace("*", "").strip()
        nome_arquivo_json = f"resultado/{cpf_limpo}.json"
        if os.path.exists(nome_arquivo_json):
            print(f"[AVISO] Resultado já existente para: {valor}, ignorando duplicata.")
            return

        img_b64 = self.capturar_de_imagem(f"evidencias/{valor}.png")

        titulo_rr, valor_rr = "", ""
        try:
            acc = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#accordion-recebimentos-recursos .box-ficha__resultados')))
            titulo_rr = acc.find_element(By.TAG_NAME, "strong").text.strip()
            valor_rr = acc.find_element(By.CSS_SELECTOR, "#gastosDiretos, table tbody tr td:last-child").text.split(":")[-1].strip()
        except:
            pass

        resultado = {
            "busca": valor,
            "nome": mapa.get("Nome", ""),
            "cpf": mapa.get("CPF", ""),
            "localidade": mapa.get("Localidade", ""),
            "recebimentos": {"titulo": titulo_rr, "valor": valor_rr},
            "screenshot": img_b64
        }

        self.abrir_detalhes_da_pessoa()
        consultas = self.extrair_tabela_consulta()
        resultado["consultas"] = consultas
        self.salvar_resultado(resultado, nome_arquivo_json)
        self.driver.get("https://portaldatransparencia.gov.br/pessoa-fisica/busca/lista?pagina=1&tamanhoPagina=10")
        sleep(3)

    def main(self):
        self.start()
        self.carregar_dados()
        self.arquivos_anteriores = set(os.listdir("resultado")) if os.path.exists("resultado") else set()
        while self.pessoas:
            pessoa = self.pessoas.pop(0)
            print(f"➡ Iniciando busca para: {pessoa}")
            self.realizar_busca_por_nome(pessoa)
            sleep(2)
        
if __name__ == "__main__":
    app = Main()
    try:
        app.main()
    finally:
        app.finalizar()
        novos_arquivos = [f for f in os.listdir("resultado") if f not in app.arquivos_anteriores]
        processar(novos_arquivos)
