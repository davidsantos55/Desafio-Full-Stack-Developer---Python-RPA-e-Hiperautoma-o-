import os
import json
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

CREDENTIALS_PATH = "credentials.json"
PASTA_RESULTADOS = "resultado"
NOME_PLANILHA = "Automacao-Robo"
NOME_ABA = "Dados"
ID_PASTA_DRIVE = "1qlDwYcDv6MD2XwGJypOFHDcRMPDnptYs"


def autenticar():
    escopos = ["https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_PATH, escopos)
    gauth = GoogleAuth()
    gauth.credentials = creds
    return GoogleDrive(gauth)


def autenticar_sheets():
    escopos = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_PATH, escopos)
    cliente = gspread.authorize(creds)
    return cliente.open(NOME_PLANILHA).worksheet(NOME_ABA)

def resumir_dados(dados):
    return {
        "identificador": dados.get("cpf", "").replace(".", "").replace("-", "").replace("*", ""),
        "nome": dados.get("nome", ""),
        "cpf": dados.get("cpf", ""),
        "datahora": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    }

def enviar_arquivo(drive, caminho):
    nome = os.path.basename(caminho)
    arquivo = drive.CreateFile({"title": nome, "parents": [{"id": ID_PASTA_DRIVE}]})
    arquivo.SetContentFile(caminho)
    arquivo.Upload()
    arquivo.InsertPermission({
        'type': 'anyone',
        'value': 'anyone',
        'role': 'reader'
    })
    return f"https://drive.google.com/file/d/{arquivo['id']}/view?usp=sharing"

def processar(lista_arquivos):
    drive = autenticar()
    aba = autenticar_sheets()
    for nome_arquivo in lista_arquivos:
        if not nome_arquivo.endswith(".json"):
            continue
        caminho = os.path.join(PASTA_RESULTADOS, nome_arquivo)
        with open(caminho, "r", encoding="utf-8") as f:
            dados = json.load(f)
        resumo = resumir_dados(dados)
        link = enviar_arquivo(drive, caminho)
        aba.append_row([resumo["identificador"], resumo["nome"], resumo["cpf"], resumo["datahora"], link])
        print(f"✅ {nome_arquivo} enviado e registrado.")

