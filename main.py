from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
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
        opts.add_argument("--headless=new")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--window-size=1920,1080")
        opts.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)
        opts.add_argument("--disable-blink-features=AutomationControlled")

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=opts)
        self.wait = WebDriverWait(self.driver, 60)
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
            elementos = self.driver.find_elements(By.ID, "accept-minimal-btn")
            if elementos:
                btn = elementos[0]
                if btn.is_displayed() and btn.is_enabled():
                    btn.click()
            else:
                print("[INFO] Botão de cookies não está presente na página.")
        except Exception as e:
            print(f"[ERRO] ao tentar rejeitar cookies: {e}")

    def realizar_busca_por_nome(self, valor):
        self.rejeitar_cookies()
        campo = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#termo")))
        campo.click()
        campo.clear()
        campo.send_keys(valor)
        campo.send_keys(Keys.ENTER)
        self.driver.execute_script("window.scrollBy(0,600)")
        sleep(5)
        try:
            link = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#resultados .link-busca-nome")))
            link.click()
            sleep(2)
            self.coletar_dados_da_pessoa(valor)
            print(f"[SUCESSO] Dados coletados com sucesso para: {valor}")
        except TimeoutException:
            erro = {"busca": valor, "erro": "Não foi possível retornar os dados no tempo de resposta solicitado."}
            self.salvar_resultado(erro, f"resultado/{valor}.json")
            print(f"[ERRO - CPF] Timeout: {valor}")
        except NoSuchElementException:
            erro = {"busca": valor, "erro": "Foram encontrados 0 resultados para o termo informado."}
            self.salvar_resultado(erro, f"resultado/{valor}.json")
            print(f"[ERRO - Nome] Nenhum resultado para: {valor}")
        except Exception as e:
            erro = {"busca": valor, "erro": f"Erro inesperado: {str(e)}"}
            self.salvar_resultado(erro, f"resultado/{valor}.json")
            print(f"[FALHA] Erro inesperado com '{valor}': {str(e)}")

    def extrair_tabela_consulta(self):
        sleep(5)
        self.rejeitar_cookies()
        dados = []

        try:
            if self.driver.find_elements(By.CSS_SELECTOR, "div.ativo div.double-scroll table#lista"):
                self.driver.execute_script("document.querySelector('div.ativo div.double-scroll table#lista').scrollIntoView();")
                sleep(1)
                tabela = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.ativo div.double-scroll table#lista")))
            else:
                tabela = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "section.dados-detalhados div.table-responsive.wrapper-table.ativo table")))
        except TimeoutException:
            print("[ERRO] Nenhuma tabela encontrada após tentativas.")
            return dados
        try:
            headers = [th.text.strip() for th in tabela.find_elements(By.CSS_SELECTOR, "thead th")]
            for tr in tabela.find_elements(By.CSS_SELECTOR, "tbody tr"):
                cols = tr.find_elements(By.TAG_NAME, "td")
                registro = {}
                for i, td in enumerate(cols):
                    key = headers[i] if i < len(headers) else f"col_{i}"
                    registro[key] = td.text.strip()
                dados.append(registro)
        except Exception as e:
            print(f"[ERRO] Extração da tabela: {e}")

        return dados

    def abrir_recebimentos_recursos(self):
        try:
            btn_recursos = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.header[aria-controls="accordion-recebimentos-recursos"]')))
            btn_recursos.click()
            sleep(5)
        except Exception as erro:
            print(f"[ERRO] abrir_recebimentos_recursos: não abriu Recebimentos — {erro}")

    def clicar_em_detalhar(self):
        try:
            btn_detalhe = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#btnDetalharBpc, a.br-button.secondary.mt-3')))
            url = btn_detalhe.get_attribute('data-url') or btn_detalhe.get_attribute('href')
            if not url:
                btn_detalhe.click()
            else:
                self.driver.execute_script("window.open(arguments[0], '_blank');", url)
                self.driver.switch_to.window(self.driver.window_handles[-1])
            sleep(5)
        except Exception as erro:
            print(f"[ERRO] clicar_em_detalhar: não conseguiu abrir detalhe — {erro}")

    def coletar_dados_da_pessoa(self, valor):
        self.rejeitar_cookies()
        sec = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "section.dados-tabelados")))
        campos_desejados = ["Nome", "CPF", "Localidade"]
        mapa = {}
        try:
            blocos = sec.find_elements(By.CSS_SELECTOR, "div")
            for campo in campos_desejados:
                encontrado = False
                for div in blocos:
                    textos = div.text.strip().split("\n")
                    if len(textos) >= 2 and textos[0].strip() == campo:
                        mapa[campo] = textos[1].strip()
                        print(f"[OK] {campo}: {mapa[campo]}")
                        encontrado = True
                        break
                if not encontrado:
                    print(f"[ERRO] Campo {campo} não encontrado.")
                    mapa[campo] = ""
        except Exception as e:
            print(f"[ERRO] Falha ao extrair dados do cabeçalho: {e}")
            for campo in campos_desejados:
                mapa[campo] = ""

        cpf_limpo = mapa.get("CPF", valor).replace(".", "").replace("-", "").replace("*", "").strip()
        nome_arquivo_json = f"resultado/{cpf_limpo}.json"

        if os.path.exists(nome_arquivo_json):
            print(f"[AVISO] Resultado já existente para: {valor}, ignorando duplicata.")
            self.driver.get("https://portaldatransparencia.gov.br/pessoa-fisica/busca/lista?pagina=1&tamanhoPagina=10")
            sleep(self.delay)
            return

        img_b64 = self.capturar_de_imagem(f"evidencias/{cpf_limpo}.png")
        sleep(2)
        self.abrir_recebimentos_recursos()
        try:
            self.wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, '#loadingcollapse-3')))
        except:
            print("[AVISO] Timeout esperando loading sumir.")
        sleep(3)
        titulo_recebimentos_recursos = ""
        valor_recebimento_recursos = ""
        try:
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "strong")))
            for el in self.driver.find_elements(By.CSS_SELECTOR, "strong"):
                texto = el.text.strip()
                if texto:
                    titulo_recebimentos_recursos = texto
                    break
        except Exception as erro:
            print(f"[ERRO] Título de recebimento: {erro}")
        try:
            sleep(2)
            if self.driver.find_elements(By.ID, "gastosDiretos"):
                span = self.wait.until(EC.presence_of_element_located((By.ID, "gastosDiretos")))
                texto = span.text.strip()
                if "R$" in texto:
                    valor_recebimento_recursos = texto.split("R$")[-1].strip()
                    valor_recebimento_recursos = "R$ " + valor_recebimento_recursos
        except TimeoutException:pass
        if not valor_recebimento_recursos:
            try:
                tabela = self.driver.find_element(By.ID, "tabela-visao-geral-sancoes")
                tds = tabela.find_elements(By.TAG_NAME, "td")
                for td in tds:
                    if "R$" in td.text:
                        valor_recebimento_recursos = td.text.strip()
                        break
            except Exception as e:pass
        self.clicar_em_detalhar()
        resultado = {
            "busca": valor,
            "nome": mapa.get("Nome", ""),
            "cpf": mapa.get("CPF", ""),
            "localidade": mapa.get("Localidade", ""),
            "recebimentos": {
                "titulo": titulo_recebimentos_recursos,
                "valor": valor_recebimento_recursos
            },
            "screenshot": img_b64
            }
        resultado["consultas"] = self.extrair_tabela_consulta()
        print("[INFO] Salvando resultado em JSON")
        self.salvar_resultado(resultado, nome_arquivo_json)
        print("[INFO] Redirecionando para próxima busca")
        self.driver.get("https://portaldatransparencia.gov.br/pessoa-fisica/busca/lista?pagina=1&tamanhoPagina=10")
        sleep(5)

       
    def main(self):
        self.start()
        self.carregar_dados()
        self.arquivos_anteriores = set(os.listdir("resultado")) if os.path.exists("resultado") else set()
        evidencias = set(os.listdir("evidencias")) if os.path.exists("evidencias") else set()
        resultados = set(os.listdir("resultado")) if os.path.exists("resultado") else set()

        novas_pessoas = []

        for pessoa in self.pessoas:
            base = pessoa.strip().lower().replace(" ", "").replace(".", "").replace("-", "").replace("*", "")
            tem_img = any(f.lower().startswith(base) for f in evidencias)
            tem_json = any(f.lower().startswith(base) for f in resultados)

            if tem_img and tem_json:
                print(f"[PULO] Já existem evidência e resultado para: {pessoa}")
                continue

            novas_pessoas.append(pessoa)

        self.pessoas = novas_pessoas

        for pessoa in self.pessoas:
            print(f"➡ Iniciando busca para: {pessoa}")
            self.realizar_busca_por_nome(pessoa)
            sleep(2)

if __name__ == "__main__":
    app = Main()
    try:
        app.main()
    finally:
        app.finalizar()
        novos = [f for f in os.listdir("resultado") if f not in app.arquivos_anteriores]
        processar(novos)
