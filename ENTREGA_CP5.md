# Memórias Perdidas — Entrega CP5 (Vibe Coding e MVP)

**Disciplina:** NLP, Chatbots e Agentes Virtuais — FIAP
**Integrantes:** Rafael de Paiva Ramos (RM 563978) · Thiago Santana Danyluk (RM 562286)

Como executar, dependências e configuração da API: ver `README.md`.
Histórico técnico da primeira versão do MVP: ver `RELATORIO_MVP.md`.

> Campos marcados com **[GRUPO]** devem ser preenchidos pelos integrantes antes da entrega.

---

## 1. Atendimento aos requisitos da CP5

| Requisito | Onde está no MVP |
| --- | --- |
| Menu principal funcional | `game/screens/menu.py`: Novo Jogo, Fragmentos, Sair |
| Gameplay com HUD do mockup | `game/screens/gameplay.py`: barras de Vida/Energia, Fragmentos x/12, cena, NPC, caixa de diálogo, 4 escolhas |
| Mecânica 1: Escolhas narrativas | 3 rodadas × 4 escolhas (`game/systems/choices.py`) alterando atributos e a confiança de Darian |
| Mecânica 2: Diálogos com IA generativa | Fala de Darian gerada por LLM a cada escolha, com estado e histórico (`dialogue.py`, `prompt_builder.py`) |
| Mecânica 3: Fragmentos de memória | Desbloqueio por regras em Python e texto da lembrança gerado pelo LLM; tela Fragmentos (`fragments.py`) |
| Mecânica extra: Sistema comportamental (CP4 §1.6) | Empatia, Agressividade, Curiosidade, Egoísmo e Lealdade definem o desfecho (`ending.py`) |
| Começo, meio e fim | Abertura → 3 rodadas → tela de desfecho (“Kael, O Protetor” etc.) |
| Integração real de IA generativa (texto) | OpenAI Responses API via SDK oficial (`openai_client.py`); rótulo “Resposta narrativa — ChatGPT (LLM)” |
| IA generativa de imagem (assets pré-gerados) | Kael, Darian, cenário, logo, botões e caixa de diálogo gerados com ChatGPT na CP4 e usados no jogo |
| Extra: testes automatizados | 60 testes (`pytest -q`), sem rede |
| Extra: tratamento de erro da IA | Fala de reserva roteirizada e identificada; o jogo continua; “Tentar IA de novo [R]” |

---

## 2. Diário de Mudanças em relação à CP4

| Item alterado | O que estava na CP4 | O que foi implementado | Justificativa técnica |
| --- | --- | --- | --- |
| Personagem Lira | POC com três personagens: Kael, Darian e Lira | Somente o encontro Kael × Darian. O fragmento “Lira” não existe; os espaços excedentes aparecem bloqueados | O PNG aprovado da Lira não está no repositório nem no pacote de assets do projeto. Uma segunda cena exigiria nova ficha de NPC, política de segredos e prompts. Priorizamos um encontro completo, com começo, meio e fim e IA real. Impacto: a Lira fica para uma versão futura, e o sistema de NPC (`characters.json` + `PromptBuilder`) já comporta novos personagens |
| Opções do menu | Novo Jogo, Continuar, Fragmentos, Configurações e Sair | Novo Jogo, Fragmentos e Sair | “Continuar” depende de save/load, que não existe no MVP. Não há opções configuráveis em jogo, porque chave e modelo ficam no `.env`. Botões sem função seriam enganosos. Impacto: nenhuma mecânica depende deles |
| Mecânica de Exploração | Percorrer ambientes e investigar ruínas | Não implementada como movimentação livre. A cena é fixa, com escolhas como “Examinar o medalhão” | O escopo do MVP foi concentrado nas mecânicas que usam IA. Movimentação exigiria mapa, colisão e novos assets. Impacto: continuam implementadas 3 mecânicas da CP4 (escolhas, diálogos com IA e fragmentos), mais o sistema comportamental |
| Escolhas do encontro | Tabela §1.6: Ajudar, Ameaçar e Perguntar sobre o passado. Mockup: 4 escolhas | Rodada 1 igual ao mockup. Rodada 2 inclui “Ameaçar Darian” e “Perguntar sobre o passado” com os efeitos da CP4. A rodada 3 traz a decisão final | Uma única escolha não dava “meio e fim” à sessão. Em “Ameaçar” foram acrescentados Vida −10 e Confiança −15, para a resistência de Darian (prevista na CP4) ter efeito mecânico. Valores limitados a 0–100 |
| Ferramenta de IA de texto em tempo de execução | ChatGPT (interface), com “API/SDK de LLM (previsto)” a definir | OpenAI Responses API pelo SDK oficial `openai`. Modelo configurável no `.env` e validado com `gpt-5.6-luna` | A interface web não pode ser chamada pelo jogo. A API é o mesmo provedor do ChatGPT. Timeout de 25 s, sem retries automáticos e limite de 512 tokens, para controlar latência e custo (CP4 §6.4 e §6.5) |
| Fallback local | Previsto na CP4 (§2.2.3 e §6.4) | A primeira versão do MVP mostrava apenas “falha”. Agora há falas e memórias de reserva roteirizadas, sempre identificadas em vermelho como reserva | Retoma o que a CP4 previa. A reserva nunca é rotulada como gerada por IA e só aparece quando a geração falha. Impacto: o jogo segue até o fim mesmo sem internet ou sem chave |
| Arte dos fragmentos | Um ícone gerado por IA para cada fragmento (mockup) | Os fragmentos desbloqueados usam um recorte do cenário oficial das ruínas | Não havia arte aprovada por fragmento. Gerar imagens novas sem revisão de consistência contrariaria a estratégia da CP4 (§6.2). Impacto apenas visual |
| Quantidade de fragmentos | Contador x/12 | 4 fragmentos obtíveis (A Batalha, O Medalhão, Darian, Mãos Manchadas) e 8 bloqueados | Cada fragmento precisa de condição, tema de prompt e texto de reserva. Quatro fragmentos cobrem os perfis de escolha do encontro. Os nomes “A Ordem de Arkan” e “Lira” dependem de enredo e personagem ainda não implementados |
| Persistência | Não especificada | As memórias duram até o jogo ser fechado; não há save em disco | Save/load não está entre as mecânicas da CP4 e não era necessário para o fluxo de uma sessão |

