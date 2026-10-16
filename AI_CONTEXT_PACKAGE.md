# AI Context Package — Memórias Perdidas

Atualização de 15/10/2026 — CP5 de Front-End com continuidade de PLN.

## Objetivo e limites

Reutilizar o RPG da CP4/CP5 e desacoplar a chamada de IA em FastAPI.
Uma rota de texto, router/provider, X-API-Key, requests, Swagger, README e mini vídeo.
Seguir os exemplos do professor Lucas; sem banco, observabilidade, Docker, deploy ou cadastro.

## Estado técnico

- frontend/: Pygame, assets/dados originais, prompts, regras e saves.
- backend/: FastAPI, contratos Pydantic, autenticação e provider OpenAI.
- POST /v1/ia-generativa/texto serve conversa e lembrança e preserva JSON Schema dos turnos.
- Frontend recebe API_URL e API_KEY do grupo; chave/modelo OpenAI ficam no backend.
- Backend não importa Pygame/game. Frontend não importa OpenAI/backend.
- O fallback offline continua identificado na interface.
- main.py da raiz é atalho; frontend/main.py é a entrada principal.
- Nenhuma arte nova foi gerada.

## Evidências e limites

VALIDACAO_FRONTEND.md registra os testes executados.
Provider simulado não comprova acesso à OpenAI.
O vídeo antigo pertence a PLN e não demonstra a API nova.
Os campos [GRUPO], explicação autoral e resultados manuais dependem dos integrantes.

## Prompt real

O usuário pediu conferir no Teams a atividade de PLN e Front e usar somente o conteúdo de aula.
Após a conferência, autorizou: "então pode fazer".
Decisão: extrair a chamada existente para o backend e substituir a fronteira de comunicação do jogo,
organizando dois projetos no mesmo repositório e preservando as mecânicas.

## Credenciais

Nunca publicar .env ou credenciais em logs, commits ou vídeo.
Exemplos vazios; arquivos reais e saves ignorados.
Uma falha de autenticação não deve alcançar o provider.
