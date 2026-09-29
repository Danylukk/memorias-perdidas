# Memórias Perdidas

MVP acadêmico de **Processamento de Linguagem Natural, Chatbots e Agentes Virtuais — FIAP**.
RPG narrativo dark fantasy: enquanto Kael descobre quem era, o jogador decide quem ele será.

## Requisitos e instalação

Python 3.11+ com suporte às dependências. Ambiente validado: **Python 3.12.14 / Windows**.
Pygame 2.6.1, SDK oficial OpenAI, python-dotenv e pytest estão em `requirements.txt`.
Para reproduzir este ambiente, prefira Python 3.12; o Python global desta máquina é 3.14,
mas o `.venv` preparado para o projeto usa 3.12.

Em um terminal PowerShell na pasta do projeto, para preparar um ambiente novo
(o comando `python` deve apontar para a versão escolhida):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

O `.venv` desta entrega já está instalado. Basta ativá-lo. Também é possível executar
diretamente `.\.venv\Scripts\python.exe`, sem depender da ativação.

## Configuração da API

Se ainda não existir `.env`, copie o exemplo:

```powershell
Copy-Item .env.example .env
```

Edite o `.env` local e preencha `OPENAI_API_KEY` com sua credencial e `OPENAI_MODEL`
com o identificador de um modelo de texto disponível à sua conta e compatível com
a Responses API. Ambos são obrigatórios. O exemplo permanece vazio; a configuração
local foi fornecida pelo responsável pelo projeto. Reinicie o jogo após configurar.

Variáveis já definidas no ambiente têm precedência sobre o `.env`.
Não publique o `.env`: ele e suas variantes estão no `.gitignore`; `.env.example` é permitido.
Sem chave e modelo configurados, o jogo roda inteiro no **roteiro offline** (ver abaixo), sem acessar a rede.

## Executar

Com o ambiente ativado:

```powershell
python main.py
```

Sem ativação:

```powershell
.\.venv\Scripts\python.exe main.py
```

## Fluxo do jogo (fiel à CP4)

As três telas seguem os mockups da CP4 (16:9): **Menu Principal** (Figura 4), **Gameplay** (Figura 5)
e **Fragmentos de Memória** (Figura 6). Todos os rodapés identificam os assets gerados por IA.

**Menu:** NOVO JOGO, CONTINUAR, FRAGMENTOS, CONFIGURAÇÕES e SAIR (mouse, ↑/↓ + Enter; Esc sai).
CONTINUAR retoma a última partida salva; FRAGMENTOS mostra todas as memórias já recuperadas.

A jornada segue a premissa e o objetivo da CP4 (§1.3 e §1.7):

1. **Despertar — Darian (5 turnos).** Kael acorda nas ruínas; Darian pergunta **“Você... está vivo?”**
   com as 4 escolhas do mockup (Quem é você? / Você me conhece? / Ajudar o soldado / Ir embora).
   A cada escolha, o LLM gera a **fala de Darian** e **4 novas respostas curtas para Kael**, na mesma chamada.
2. **Exploração das ruínas.** Kael caminha pelo cenário (←/→ ou clique) e investiga locais e objetos
   (E ou botões 1–4): o **estandarte rasgado** desperta *A Ordem de Arkan*; as **espadas cravadas**
   despertam *A Batalha*. O texto de cada lembrança é escrito pelo LLM.
3. **Lira (3 turnos).** A curandeira que conhece Kael e evita revelar tudo o que sabe. Mesmo sistema
   de conversa, com a ficha e os segredos dela.
4. **Decisão final:** Confiar em Darian, em Lira, nos dois ou seguir sozinho.
5. **Desfecho:** quem Kael se tornou (atributo dominante), o destino conforme a confiança conquistada e
   os fragmentos recuperados.

Durante a conversa, as opções ficam bloqueadas e aparece **“Darian está pensando...”** (thread separada).
Os efeitos de cada escolha aparecem acima de Kael; **TAB** abre o perfil completo; **F** abre os Fragmentos;
**Esc** volta ao menu (o progresso é salvo). O botão de fechar a janela funciona durante a geração.

### Regras (sempre em Python)

A IA escreve o texto, mas nunca define números. Cada opção gerada vem marcada com uma **intenção**
de uma lista fixa, validada por JSON Schema; o Python converte a intenção em efeitos:

| Intenção | Efeitos |
| --- | --- |
| curiosidade | Curiosidade +1 |
| empatia | Empatia +1, Energia −5, Confiança +5 |
| lealdade | Lealdade +1, Confiança +5 |
| agressividade | Agressividade +1, Vida −5, Confiança −10 |
| egoismo | Egoísmo +1, Confiança −5 |

Escolhas fixas: Quem é você? (Curiosidade +1), Você me conhece? (Curiosidade +2), Ajudar o soldado
(Empatia +2, Lealdade +1, Confiança +10), Ir embora (Egoísmo +2, Confiança −10) e, da tabela da CP4 §1.6,
Perguntar sobre o passado (Curiosidade +2) e Ameaçar Darian (Agressividade +2, Empatia −1, Vida −10,
Confiança −15). Investigar um objeto novo custa Energia −5. Valores entre 0 e 100.
Confiança inicial: Darian 20, Lira 30.

| Fragmento (mockup) | Origem | Como desbloquear |
| --- | --- | --- |
| A Batalha | local | Examinar as espadas cravadas |
| A Ordem de Arkan | objeto | Investigar o estandarte rasgado |
| Lira | personagem | Confiança de Lira ≥ 45 |
| Darian | personagem | Confiança de Darian ≥ 40 |

Os outros 8 espaços da tela (12 no total, como no mockup) aparecem bloqueados.

**Desfecho:** o atributo mais alto define o título (Protetor, Companheiro, Buscador, Implacável ou
Sobrevivente; empate segue essa ordem). Confiar em Darian exige confiança ≥ 30; em Lira, ≥ 40;
nos dois, ambas — caso contrário o desfecho mostra a recusa ou a desconfiança.

### Roteiro offline e falhas da IA

`data/roteiro_offline.json` contém uma conversa **ramificada** para Darian e Lira, escrita com o Claude Code
e editável pelo grupo. Cada escolha leva a um **caminho** conforme a intenção: empatia/lealdade → **Cuidado**,
curiosidade → **Perguntas**, agressividade → **Confronto**, egoísmo → **Abandono**.

- **Sem chave/modelo no `.env`** (ou com a IA desligada em Configurações): o menu mostra “Diálogos: roteiro
  offline” e a partida inteira segue o roteiro, identificado na caixa de diálogo. Nenhuma chamada de rede.
- **Com a API configurada:** se uma geração falhar (sem internet, timeout, resposta inválida), aquele turno
  segue pelo roteiro com o aviso “IA indisponível — roteiro offline”; **Tentar IA [R]** faz nova solicitação
  sem reaplicar efeitos. Não há tentativas automáticas.
- Lembranças sem IA usam o texto do roteiro — para *A Batalha*, o texto gerado com ChatGPT na CP4 (§2.2.2).

### Configurações e save

CONFIGURAÇÕES liga/desliga os diálogos com IA, a tela cheia e o texto animado. Progresso, galeria de
fragmentos e configurações ficam em `save/` (JSON local, fora do Git). Ao terminar a jornada, o
progresso é apagado, mas as memórias continuam na galeria.

## Assets

Todos os visuais são os aprovados na CP4 (gerados com ChatGPT — geração de imagens):

- `assets/characters/`: Kael, Darian e **Lira** (extraída em resolução original do PDF da CP4, Figura 2).
- `assets/backgrounds/`: cenário das ruínas; `assets/ui/`: logo, botão, caixa de diálogo e cristal.
- `assets/fragments/`: artes dos fragmentos e dos espaços bloqueados, recortadas do mockup da Figura 6.
- `assets/portraits/`: retratos recortados dos sprites oficiais, para o HUD e a caixa de diálogo.

Nenhuma imagem nova foi gerada; os textos da interface são renderizados pelo jogo (CP4 §6.3).

## Arquitetura

```text
GameplayScreen → Journey (fases: darian → exploração → lira → decisão → fim)
                    ↓
                 Encounter → choices.apply_effects (estado atualizado pelo Python)
                    ↓ thread + fila de resultados
                 DialogueService ── PromptBuilder ── OpenAIClient → Responses API (JSON Schema)
                    ↓ falha ou modo offline
                 script.py (roteiro ramificado)
                    ↓
                 validação → fila → GameplayScreen → save/ (JSON)
```