Sem mudança: título, gênero, premissa, plataforma (PC), tecnologia (Python + Pygame + JSON) e a geração de imagens offline com ChatGPT.

---

## 3. Diário de Vibe Coding

**Ferramentas:** Claude Code (terminal), usado nesta etapa da CP5. **[GRUPO]** Indiquem a ferramenta usada na primeira versão do MVP (a de `RELATORIO_MVP.md`).

### Prompts-chave

> O enunciado exige prompts **reais**. Os prompts 1 a 4 abaixo foram de fato usados nesta sessão.
> **[GRUPO]** Acrescentem pelo menos 1 prompt real da primeira versão do MVP e completem a coluna “Revisão do grupo”.

**Prompt 1: obter o projeto**
- *Pedido:* “preciso que você pegue esse arquivo para realizarmos o jogo https://github.com/Danylukk/memorias-perdidas.git”
- *O que a IA gerou:* clonou o repositório, criou o `.venv`, instalou as dependências, criou o `.env` vazio e rodou os 45 testes existentes (todos passaram).
- *Ajustes:* o README recomenda Python 3.12. O ambiente usou 3.13.14 e os testes passaram. Chave e modelo continuam sob responsabilidade do grupo.
- *Revisão do grupo:* **[GRUPO]**

**Prompt 2: comparar o relatório da CP4 com o código**
- *Pedido:* “pode ler pra mim” (PDF do relatório da CP4)
- *O que a IA gerou:* resumo do relatório e uma tabela com o que a CP4 promete e ainda não existe no código (Lira, menu completo, tela de Fragmentos, escolha “Ameaçar”, fallback).
- *Ajustes:* a IA apontou que a primeira versão contradizia a CP4 ao recusar qualquer fallback. Esse ponto virou a mudança “Fallback local” do Diário de Mudanças.
- *Revisão do grupo:* **[GRUPO]**

**Prompt 3: plano da CP5**
- *Pedido:* “poderia me ajudar com isso” (PDF do enunciado da CP5)
- *O que a IA gerou:* comparação com a rubrica e uma lista dos riscos de nota: fim de sessão fraco, apenas 2 das 4 mecânicas da CP4, ausência do Diário de Mudanças. Propôs 3 rodadas, fragmentos, desfecho e fallback.
- *Decisões do grupo:* escopo “plano proposto”, sem a Lira (não há imagem dela) e commits numa branch local `cp5`, sem push.
- *Revisão do grupo:* **[GRUPO]**

**Prompt 4: implementação (continuação do Prompt 3, com as decisões acima)**
- *O que a IA gerou:* `choices.py` com 3 rodadas; `fragments.py`; `ending.py`; `Encounter` com rodadas, histórico e fragmentos; prompt de fragmento; telas de Fragmentos e de Desfecho; botão Fragmentos no menu; 15 testes novos.
- *Correções feitas durante a própria sessão:*
  1. Dois testes antigos quebraram. O serviço passou a receber o histórico, e a falha passou a mostrar a fala de reserva em vez da mensagem de erro. Os testes foram atualizados para o novo comportamento.
  2. Em `test_endings`, dois casos estavam com expectativa errada. Exemplo: a sequência 4→6→12 soma Egoísmo 4 contra Agressividade 2, então o desfecho correto é “Sobrevivente”. A lógica do jogo estava certa; os dados do teste foram corrigidos.
  3. As telas foram renderizadas em PNG para inspeção. O título da caixa de diálogo sobrepunha a moldura e o rótulo “reserva” passava da borda do painel de fragmentos. Posição e texto foram ajustados.
  4. Ao repetir a geração, o aviso “Memória recuperada” sumia. Isso foi corrigido: o aviso só é limpo numa nova escolha.
