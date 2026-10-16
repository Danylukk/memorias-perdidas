# CP5 Front-End — Roteiro para gravar sem improviso

**Entrega:** CP5 - MVP do Jogo - Matéria de FRONTEND (16/10/2026).
**Professor:** Lucas Tadeu Cunha Rios.
**Jogo:** Memórias Perdidas — Thiago Santana Danyluk (RM 562286) e Rafael de Paiva Ramos (RM 563978).

## Antes de apertar REC

1. Na pasta do repositório, atualize o código da branch `main` depois do merge do PR #2 (ou use `feat/cp5-fastapi` se o merge não ocorreu).
2. Dê **duplo clique** em `ABRIR_PARA_GRAVAR.cmd`. Ele prepara um ambiente virtual se necessário, instala as dependências caso estejam faltando, sincroniza automaticamente a credencial interna entre `backend/.env` e `frontend/.env`, inicia FastAPI e jogo e abre o Swagger.
3. Se o script pedir, configure `OPENAI_API_KEY` e `OPENAI_MODEL` no **`backend/.env`**, salve e pressione Enter. As chaves antigas do `.env` da raiz são migradas localmente quando disponíveis. A chave interna `API_KEY` não é a chave da OpenAI e é gerada automaticamente caso não exista.
4. Deixe visíveis: navegador em `http://127.0.0.1:8000/docs`, janela do jogo no menu e terminal **do backend**. Abra o `README.md` e a árvore de pastas do projeto no VS Code ou GitHub, **sem mostrar arquivos `.env`**.
5. Verifique que Configurações do jogo está com a IA ativada. **Comece a gravar ANTES de clicar em NOVO JOGO.**

**Se o jogo mostrar roteiro offline, não diga que houve geração real.** Confira se o backend está ligado, se as credenciais e modelo são válidos e se aparece `POST /v1/ia-generativa/texto 200` no terminal. Em caso de erro, interrompa a gravação, corrija e grave novamente.

## Vídeo — duração-alvo 1min30s a 2min

| Tempo | Mostre na tela | O que dizer |
| --- | --- | --- |
| 0–15s | Nome do jogo e pastas `frontend/` e `backend/` | “Este é o Memórias Perdidas. Para Front-End, separamos a integração de IA do jogo em uma API própria feita com FastAPI.” |
| 15–35s | Swagger `/docs`, expanda `POST /v1/ia-generativa/texto` | “Esta é a rota que recebe o contexto da narrativa. Ela exige uma API Key do grupo, usa um router e encaminha a geração para um provider.” |
| 35–80s | Jogo, `NOVO JOGO`, escolha `Ajudar o soldado`; depois terminal com `POST ... 200` | “O Pygame chama essa API com requests. A API é que acessa o modelo externo, e a fala retorna para aparecer no jogo.” **Espere o resultado aparecer.** |
| 80–105s | Código `frontend/game/systems/api_client.py`, `backend/routers/ia_generativa.py` e `backend/providers/openai_provider.py` | “O jogo não acessa diretamente a OpenAI. O fluxo é jogo, requests, FastAPI, router e provider. A autenticação está no backend.” |
| 105–120s | README com instruções; Swagger ou jogo ao final | “O repositório tem instalação, execução dos dois processos e testes da integração. A demonstração usa a mesma rota consumida durante o jogo.” |

**Se precisar encurtar:** mostre apenas Swagger, escolha no jogo, `POST 200` e arquitetura. **Não é necessário** gravar a campanha inteira nem gerar outra apresentação em PowerPoint.

## O que NÃO mostrar

- `backend/.env`, `frontend/.env`, chaves da OpenAI, a credencial `API_KEY` e telas do portal do provedor.
- Resultado de teste simulado como se fosse resposta real.
- Tela de erros, segredos do terminal, arquivos locais particulares ou informações pessoais.

## Depois de gravar

1. Publique o vídeo como **não listado** no YouTube (ou use um link de Drive acessível ao professor).
2. Substitua `PENDENTE` em `ENTREGA_CP5_FRONTEND.txt` pelo link verdadeiro da nova gravação.
3. Envie na atividade **CP5 - MVP do Jogo - Matéria de FRONTEND**, no Teams, o link do repositório `https://github.com/Danylukk/memorias-perdidas` e o link do vídeo novo.
4. Confirme que a atividade mostra **Entregue**. O vídeo anterior de PLN não substitui esta gravação de Front-End.

**Obs.:** o script abre tudo, mas não pode gravar ou publicar o vídeo sozinho. Se o computador estiver desligado ou offline, o ambiente local só poderá ser preparado quando ele voltar a ficar acessível.