- `game/models/`: estado imutável de Kael e dos NPCs. JSONs de `data/` são dados iniciais, não saves.
- `game/systems/journey.py`: fases da partida, exploração (pontos de interesse), decisão e save.
- `game/systems/encounter.py`: conversa em turnos com um NPC; decide os fragmentos desbloqueados
  e coordena a thread. Somente o loop principal atualiza o estado e desenha.
- `game/systems/choices.py`: escolhas fixas, tabela intenção → efeitos e serialização.
- `game/systems/script.py` + `data/roteiro_offline.json`: roteiro ramificado por personagem e caminho.
- `game/systems/fragments.py`: os 4 fragmentos do mockup, condições e textos de reserva.
- `game/systems/ending.py`: perfil de Kael e desfecho da decisão.
- `game/systems/prompt_builder.py`: regras fixas por personagem e contexto JSON com o estado atualizado.
- `game/systems/openai_client.py`: único local que usa o SDK. Timeout de 25 s, `max_retries=0`,
  `store=False`, Structured Outputs nos turnos. Apenas `output_text` sai do adaptador.
- `game/systems/dialogue.py`: `converse` valida o JSON do turno (fala + 4 opções de até 36 caracteres,
  sem repetição); rejeita respostas vazias, longas, com mais frases que o permitido ou com metalinguagem.
- `game/systems/save.py`: progresso, galeria e configurações em JSON.
- `game/screens/`: menu, gameplay, fragmentos, configurações e desfecho. As telas não conhecem a OpenAI.

O conhecimento privado dos NPCs não é serializado integralmente. O prompt recebe apenas fatos
conhecidos **e explicitamente permitidos**, a política de revelação e os temas proibidos.
`pode_revelar_passado` permanece `false` para Darian e Lira. Nenhuma saída da IA é executada,
convertida em atributos ou utilizada para liberar progressão.

As verificações textuais são guardrails simples: **não provam ausência de alucinações semânticas**.
Mesmo uma fala inadequada não altera o estado do jogo. A revisão narrativa com a API real continua necessária.

Referências usadas na integração: [Responses API](https://developers.openai.com/api/reference/python/resources/responses/methods/create)
e [SDK Python — retries e timeouts](https://developers.openai.com/api/reference/python).

## Testes e validação

Com o ambiente ativado, execute nesta ordem:

```powershell
python -m compileall .
pytest -q
```

O primeiro comando também visita o `.venv` quando ele fica dentro do projeto.
A suíte usa mocks e bloqueia conexões de rede por uma fixture automática. Nenhuma chamada real é feita
por `pytest -q`. Os testes de interface usam o driver SDL `dummy`, sem abrir janela.

Para testar somente regras, modelos e prompt, sem inicializar o Pygame:

```powershell
pytest -q tests/test_state.py tests/test_choices.py tests/test_prompt_builder.py tests/test_cp5_mechanics.py tests/test_encounter.py
```

## Validação manual real

Depois de configurar a credencial e o modelo, execute o jogo e escolha **Ajudar o soldado**.
Observe Empatia **2**, Lealdade **1**, Confiança **30**, a mensagem de espera e, finalmente,
a fala gerada. Fechar a janela deve continuar possível durante a espera.
Cada escolha faz uma requisição (fala + opções) e, se desbloquear um fragmento, mais uma por fragmento.
Uma partida completa faz de 8 a 12 requisições; uma nova tentativa explícita pode gerar nova cobrança.

Na primeira versão do MVP, uma chamada real com **gpt-5.6-luna**, usando **Ajudar o soldado**, retornou HTTP 200.
Foi corrigida a contagem de frases quando a fala vem entre aspas externas; a mesma resposta
recebida foi validada e exibida na janela nativa, sem nova solicitação. O estado permaneceu
Empatia 2, Lealdade 1, Confiança 30. Evidências e limites estão no relatório.

## Limites desta entrega

A jornada cobre um capítulo: Darian, exploração das ruínas, Lira e a decisão final. Dos 12 fragmentos,
os 4 do mockup podem ser recuperados; os demais aparecem bloqueados. A exploração é lateral, em uma
única cena. Não há combate. As mudanças em relação à CP4 estão justificadas em `ENTREGA_CP5.md`,
junto com o Diário de Vibe Coding e o checklist de testes. O histórico da primeira entrega do MVP
está em `RELATORIO_MVP.md`.
