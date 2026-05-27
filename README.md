# SQL Explorer Readonly MCP

MCP server para exploracao de banco SQL em modo somente leitura, com foco em consultas analiticas seguras (`SELECT`/`WITH`), listagem de tabelas e descricao de schema.

## 1) Requisitos

- Linux/WSL (Ubuntu/Debian recomendado)
- Python 3.10+
- Driver ODBC 18 da Microsoft para SQL Server
- (Opcional) Docker + Docker Compose

## 2) Instalar ODBC Driver 18 (Linux/WSL)

Referencia oficial Microsoft:
- https://learn.microsoft.com/pt-br/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server?view=sql-server-ver17

Exemplo para Ubuntu/Debian (WSL tambem):

```bash
sudo apt-get update
sudo apt-get install -y curl gnupg ca-certificates unixodbc unixodbc-dev

curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | sudo gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" | sudo tee /etc/apt/sources.list.d/microsoft-prod.list

sudo apt-get update
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18
```

Validacao rapida:

```bash
odbcinst -j
```

## 3) Setup do projeto (modo local)

```bash
cd /home/filipe/projetos/sql-explorer-tool
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 4) Configurar conexao

1. Copie o exemplo:

```bash
cp config.example.yaml config.yaml
```

2. Edite `config.yaml` com sua conexao SQL Server.

Observacao importante:
- Se a senha tiver caracteres especiais (`%`, `@`, `:`, `/`, `#`), use URL encoding.
- Exemplo: `%` vira `%25`.

## 5) Rodar MCP localmente

```bash
source venv/bin/activate
python3 server.py
```

Ao iniciar, voce deve ver log de startup do servico.

## 6) Testar rapido no terminal

```bash
source venv/bin/activate
python3 -c "from db import list_tables; print(len(list_tables('banco-dev')))"
```

Se retornar um numero (`> 0`), a conexao e a listagem de tabelas estao funcionando.

## 7) Integrar no Codex (local Python)

Configurar servidor MCP no Codex com:

- Comando:
`/home/filipe/projetos/sql-explorer-tool/venv/bin/python`
- Argumento:
`/home/filipe/projetos/sql-explorer-tool/server.py`
- Diretorio de trabalho:
`/home/filipe/projetos/sql-explorer-tool`

Tools disponiveis:
- `health()`
- `tables(connection)`
- `describe(connection, table, schema?)`
- `query(connection, sql, limit=100)`

## 8) Rodar com Docker

Arquivos incluidos:
- `Dockerfile`
- `docker-compose.yml`
- `run-mcp-docker.sh`

Build da imagem:

```bash
docker build -t sql-explorer-readonly:latest .
```

Rodar MCP em modo stdio (recomendado para Codex):

```bash
./run-mcp-docker.sh
```

Opcional com Compose:

```bash
docker compose up --build
```

Para usar no Codex via Docker:
- Comando: `/home/filipe/projetos/sql-explorer-tool/run-mcp-docker.sh`
- Sem argumentos
- Diretorio de trabalho: `/home/filipe/projetos/sql-explorer-tool`

## 9) Logs e observabilidade

O servidor usa logger customizado em JSON (arquivo `logging_utils.py`) com:
- inicio/fim de chamadas MCP
- duracao (`duration_ms`)
- warnings (ex.: clamp de `limit`)
- erros e stacktrace
- contexto (`os_user`, `host`, `pid`, `client_name`, `client_version`)

Nivel de log:

```bash
LOG_LEVEL=DEBUG python3 server.py
```

Ou em Docker:

```bash
LOG_LEVEL=DEBUG ./run-mcp-docker.sh
```

## 10) Troubleshooting

- `ModuleNotFoundError`: faltou instalar dependencias no `venv`.
- `libodbc.so.2`: faltam pacotes `unixodbc`/driver ODBC.
- `08001 / SQLDriverConnect`: problema de rede/DNS/VPN para host SQL (ex.: `rigel:1433`).
- Tool nao aparece no Codex: reinicie o servidor MCP e recarregue a sessao do Codex.

## 11) Referencias MCP

- MCP Python SDK (oficial): https://github.com/modelcontextprotocol/python-sdk
- README da SDK: https://github.com/modelcontextprotocol/python-sdk/blob/main/README.md
- Documentacao geral MCP: https://modelcontextprotocol.io
