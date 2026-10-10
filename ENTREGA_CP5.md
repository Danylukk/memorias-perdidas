# Memórias Perdidas — Entrega CP5 (Vibe Coding e MVP)

**Disciplina:** NLP, Chatbots e Agentes Virtuais — FIAP
**Integrantes:** Rafael de Paiva Ramos (RM 563978) · Thiago Santana Danyluk (RM 562286)

Como executar, dependências e configuração da API: ver `README.md`.
Histórico técnico da primeira versão do MVP: ver `RELATORIO_MVP.md`.

**Repositório público (main):** https://github.com/Danylukk/memorias-perdidas
**Relatório de validação:** [VALIDACAO_CP5_2026-10-09.md](VALIDACAO_CP5_2026-10-09.md).
**Evidências visuais:** [painel de telas](docs/evidencias/painel_validacao.jpg).

> Campos marcados com **[GRUPO]** devem ser preenchidos pelos integrantes antes da entrega.

---

## 1. Atendimento aos requisitos da CP5

| Requisito | Onde está no MVP |
| --- | --- |
| Mesmo jogo da CP4 | Mesmo título, gênero (RPG narrativo dark fantasy), premissa, personagens (Kael, Darian e Lira) e objetivo (recuperar fragmentos, decidir em quem confiar e quem Kael vai se tornar) |
| Menu principal (Figura 4) | `game/screens/menu.py`: logo, Kael, NOVO JOGO, CONTINUAR, FRAGMENTOS (com cristal), CONFIGURAÇÕES e SAIR, com rodapé “Assets gerados por IA” |
| Gameplay (Figura 5) | `game/screens/gameplay.py`: cena, retrato de Kael com barras de Vida e Energia, cristal com “Fragmentos: x/12”, NPC, caixa de diálogo com retrato e nome, 4 escolhas em linha e rodapé de assets |
| Fragmentos de Memória (Figura 6) | `game/screens/fragments.py`: grade 4×3 com A Batalha, A Ordem de Arkan, Lira e Darian, espaços bloqueados, painel do fragmento selecionado (imagem, citação e descrição) e botão VOLTAR |
| Mecânica 1: Exploração | Kael caminha pelas ruínas e investiga o estandarte, as espadas, o soldado caído e o próprio medalhão (`journey.py`) |
| Consequências entre cenas | Lira sabe como Kael tratou Darian: fala de abertura, confiança inicial e contexto do LLM mudam (`journey.py`, `prompt_builder.py`) |
| Mecânica 2: Escolhas narrativas | Cada escolha altera atributos, vida, energia e confiança; a decisão final define em quem Kael confia (`choices.py`, `ending.py`) |
| Mecânica 3: Diálogos com IA generativa | Darian e Lira respondem pelo LLM, com personalidade, conhecimento permitido, segredos e estado; o LLM também sugere as 4 próximas respostas de Kael (`prompt_builder.py`, `dialogue.py`) |
| Mecânica 4: Fragmentos de memória | Personagens (confiança), locais e objetos (investigação) desbloqueiam lembranças escritas pelo LLM (`fragments.py`) |
| Sistema comportamental (CP4 §1.6) | Empatia, Agressividade, Curiosidade, Egoísmo e Lealdade entram no contexto do LLM e definem o desfecho |
| Começo, meio e fim | Despertar (Darian) → exploração → Lira → decisão → desfecho |
| Integração real de IA: texto | OpenAI Responses API pelo SDK oficial (`openai_client.py`); rótulo “Resposta narrativa — ChatGPT (LLM)” e “Lembrança — ChatGPT (LLM)” |
| Integração real de IA: imagem | Todos os visuais são os assets aprovados da CP4, gerados com ChatGPT e identificados no rodapé de cada tela |
| Extra: testes automatizados | 94 testes (`pytest -q`), sem rede; 13 regressões adicionadas na revisão de 09/10/2026 |
| Extra: mecânicas adicionais | Save/Continuar, galeria de fragmentos, perfil (TAB), decisão de confiança com desfechos |
| Extra: tratamento de erro da IA | Roteiro offline ramificado; “Tentar IA [R]” sem reaplicar efeitos; o turno continua por roteiro nos cenários de falha cobertos pelos testes |
| Extra: polimento | Fade entre telas e cenas, texto animado, efeitos das escolhas exibidos na tela, aviso de memória recuperada, configurações |

