# Memórias Perdidas — CP5 PLN e Front-End

RPG narrativo dark fantasy em Python/Pygame, continuação do jogo e mockups da CP4.
A IA produz falas, opções e lembranças; as regras e a progressão continuam sob controle do Python.

**Integrantes:** Thiago Santana Danyluk — RM 562286; Rafael de Paiva Ramos — RM 563978.

## Adaptação para Front-End

O jogo agora usa **requests → FastAPI → provider OpenAI**.
Uma rota de texto, protegida por **X-API-Key**, atende diálogos e lembranças.
O Swagger fica em **/docs**. A chave da OpenAI existe somente no backend.
Implementação baseada no enunciado retificado em 11/10 e nos exemplos de aula do professor Lucas.

- [Requisitos, arquitetura e roteiro do vídeo](ENTREGA_FRONTEND.md)
- [Diários e checklist original de PLN](ENTREGA_CP5.md)
- [AI Context Package](AI_CONTEXT_PACKAGE.md)
- [Validação da adaptação](VALIDACAO_FRONTEND.md)
- [Vídeo original do MVP](https://youtu.be/nB9UEZMc7IU) — anterior ao FastAPI.

## Organização

| Caminho | Responsabilidade |
| --- | --- |
| frontend/main.py | Inicialização do Pygame |
| frontend/game/ | Telas, regras, estado, prompts e cliente HTTP |
| frontend/assets/ e frontend/data/ | Artes da CP4, dados e roteiro offline |
| backend/main.py | FastAPI, Swagger e configuração de CORS |
| backend/routers/ia_generativa.py | Rota de geração de texto |
| backend/providers/openai_provider.py | Único local que importa o SDK OpenAI |
| backend/auth.py e backend/models.py | Autenticação e contratos Pydantic |
| tests/ | Mecânicas, provider, autenticação e integração |
| main.py | Atalho compatível com o comando antigo |

Frontend e backend têm requirements.txt e .env.example próprios e executam em processos separados.
O backend pode ser instalado sem Pygame e o frontend sem OpenAI ou FastAPI.

## Instalação — Windows PowerShell

Python 3.12 ou superior com suporte às dependências. Na raiz do repositório:

~~~powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item backend/.env.example backend/.env
Copy-Item frontend/.env.example frontend/.env
~~~

Crie uma credencial da API do grupo:

~~~powershell
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(32))"
~~~

Cole o mesmo valor em API_KEY nos dois .env. Essa credencial é diferente da chave da OpenAI.

**backend/.env:**

~~~dotenv
API_KEY=SUA_CREDENCIAL_DO_GRUPO
OPENAI_API_KEY=SUA_CHAVE_OPENAI
OPENAI_MODEL=MODELO_DISPONIVEL_NA_SUA_CONTA
CORS_ORIGINS=
~~~

**frontend/.env:**

~~~dotenv
API_URL=http://127.0.0.1:8000
API_KEY=SUA_CREDENCIAL_DO_GRUPO
~~~

O modelo deve suportar Responses API e Structured Outputs. Não publique os .env.
Quem já tinha o .env antigo deve copiar OPENAI_API_KEY e OPENAI_MODEL para backend/.env.
O .env antigo na raiz não é mais usado; o jogo não lê as credenciais da OpenAI.
Variáveis já definidas no sistema têm precedência sobre os .env.

## Executar em dois terminais

**Terminal 1, na raiz:**

~~~powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
~~~

Abra http://127.0.0.1:8000/docs. Use **Authorize** com a API_KEY do grupo e teste a rota.

**Terminal 2, na raiz:**

~~~powershell
.\.venv\Scripts\python.exe frontend/main.py
~~~

O comando antigo **python main.py** continua funcionando no ambiente preparado.
Há também os atalhos **iniciar_backend.ps1** e **iniciar_jogo.ps1**.

Para ambientes separados, instale **backend/requirements.txt** e **frontend/requirements.txt** em seus
respectivos ambientes. Inicie o backend a partir da raiz com **python -m uvicorn backend.main:app**;
inicie o jogo com **python frontend/main.py**.

## Contrato da API

**POST /v1/ia-generativa/texto**, header **X-API-Key** com a credencial do grupo.

~~~json
{
  "instructions": "Interprete Darian em português. Responda em até duas frases.",
  "context": "Kael ajudou o soldado ferido nas ruínas.",
  "response_schema": null,
  "max_output_tokens": 512
}
~~~

Sucesso: **200**, corpo **{"texto": "fala retornada pelo modelo"}**.
Nos turnos, o jogo também envia o JSON Schema do MVP e o provider preserva Structured Outputs.
O modelo é escolhido no backend.

| Código | Significado |
| --- | --- |
| 401 | Credencial do grupo ausente ou incorreta |
| 422 | Corpo inválido ou fora dos limites do contrato |
| 502 | Falha na geração externa |
| 503 | Credencial/configuração ausente no backend |

O provider tem timeout de 25 s e não faz retries automáticos.
O cliente tem timeout de 30 s e não segue redirecionamentos com a credencial.
CORS aceita somente origens explícitas em CORS_ORIGINS, separadas por vírgula.
Pygame/requests não exige CORS; para ele, a lista pode ficar vazia.

## Como jogar

1. **NOVO JOGO:** Kael encontra Darian e as quatro escolhas do mockup.
2. **Darian:** cinco turnos; a IA responde e sugere quatro opções, mantendo a intenção validada.
3. **Exploração:** caminhe com as setas ou clique; investigue com E ou os botões.
4. **Lira:** três turnos; sua abertura e confiança refletem como Kael tratou Darian.
5. **Decisão:** escolha em quem confiar e veja o perfil e o desfecho de Kael.

**TAB:** perfil; **F:** fragmentos; **Esc:** menu; **R:** tentar a IA novamente após falha.
Textos longos usam PgUp/PgDn ou roda do mouse.
O menu contém Continuar, Fragmentos e Configurações.
As regras de atributos e confiança continuam em Python. A IA não executa código nem define valores.
Os quatro fragmentos da CP4 podem ser recuperados; oito espaços continuam bloqueados.
Saves locais ficam em **frontend/save/**, fora do Git.

## Modo offline

Sem API_KEY do grupo no frontend ou com a IA desligada em Configurações, usa-se o roteiro offline.
Se o backend estiver desligado, a chave estiver incorreta ou a OpenAI falhar, aquela geração usa
o fallback existente, identificado na interface. A nova tentativa continua manual, sem reaplicar efeitos.

**Roteiro offline não comprova geração online.** Para demonstrar IA real, configure os dois .env,
ligue a IA e observe o POST 200 no backend junto com a fala/opções retornadas no jogo.

## Testes

~~~powershell
.\.venv\Scripts\python.exe -m compileall -q backend frontend tests main.py
.\.venv\Scripts\python.exe -m pytest -q
~~~

Os testes simulam o provider, bloqueiam rede externa e isolam os saves.
Incluem jogo → cliente HTTP → FastAPI em memória, autenticação, CORS, JSON Schema,
lembranças, indisponibilidade e as mecânicas/telas anteriores.
Não substituem uma chamada real à OpenAI.

## Entrega

Use **ENTREGA_CP5_FRONTEND.txt** e o roteiro em **ENTREGA_FRONTEND.md**.
O vídeo antigo de PLN não demonstra a API nova.
Os campos **[GRUPO]**, a explicação própria e os resultados manuais em ENTREGA_CP5.md
devem ser preenchidos pelos integrantes. As artes e a identidade visual da CP4 foram preservadas.
Não há banco de dados, Docker, deploy, observabilidade ou cadastro de usuários nesta adaptação.
