# Culto de Jovens — Ensaio Local

App em Streamlit para contagem de músicos, organistas e recitativos, com prévia
automática de presença por categoria (Cordas, Madeiras, Metais) e total geral.
Os ensaios ficam salvos no Turso, então dá pra consultar ensaios anteriores.

## 1. Criar o banco no Turso

Se ainda não tiver a CLI do Turso instalada:

```bash
curl -sSfL https://get.tur.so/install.sh | bash
turso auth login
turso db create ensaio-culto-jovens
turso db show ensaio-culto-jovens --url
turso db tokens create ensaio-culto-jovens
```

Guarde a URL (começa com `libsql://...`) e o token gerado — são eles que vão
para o `secrets.toml`. A tabela `ensaios` é criada automaticamente na primeira
vez que o app rodar.

## 2. Configurar as credenciais

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Edite `.streamlit/secrets.toml` e preencha:
- `APP_PASSWORD`: a senha única que as 6 pessoas vão usar para entrar
- `TURSO_DATABASE_URL`: a URL do banco
- `TURSO_AUTH_TOKEN`: o token gerado

Esse arquivo já está no `.gitignore` — não vai para o GitHub.

## 3. Rodar localmente

```bash
python -m venv .venv
source .venv/bin/activate  # no Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## 4. Publicar

Suba a pasta para um repositório novo no GitHub (o `secrets.toml` real fica de
fora automaticamente) e conecte no [Streamlit Community Cloud](https://streamlit.io/cloud).
Lá, em **Settings → Secrets**, cole o mesmo conteúdo do seu `secrets.toml`
local — é assim que o app hospedado vai pegar a senha e a conexão com o Turso.

## Como funciona o acesso

Login com senha única: todas as 6 pessoas usam a mesma senha, definida em
`APP_PASSWORD`. Não há usuários individuais nem histórico de quem preencheu
cada ensaio — os registros salvos mostram só o título e os números.