---

## 2. Diário de Mudanças em relação à CP4

As telas, os três personagens, as quatro mecânicas, os fragmentos do mockup e o menu completo seguem a CP4.
As divergências que restam são estas:

| Item alterado | O que estava na CP4 | O que foi implementado | Justificativa técnica |
| --- | --- | --- | --- |
| Ferramenta de IA de texto em tempo de execução | ChatGPT (interface), com “API/SDK de LLM (previsto)” a definir no MVP (§3 e §4) | OpenAI Responses API pelo SDK oficial `openai`, com Structured Outputs (JSON Schema estrito) nos turnos. Modelo configurável no `.env`; a primeira versão foi validada com `gpt-5.6-luna` | A interface web não pode ser chamada pelo jogo; a própria CP4 previa definir a API no MVP. A API é do mesmo provedor do ChatGPT. Timeout de 25 s, sem retries automáticos e limite de tokens para controlar latência e custo (§6.4 e §6.5) |
| Respostas de Kael | Mockup: 4 escolhas fixas | Turno 1 igual ao mockup. Nos turnos seguintes, o LLM sugere as 4 respostas de Kael junto com a fala do NPC, cada uma marcada com uma intenção de lista fixa (curiosidade, empatia, lealdade, agressividade, egoísmo) que o Python converte em efeitos | Com opções fixas, a conversa não reagia ao que o NPC dizia. Gerar as opções mantém o diálogo coerente (CP4 §2.2). A IA não define números: a intenção é validada pelo JSON Schema, preservando a regra de que o estado pertence ao jogo. Impacto: validação extra (4 opções, até 36 caracteres, sem repetição) e textos curtos para caber nos botões do mockup |
| Tabela de escolhas (§1.6) | Ajudar Darian (Empatia +2, Lealdade +1); Ameaçar Darian (Agressividade +2, Empatia −1); Perguntar sobre o passado (Curiosidade +2) | Mesmos efeitos. Foram acrescentados efeitos em confiança, vida e energia (ex.: Ameaçar também dá Vida −10 e Confiança −15) | Na CP4, a confiança e a resistência de Darian eram “efeitos narrativos esperados”; no MVP elas viraram números, para influenciar os fragmentos e o desfecho |
| Fallback local | Previsto (§2.2.3 e §6.4) | Roteiro offline ramificado em JSON: 4 caminhos por intenção, para Darian (5 turnos) e Lira (3 turnos). Sem chave, o jogo roda inteiro por ele; com a API, cobre só os turnos que falharem | A primeira versão do MVP mostrava apenas “falha”. Um fallback genérico quebrava a história; o roteiro por caminho mantém a coerência sem IA. O texto é sempre identificado como “roteiro offline” e nunca rotulado como gerado por IA |
| Exploração | “Percorrer ambientes, investigar ruínas” | Exploração lateral em uma única cena (o cenário oficial das ruínas), com 5 pontos de interesse (estandarte, espadas, soldado caído, medalhão, Darian) e a Lira | Havia apenas um cenário aprovado; novos ambientes exigiriam gerar e aprovar novas imagens (§6.2). Impacto: a mecânica existe e desbloqueia fragmentos, em escala de MVP |
| Fragmentos | Contador 2/12; visíveis: A Batalha, A Ordem de Arkan, Lira, Darian | Os mesmos 4 fragmentos podem ser recuperados; os outros 8 espaços aparecem bloqueados, com as artes de “bloqueado” do mockup | Os 8 fragmentos restantes não têm nome nem enredo definidos na CP4 |
| Arte dos fragmentos e retratos | Ícones gerados por IA no mockup | Ícones, artes de “bloqueado” e cristal recortados do próprio mockup da Figura 6; retratos recortados dos sprites oficiais; Lira extraída em resolução original do PDF (Figura 2) | Não havia arquivos separados desses elementos. Recortar os assets aprovados evita gerar imagens novas e mantém a consistência visual (§6.2). Os textos são renderizados pelo jogo (§6.3) |
| Desfecho | “Definir quem Kael deseja se tornar” e “decidir em quais personagens confiar” (§1.7), sem tela no mockup | Tela de desfecho com o perfil dominante e o resultado da decisão de confiança | Necessária para o “fim” exigido pela CP5; segue a identidade visual das outras telas |
| Conteúdo narrativo novo | Premissa, personagens e fragmentos, sem roteiro detalhado | Falas do roteiro offline, fatos permitidos de Lira (“conhece Kael e evita revelar tudo”), descrições dos fragmentos e textos dos desfechos, escritos com o Claude Code | A CP4 não tinha roteiro escrito. O conteúdo respeita as regras da CP4: não revela o passado de Kael nem quem causou a batalha. **[GRUPO]** revisar e ajustar em `data/` |

