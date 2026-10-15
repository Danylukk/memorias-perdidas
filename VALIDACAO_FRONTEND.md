# Validação — CP5 Front-End — 15/10/2026

## Resultado

**122 testes aprovados.** Jogo, API e documentação foram preparados na branch **feat/cp5-fastapi**.
O fluxo Pygame → requests → FastAPI foi validado também com servidor HTTP local em execução.

## Ambiente

Windows, Python 3.14.3, pygame-ce 2.5.8, FastAPI 0.143.2, Uvicorn 0.54.0,
OpenAI SDK 2.54.0 e requests 2.34.2, instalados em ambiente virtual novo.
O README recomenda Python 3.12 ou superior, com wheels disponíveis.

## Verificações executadas

| Verificação | Resultado |
| --- | --- |
| Compilação de backend, frontend, testes e main.py | Aprovada |
| Suíte pytest completa | 122 aprovados |
| API sem chave ou com chave incorreta | 401; provider não chamado |
| API sem configuração de credencial | 503; acesso fechado |
| Corpo inválido/limites excedidos | 422; provider não chamado |
| Chamada autenticada em memória | 200; texto retornado |
| Swagger e OpenAPI | Documentados, com X-API-Key e Authorize |
| CORS | Origem permitida aceita; origem não listada rejeitada |
| JSON Schema do turno | Preservado entre cliente, rota e provider |
| Lembranças | Usam a mesma rota, sem schema de turno |
| Falhas do serviço externo | Erros sanitizados, sem detalhes privados |
| Cliente HTTP | Timeout, corpo inválido, 401/502 e redirecionamento tratados |
| Mecânicas/telas originais | Regressões cobertas pela suíte |
| Rodapé com fonte do Windows | Espaçamento corrigido pela altura real do texto renderizado |
| git diff --check | Sem erros de espaços |

Há um aviso de depreciação da biblioteca Starlette sobre o cliente HTTP de testes.
Não houve falha decorrente desse aviso; não altera o consumo por requests em execução.

## Verificação com HTTP real local

Servidor Uvicorn/FastAPI iniciado em porta local temporária, com provider substituído por resposta de teste.
O cliente HTTP original do jogo enviou as requisições pela rede local, sem monkeypatch de requests.

- GET /docs: **200**.
- POST sem chave: **401**, antes de chamar o provider.
- Uma escolha no Pygame gerou uma chamada autenticada e exibiu fala com **4 opções**.
- Confiança de Darian após Ajudar o soldado: **30**.
- Geração de lembrança: segunda chamada à mesma rota, validada.
- Servidor finalizado ao término da verificação.
- Saves temporários isolados.

Essa verificação comprova o transporte HTTP entre jogo e backend, não uma geração real da OpenAI.

## Limites e próximos passos da entrega

Não foi feita chamada real à OpenAI nesta adaptação: não foi fornecida uma credencial/modelo
para esse ambiente novo. Não foram inventados resultados de geração real.

Antes de entregar:
1. Preencher backend/.env com chave/modelo e a mesma API_KEY do grupo nos dois projetos.
2. Validar uma fala e uma lembrança reais conforme ENTREGA_FRONTEND.md.
3. Gravar e anexar o mini vídeo atualizado. O vídeo antigo de PLN é anterior ao FastAPI.
4. Completar a explicação autoral e os campos [GRUPO] da documentação de PLN.

A entrega não foi enviada no Teams. A main não foi alterada por esta implementação.
