# CP5 — MVP do Jogo — Front-End

**Professor:** Lucas Tadeu Cunha Rios
**Integrantes:** Thiago Santana Danyluk — RM 562286; Rafael de Paiva Ramos — RM 563978.

## Resultado

O Pygame deixa de chamar a OpenAI diretamente e usa a API FastAPI do grupo.
O backend autentica, valida o corpo e chama o provider. A mesma rota atende falas/opções e lembranças.

| Requisito | Evidência |
| --- | --- |
| Dois projetos separados | frontend/ e backend/, com dependências e .env.example próprios |
| Rota real de texto | POST /v1/ia-generativa/texto |
| Rota → provider | backend/routers/ia_generativa.py → backend/providers/openai_provider.py |
| Autenticação pelo header | X-API-Key em backend/auth.py |
| Consumo no jogo | frontend/game/systems/api_client.py, injetado por frontend/game/app.py |
| OpenAI somente no backend | SDK apenas em backend/providers/openai_provider.py |
| Swagger | /docs e /openapi.json, com botão Authorize |
| CORS | Origens explícitas configuráveis; Pygame não exige origem web |
| README e integrantes | README.md, com comandos dos dois processos |
| Vídeo simples | Roteiro abaixo; vídeo antigo é anterior ao FastAPI |

A rota é usada pela narrativa em execução, não apenas uma rota de status para demonstrar o framework.

## Referências das aulas

- **14/08:** introdução ao FastAPI, Pydantic, routers/providers, Swagger e processos separados.
  https://github.com/LucasRios/FIAP/blob/main/Aula12/FastAPI%20-%20Do%20Python%20Simples%20ao%20Backend%20de%20IA.md
- **21 e 28/08:** requests, autenticação pelo header e tratamento de erros.
  https://github.com/LucasRios/FIAP/blob/main/Aula13/Consumindo%20a%20API%20no%20Front%20com%20Streamlit.md
- **04/09:** refatoração do projeto e CORS.
  https://github.com/LucasRios/FIAP/blob/main/Aula15/Workshop%20-%20Refatorando%20o%20Sprint%20com%20FastAPI.md

Escopo baseado no enunciado e no aviso retificado de 11/10.
Sem observabilidade, banco ou publicação em nuvem. Mecânicas e visual continuam no escopo de PLN.

## Validação manual com IA real

1. Configure os dois .env pelo README e inicie o backend.
2. Em /docs, envie a requisição sem credencial: deve retornar 401.
3. Use Authorize com a API_KEY do grupo e envie o exemplo: deve retornar 200 e texto real.
4. Inicie o jogo e mantenha os diálogos com IA ligados em Configurações.
5. Selecione Ajudar o soldado e observe a fala/opções e o POST 200 no terminal do backend.
6. Gere uma lembrança durante a exploração e confirme a chamada à mesma rota.
7. Desligue o backend e faça outra escolha: o roteiro de reserva deve ser usado.
8. Não mostre .env ou credenciais na gravação.

## Roteiro do mini vídeo — 1 a 2 minutos

- **0–15 s:** nome do jogo e integrantes; mostre frontend/ e backend/.
- **15–35 s:** mostre a rota no Swagger e o Authorize sem revelar a chave.
- **35–70 s:** escolha no jogo, fala gerada e POST 200 no backend.
- **70–90 s:** explique requests → router → provider; chave OpenAI só no backend.
- **90–110 s:** mostre os comandos no README e explique o fallback.

O roteiro é apoio para a gravação, não um registro de execução.
O vídeo https://youtu.be/nB9UEZMc7IU pertence ao MVP anterior, sem FastAPI.

## Autoria do grupo

Completar a explicação própria em ENTREGA_CP5.md.
Gravar e incluir o link do vídeo atualizado e validar com chave/modelo próprios.
Não declarar respostas simuladas como geração real.