Sem mudança: título, gênero, premissa, plataforma (PC), tecnologia (Python + Pygame + JSON), proporção 16:9 das telas, personagens e geração de imagens offline com ChatGPT.

---

## 3. Diário de Vibe Coding

**Ferramentas:** Claude Code (terminal), usado nesta etapa da CP5 (branch `paiva`). Antigravity com Gemini 3.1 Pro, orientado pelo ChatGPT, usado na branch `feat/vertical-slice`, cujas ideias foram incorporadas no Prompt 9. **[GRUPO]** Indiquem a ferramenta usada na primeira versão do MVP (a de `RELATORIO_MVP.md`).

### Prompts-chave

> O enunciado exige prompts **reais**. Os prompts 1 a 9 abaixo foram de fato usados nesta sessão.
> **[GRUPO]** Acrescentem pelo menos 1 prompt real da primeira versão do MVP e completem a “Revisão do grupo”.

**Prompt 1: obter o projeto**
- *Pedido:* “preciso que você pegue esse arquivo para realizarmos o jogo https://github.com/Danylukk/memorias-perdidas.git”
- *O que a IA gerou:* clonou o repositório, criou o `.venv`, instalou as dependências, criou o `.env` vazio e rodou os 45 testes existentes (todos passaram).
- *Ajustes:* o README recomenda Python 3.12. O ambiente usou 3.13.14 e os testes passaram.
- *Revisão do grupo:* **[GRUPO]**

**Prompt 2: comparar o relatório da CP4 com o código**
- *Pedido:* “pode ler pra mim” (PDF do relatório da CP4)
- *O que a IA gerou:* resumo do relatório e uma tabela com o que a CP4 promete e ainda não existia no código (Lira, menu completo, tela de Fragmentos, escolha “Ameaçar”, fallback).
- *Ajustes:* a IA apontou que a primeira versão contradizia a CP4 ao recusar qualquer fallback.
- *Revisão do grupo:* **[GRUPO]**

**Prompt 3: plano da CP5**
- *Pedido:* “poderia me ajudar com isso” (PDF do enunciado da CP5)
- *O que a IA gerou:* comparação com a rubrica e uma lista dos riscos de nota (fim de sessão fraco, poucas mecânicas, ausência do Diário de Mudanças), com um plano de rodadas, fragmentos, desfecho e fallback.
- *Decisões do grupo:* escopo “plano proposto” e commits numa branch local `cp5`, sem push. Naquele momento a Lira ficou de fora porque não achamos a imagem dela (corrigido no Prompt 7).
- *Revisão do grupo:* **[GRUPO]**

**Prompt 4: implementação (continuação do Prompt 3)**
- *O que a IA gerou:* rodadas fixas, fragmentos, desfecho, telas de Fragmentos e de Desfecho e 15 testes novos.
- *Correções feitas durante a própria sessão:* dois testes antigos atualizados para o novo comportamento; duas expectativas erradas em `test_endings` (a lógica estava certa); ajustes de layout depois de renderizar as telas em PNG; o aviso “Memória recuperada” sumia ao repetir a geração.
- *Revisão do grupo:* **[GRUPO]**

