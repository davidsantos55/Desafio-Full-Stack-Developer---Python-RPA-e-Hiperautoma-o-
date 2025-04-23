# Desafio FULLstack Python - RPA no Portal da Transpararência

Automação Python que acessa o [Portal da Transparência](https://portaldatransparencia.gov.br), realiza buscas por pessoas físicas (via nome, CPF ou NIS), coleta dados públicos de benefícios recebidos, captura uma evidência da tela e gera arquivos `.json` com todos os dados formatados — incluindo screenshot em Base64.


## Funcionalidades 

- Acesso automatizado ao Portal da Transparência
- Busca de pessoa física por nome, CPF ou NIS
- Coleta de:
  - Nome completo
  - CPF (mascarado)
  - Localidade
  - Tipo e valor do benefício
  - Tabela detalhada de repasses (valores por mês)
- Captura da tela em formato imagem e codificada em Base64
- Geração de JSON com todas as informações
- Preparado para integração com Google Drive e Google Sheets


## Tecnologias utilizadas

- Python 3
- `undetected-chromedriver`
- Selenium WebDriver
- JSON
- Base64
- (opcional) Google Drive API + Google Sheets API


## Estrutura do projeto

desafio-fullstack-python/ ├── pycache/ # Arquivos gerados automaticamente (ignorar) ├── evidencias/ # Capturas de tela (.png) ├── resultado/ # Resultados em JSON ├── .gitignore # Arquivos ignorados pelo Git ├── config.json # Lista de pessoas para consulta ├── credentials.json # (Ignorado) Credenciais Google ├── main.py # Script principal (automação) ├── nome_arquivo # Arquivo temporário (uso interno) ├── resultado.json # Último resultado gerado ├── README.md # Documentação do projeto └── upload_drive_planilha.py # Upload para Google Drive/Sheets


## Como usar 

### 1. Clone o repositório
    - git clone https://github.com/davidsantos55/desafio-fullstack-python.git
### 2. Instale as dependências 
    - pip install selenium undetected-chromedriver
### 3. Configure o arquivo config.json nesse seguinte formato:
    
    {
    "pessoas": ["João Silva", "12345678900"]
    }   

### 4. Configure a integração com Google Drive/Sheets

    #### 📌 Passo a passo para obter o `credentials.json`:

    1. **Acesse**: [https://console.cloud.google.com](https://console.cloud.google.com)

    2. Crie um projeto (ou selecione um já existente)

    3. No menu lateral, vá em **"APIs e serviços" > "Tela de permissão OAuth"**
    - Selecione **"Interno"** e clique em **Salvar** (pode deixar as outras etapas em branco)

    4. Vá em **"APIs e serviços" > "Credenciais"**
    - Clique em **"Criar credenciais" > "Conta de serviço"**
    - Dê um nome (ex: `bot-rpa`) e clique em **Criar e continuar**
    - Pode pular as permissões → clique em **Concluído**

    5. Ainda em "Credenciais", clique no nome da conta criada → vá em **"Chaves"** → clique em **"Adicionar chave" > "Criar nova chave"**
    - Selecione **JSON** e clique em **Criar**
    - O navegador irá **baixar um arquivo `.json`** com suas credenciais

    6. **Renomeie esse arquivo para `credentials.json`** e **coloque-o na raiz do seu projeto** (mesmo nível do `main.py`)

    7. (Importante) Adicione essa linha ao seu `.gitignore`:

### 5. Execute a Automação
    -python.py