- *Revisão do grupo:* **[GRUPO]** O que vocês conferiram, mudaram ou rejeitaram. Exemplos: textos das falas de reserva, efeitos das escolhas, nomes dos desfechos.

**Prompt 5:** **[GRUPO]** Próximo prompt real, por exemplo o teste com a API real ou um ajuste pedido depois de jogar.

### Explicação do código principal

> **[GRUPO] Obrigatório e escrito por vocês, sem IA** (exigência da CP5, Etapa 3). Sugestão de roteiro:
> 1. O que acontece do clique em uma escolha até a fala aparecer (`GameplayScreen` → `Encounter.choose` → thread → `DialogueService` → `OpenAIClient` → fila → `update`).
> 2. Por que o estado é alterado em Python antes da chamada à IA, e por que a resposta da IA nunca altera o estado.
> 3. Como o `PromptBuilder` impede que segredos de Darian cheguem ao modelo.
> 4. Como os fragmentos são desbloqueados e quem escreve o texto deles.
> 5. O que acontece quando a API falha.

---

## 4. Checklist de testes manuais

> **[GRUPO]** Executem com a chave configurada e preencham “Resultado obtido”.

| # | Mecânica / tela | Passos | Resultado esperado | Resultado obtido |
| --- | --- | --- | --- | --- |
| 1 | Menu | Abrir o jogo | Logo, Kael, botões Novo Jogo, Fragmentos e Sair | |
| 2 | Início | Novo Jogo | Ruínas, Kael e Darian, “Você... está vivo?”, Rodada 1/3, Confiança 20 | |
| 3 | Escolha + IA | Clicar “Ajudar o soldado” | “Darian está pensando...”, depois uma fala com o rótulo ChatGPT (LLM). Empatia 2, Lealdade 1, Confiança 30 | |
| 4 | Bloqueio | Clicar em várias opções durante a espera | Nada muda; apenas uma requisição | |
| 5 | Rodada 2 | “Estancar o ferimento” | Energia 85, Confiança 40, “Memória recuperada: Darian” | |
| 6 | Fragmentos | Tecla F | Fragmento Darian desbloqueado com texto do LLM; os demais bloqueados | |
| 7 | Rodada 3 | “Exigir a verdade” | Fragmento A Batalha desbloqueado; botão “Ver desfecho” | |
| 8 | Desfecho | Enter | “Kael, O Protetor”, atributos, destino de Darian, 2/12 fragmentos | |
| 9 | Caminho agressivo | Novo Jogo → Quem é você? → Ameaçar → Exigir a verdade | Vida 90, fragmento Mãos Manchadas, desfecho “O Implacável” | |
| 10 | Fallback | Desligar a internet (ou esvaziar o `.env`) e jogar | Fala em vermelho “fala de reserva (roteirizada)”; o jogo avança até o desfecho | |
| 11 | Repetir IA | Com falha, reconectar e apertar R | Nova fala do LLM; atributos inalterados | |
| 12 | Janela | Redimensionar e fechar durante a espera | Proporção mantida; fecha sem travar | |
| 13 | Voltar ao menu | Esc no gameplay e depois Fragmentos no menu | Menu; os fragmentos da última partida aparecem | |

**Testes automatizados:** `pytest -q` → 60 aprovados. Cobrem efeitos das 12 escolhas, limites 0–100, 3 rodadas, desbloqueio de fragmentos, reservas, desfechos, prompts, validação de respostas, erros da API e um percurso completo pela interface.

---

## 5. Roteiro sugerido para o vídeo (2 a 5 min)

1. (20 s) Menu e apresentação do jogo e da proposta da CP4.
2. (90 s) Partida completa: Ajudar → Estancar → Exigir a verdade. Mostrar a espera, a fala gerada com o rótulo ChatGPT (LLM) e a mudança dos atributos no painel.
3. (30 s) Tecla F: fragmentos desbloqueados, com texto gerado pela IA.
4. (20 s) Tela de desfecho.
5. (40 s) Segunda partida rápida pelo caminho agressivo, para mostrar outro desfecho e a IA reagindo de outro jeito.
6. (20 s) Fallback: sem internet, a fala de reserva aparece identificada e o jogo continua.
7. (10 s) `pytest -q` rodando no terminal.