**Prompt 5: opções geradas pela IA**
- *Pedido:* “o que eu queria era que a ia gerasse as perguntas, tipo você ainda está vivo, sim, mas quem eu sou, daí ele falava e ia continuando sabe?”
- *O que a IA gerou:* conversa em turnos em que o LLM devolve, em JSON Schema estrito, a fala do NPC e 4 opções de Kael; a tabela intenção → efeitos em Python; e a função `parse_turn`, que valida o JSON.
- *Correções feitas durante a própria sessão:* os fragmentos, que dependiam de escolhas fixas, passaram a depender do estado; as regras de estilo (“sem JSON”) foram separadas do formato do turno, para o prompt não se contradizer.
- *Revisão do grupo:* **[GRUPO]** Conferir, com a API real, se as opções geradas fazem sentido.

**Prompt 6: história ramificada sem a API**
- *Pedido:* “quero seguir primeiro sem a api [...] se escolhi ajudar ele, a história seguiria nessa reta e as opções de diálogo mudam”
- *O que a IA gerou:* roteiro ramificado em JSON, com 4 caminhos definidos pela intenção da escolha, e modo offline automático quando o `.env` está vazio.
- *Decisões do grupo:* sem a API, o modo offline aparece como “roteiro offline” normal, sem aviso vermelho.
- *Correções feitas durante a própria sessão:* as reservas genéricas foram removidas, porque não seguiam a história.
- *Revisão do grupo:* **[GRUPO]**

**Prompt 7: fidelidade total à CP4**
- *Pedido:* “quero que você seja fiel às imagens que estão no documento e como ele está escrito, refaça o que fizemos para podermos continuar” (com o PDF da CP4)
- *O que a IA gerou:* extraiu as imagens do PDF em resolução original. Kael e Darian eram idênticos aos do repositório, e a **Lira** oficial estava no PDF. Recortou dos mockups as artes dos fragmentos, as de “bloqueado” e o cristal. Refez as três telas nas proporções e posições dos mockups (16:9, menu com 5 opções, HUD com retrato e barras, caixa de diálogo com retrato, escolhas em linha, rodapé “Assets gerados por IA”). Trocou os fragmentos inventados pelos 4 do mockup. Adicionou Lira, exploração, decisão de confiança, CONTINUAR (save em JSON) e CONFIGURAÇÕES.
- *Correções feitas durante a própria sessão:* o primeiro recorte do retrato de Darian pegou o ombro; as opções do roteiro foram encurtadas (até 30 caracteres) para caber nos botões do mockup; o contador de fragmentos passava da moldura; os textos de efeito se acumulavam no topo da tela; Kael ficava sobre Darian na cena da Lira; uma expectativa de teste errada (empate Empatia × Lealdade resolve para “O Protetor”).
- *Revisão do grupo:* **[GRUPO]** Revisar o roteiro da Lira e o texto da “Ordem de Arkan”, que foram escritos pela IA.

**Prompt 8: comparar com a branch do Thiago**
- *Pedido:* link da conversa do ChatGPT em que o Thiago conduziu a branch `feat/vertical-slice` com o Antigravity (Gemini): “depois consegue acessar esse site para terminarmos?”
- *O que a IA gerou:* leu a conversa, rodou a branch numa cópia separada e comparou com a `paiva`. Encontrou um erro de import em `explore.py` (`panel` não importado) que fecha o jogo ao clicar em Novo Jogo — os 53 testes passavam porque nenhum desenha essa tela. Também viu que, sem chave da API, aquela versão fica presa no encontro com Darian, e que a exploração usava quadrados coloridos no lugar dos sprites.
- *Decisão do grupo:* manter a `paiva` como base e trazer as boas ideias da outra branch. A `feat/vertical-slice` não foi alterada.
- *Revisão do grupo:* **[GRUPO]**

