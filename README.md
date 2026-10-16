# Memórias Perdidas — CP5 de Front-End

**Disciplina:** Front-End e Mobile Development — FIAP  
**Professor:** Lucas Tadeu Cunha Rios  
**Projeto:** Memórias Perdidas — RPG narrativo com IA generativa

**Integrantes**
- **Thiago Santana Danyluk** — RM 562286
- **Rafael de Paiva Ramos** — RM 563978

## Vídeo da entrega

**[Assistir à demonstração da CP5 de Front-End](https://youtu.be/0yclAM2c9z8)**

O vídeo apresenta a API no Swagger, o consumo da rota durante o jogo e a arquitetura da integração.

## Objetivo e arquitetura

O jogo, implementado com **Python/Pygame**, não chama o serviço externo de inteligência artificial diretamente. Ele usa um cliente HTTP (`requests`) para consultar a **API própria do grupo**, desenvolvida em **FastAPI**.

```text
Jogo Pygame
   │ HTTP POST + X-API-Key
   ▼
FastAPI → router /v1/ia-generativa/texto
   ▼
Provider OpenAI → serviço de IA generativa
   │
   └── resposta narrativa → FastAPI → jogo
```

A modalidade utilizada é **texto** (diálogos e lembranças). O backend concentra a chamada à OpenAI, a validação do corpo recebido, a autenticação e as configurações de CORS. As regras e os atributos do RPG permanecem no jogo.

| Requisito | Implementação |
| --- | --- |
| API do grupo em FastAPI | `backend/main.py` |
| Rota organizada em router | `backend/routers/ia_generativa.py` |
| Chamada à IA isolada em provider | `backend/providers/openai_provider.py` |
| Autenticação `X-API-Key` | `backend/auth.py` |
| CORS configurável | `backend/main.py` |
| Consumo via HTTP pelo jogo | `frontend/game/systems/api_client.py` |
| Swagger/OpenAPI | `http://127.0.0.1:8000/docs` |

## Estrutura do repositório

- `backend/`: API FastAPI, autenticação, schemas e provider de IA.
- `frontend/`: jogo Pygame, cliente HTTP, imagens e dados.
- `tests/`: testes de integração, autenticação e mecânicas.
- `requirements.txt`: dependências para execução e testes.
- `docs/pln/`: histórico da entrega de PLN, mantido separado desta CP.

## Instalação e configuração

Requer **Python 3.12 ou superior** compatível com as dependências e uma chave válida da API OpenAI.

Na raiz do repositório, execute no **PowerShell**:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item backend\.env.example backend\.env
Copy-Item frontend\.env.example frontend\.env
```

Configure os arquivos locais **sem publicá-los no GitHub**:

`backend/.env`
```dotenv
API_KEY=CHAVE_INTERNA_DO_GRUPO
OPENAI_API_KEY=SUA_CHAVE_OPENAI
OPENAI_MODEL=MODELO_COMPATIVEL
CORS_ORIGINS=
```

`frontend/.env`
```dotenv
API_URL=http://127.0.0.1:8000
API_KEY=CHAVE_INTERNA_DO_GRUPO
```

A `API_KEY` interna deve ter o **mesmo valor** nos dois arquivos e ser diferente da `OPENAI_API_KEY`. Para gerar uma credencial interna segura:

```powershell
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(32))"
```

A chave da OpenAI permanece **somente no backend**. O modelo configurado deve aceitar Responses API e saída estruturada. Os arquivos `.env` estão no `.gitignore`.

## Como executar

Abra **dois terminais**, ambos na raiz do repositório:

**Terminal 1 — API**

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Acesse **http://127.0.0.1:8000/docs** para visualizar a rota `POST /v1/ia-generativa/texto` no Swagger. A rota exige autenticação `X-API-Key`.

**Terminal 2 — jogo**

```powershell
.\.venv\Scripts\python.exe frontend/main.py
```

No menu do jogo, ative a IA em **Configurações**, inicie **NOVO JOGO** e interaja com o soldado Darian. A comunicação com a API pode ser observada no Terminal 1 pelo registro `POST /v1/ia-generativa/texto ... 200 OK`.

O jogo também possui um **roteiro offline de contingência**. A execução offline não comprova a integração com a IA: para essa evidência, é preciso receber uma resposta online pela rota.

## Testes

```powershell
.\.venv\Scripts\python.exe -m compileall -q backend frontend tests main.py
.\.venv\Scripts\python.exe -m pytest -q
```

Os testes automatizados usam respostas simuladas quando necessário e não substituem a demonstração da chamada real. **[Vídeo da integração funcionando](https://youtu.be/0yclAM2c9z8)**.

---

**Entrega de Front-End:** código completo do jogo e do backend neste repositório, instruções no README, integrantes identificados e demonstração em vídeo.