**Prompt 9: trazer as ideias da vertical slice**
- *Pedido:* “quero” (aceitando: Lira reage ao que Kael fez com Darian; medalhão e soldado caído na exploração; fade entre cenas).
- *O que a IA gerou:* `historia_da_partida` no estado e no prompt; cálculo do caminho predominante com Darian; abertura da Lira em 4 variações no roteiro; ajuste da confiança inicial da Lira; 2 novos pontos de exploração com efeitos aplicados uma vez; 5 botões na exploração; fade no app e nas fases do gameplay; 5 testes novos.
- *Correções feitas durante a própria sessão:* um teste antigo entrou em loop infinito porque clicava no 4º botão esperando “Falar com Lira” (agora é o 5º) — o teste foi corrigido e ganhou limite de passos; os textos de efeito se sobrepunham; o nome “Soldado caído” ficava atrás do Kael (marcadores passaram a ser desenhados por cima dos personagens).
- *Revisão do grupo:* **[GRUPO]** Revisar as 4 falas de abertura da Lira em `data/roteiro_offline.json`.

### Explicação do código principal

> **[GRUPO] Obrigatório e escrito por vocês, sem IA** (exigência da CP5, Etapa 3). Sugestão de roteiro:
> 1. Como a `Journey` organiza a partida (fases) e como o `Encounter` conduz uma conversa em turnos.
> 2. O que acontece do clique numa escolha até a fala aparecer (thread → `DialogueService` → `OpenAIClient` → fila → `update`).
> 3. Por que o estado é alterado em Python antes da chamada à IA, e por que a IA só escolhe uma “intenção” e não números.
> 4. Como o `PromptBuilder` impede que os segredos de Darian e Lira cheguem ao modelo.
> 5. Como os fragmentos são desbloqueados (confiança, investigação) e quem escreve o texto deles.
> 6. O que acontece quando a API falha ou não está configurada (roteiro offline).

---

## 4. Checklist de testes manuais

> **[GRUPO]** Executem com a chave configurada (e depois sem ela) e preencham “Resultado obtido”.

| # | Mecânica / tela | Passos | Resultado esperado | Resultado obtido |
| --- | --- | --- | --- | --- |
| 1 | Menu | Abrir o jogo | Igual à Figura 4: logo, Kael, 5 botões, rodapé de assets; CONTINUAR apagado sem save | |
| 2 | Início | NOVO JOGO | Igual à Figura 5: Darian diz “Você... está vivo?”, com as 4 escolhas do mockup | |
| 3 | Escolha + IA | “Ajudar o soldado” | “Darian está pensando...”, depois fala com o rótulo ChatGPT (LLM); acima de Kael aparece “Empatia +2, Lealdade +1, Confiança de Darian +10” | |
| 4 | Opções geradas | Ler as 4 novas opções | Respostas curtas que reagem à fala de Darian | |
| 5 | Bloqueio | Clicar várias vezes durante a espera | Nada muda; apenas uma requisição | |
| 6 | Fragmento de personagem | Escolher respostas gentis ou leais | Confiança ≥ 40 → “Memória recuperada: Darian” | |
| 7 | Exploração | “Explorar as ruínas” → andar com ←/→ → E no estandarte; depois Soldado caído e Medalhão (duas vezes cada) | Kael caminha; “Memória recuperada — A Ordem de Arkan”, com texto do LLM; Energia −5; soldado e medalhão alteram o perfil só na primeira vez | |
| 8 | Fragmentos | Tecla F | Igual à Figura 6: cartões desbloqueados com arte, detalhe com citação e descrição | |
| 9 | Lira | “Falar com Lira” e 3 turnos | Lira responde pelo LLM com retrato próprio; confiança ≥ 45 → fragmento Lira | |
| 9b | Lira lembra de Darian | Jogar uma vez ajudando Darian e outra abandonando | Abertura da Lira e confiança inicial diferentes (TAB); falas do LLM coerentes com o que Kael fez | |
| 10 | Decisão | “Decidir em quem confiar” → escolher | Desfecho com perfil de Kael e destino conforme a confiança | |
| 11 | Continuar | Esc no meio da partida → CONTINUAR | A partida volta exatamente do ponto salvo | |
| 12 | Configurações | Desligar “Diálogos com IA” | Menu mostra “roteiro offline”; nova partida sem chamadas de rede | |
| 13 | Modo offline | Esvaziar o `.env` e jogar dois caminhos (Ajudar × Ir embora) | Falas e opções diferentes em cada caminho; o jogo chega ao desfecho | |
| 14 | Falha com API | Desligar a internet no meio da partida | “IA indisponível — roteiro offline”; a história continua; R tenta de novo | |
| 15 | Janela | Redimensionar; fechar durante a espera | Proporção mantida; fecha sem travar | |

**Testes automatizados:** primeira versão da branch Paiva: 81 aprovados. Revisão de 09/10/2026: `python -m pytest -q` → **94 aprovados**. Os testes não são declarações de execução manual pelo grupo. Cobrem personagens e fragmentos da CP4, efeitos e limites, roteiro offline completo (Darian e Lira, 4 caminhos), opções geradas e validação do JSON, envio do JSON Schema à API, falha e nova tentativa, jornada completa (Darian → exploração → Lira → decisão), Lira reagindo a Darian, pontos de exploração, fade, desfechos, save/continuar, configurações e percursos completos pela interface.

---

## 5. Roteiro sugerido para o vídeo (2 a 5 min)

**Vídeo de demonstração:** [Memórias Perdidas — MVP CP5](https://youtu.be/nB9UEZMc7IU)

Link informado por Thiago em 09/10/2026. A duração, a disponibilidade pública e o conteúdo do vídeo ainda não foram verificados nesta revisão.

1. (20 s) Menu: mostrar que é igual ao mockup da CP4 e o rodapé “Assets gerados por IA”.
2. (70 s) Darian: “Ajudar o soldado” e mais alguns turnos. Mostrar a espera, a fala com o rótulo ChatGPT (LLM), as opções geradas mudando conforme a fala e os efeitos aparecendo acima de Kael.
3. (40 s) Exploração: caminhar até o estandarte e as espadas e mostrar a lembrança escrita pelo LLM.
4. (20 s) Tecla F: a tela de Fragmentos igual ao mockup.
5. (50 s) Lira: conversa e decisão de confiança; tela de desfecho.
6. (20 s) CONTINUAR e CONFIGURAÇÕES (desligar a IA → roteiro offline).
7. (10 s) `pytest -q` rodando no terminal.

---

## 6. Revisão técnica de 09/10/2026

Ver `VALIDACAO_CP5_2026-10-09.md` e `docs/evidencias/painel_validacao.jpg`.
Foram corrigidos saves antes da primeira escolha e após investigar o medalhão,
limites dos créditos e contador, leitura completa de falas e memórias longas e validação
de intenções distintas. O prompt foi esclarecido para permitir somente as opções pedidas
pelo esquema, e a fala offline de Lira que afirmava que Kael era soldado foi substituída
por uma referência ao comportamento dele nas ruínas. Não houve troca de personagens,
modalidade de IA, stack ou mecânicas.

**Prompt real 10 — revisão de entrega:**
> Hoje tem a entrega do MVP do projeto do jogo, verifique no teams o que o professor instruiu para a entrega, é a materia de PLN, verifque o que o professor está requisitando, e o nosso jogo está no github memorias-perdidas, verifique lá tambem todo o conteudo do jogo, aplique testes, verificações de Usabildiade, se da para mostrar ao professor se está fazendo sentido as coisas, verifique as branches o paiva subiu algumas verifique que elas foram as ultiams atualizações feitos do jogo, para fazer o merge para a main e tudo mais

- Ferramenta nesta etapa: ChatGPT Work / Codex.
- Resultado: conferência do enunciado e da CP4 no Teams/SharePoint, revisão das quatro branches,
  execução das suítes, reprodução da falha de desenho da vertical slice, correções focadas e
  13 testes de regressão, com inspeção de oito telas renderizadas.
- Ajustes e rejeições: a vertical slice não foi integrada integralmente porque fecha ao desenhar
  a exploração; as ideias compatíveis já estavam na Paiva. Correções e limites estão no relatório.
- Revisão e entendimento pelos integrantes: **[GRUPO]**. A explicação própria do código e os
  resultados dos testes manuais continuam sob responsabilidade dos integrantes.
