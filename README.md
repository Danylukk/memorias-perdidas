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

## Fluxo demonstrável (CP5)

O menu tem **Novo Jogo**, **Fragmentos** e **Sair**. Enter inicia; F abre os Fragmentos; Esc sai do menu
ou volta a ele durante o gameplay quando não há geração pendente. O botão de fechar a janela funciona
durante a geração. A janela pode ser redimensionada; o conteúdo mantém sua proporção.

1. **Novo Jogo** abre as ruínas com Kael e Darian. A frase inicial roteirizada é **“Você... está vivo?”**,
   com as 4 opções do mockup da CP4 (Quem é você? / Você me conhece? / Ajudar o soldado / Ir embora).
2. A partir daí é uma **conversa de 5 turnos**. A cada escolha, o LLM gera, na mesma chamada, a **fala de
   Darian** e **4 novas opções** para Kael responder, reagindo ao que acabou de ser dito
   (ex.: “Estou... por que me olha como se não me conhecesse?” → “Sim, estou vivo... mas quem sou eu?”).
3. Enquanto isso, as opções ficam bloqueadas e aparece **“Darian está pensando...”** (thread separada).
4. Cada opção gerada vem marcada com uma **intenção** de uma lista fixa. **O Python** converte a intenção
   em efeitos; a IA escreve o texto, mas nunca define números:

   | Intenção | Efeitos |
   | --- | --- |
   | curiosidade | Curiosidade +1 |
   | empatia | Empatia +1, Energia −5, Confiança +5 |
   | lealdade | Lealdade +1, Confiança +5 |
   | agressividade | Agressividade +1, Vida −5, Confiança −10 |
   | egoismo | Egoísmo +1, Confiança −5 |

   Efeitos das opções fixas do turno 1: Quem é você? (Curiosidade +1), Você me conhece? (Curiosidade +2),
   Ajudar o soldado (Empatia +2, Lealdade +1, Confiança +10), Ir embora (Egoísmo +2, Confiança −10).
   Valores ficam entre 0 e 100; confiança inicial de Darian: 20.
5. A resposta é pedida no modo **Structured Outputs** (JSON Schema estrito) e validada em Python:
   fala com até 2 frases/360 caracteres, exatamente 4 opções de até 80 caracteres, sem repetição,
   intenções conhecidas e sem metalinguagem. O histórico da conversa é enviado para manter coerência.
6. Algumas intenções desbloqueiam **Fragmentos de Memória** (regra em Python); o texto de cada lembrança
   é escrito pelo LLM e pode ser lido na tela **Fragmentos** (F), com 12 espaços como no mockup.
7. No 5º turno, Darian dá a fala final e aparece **Ver desfecho**: quem Kael se tornou (atributo dominante),
   o destino de Darian e os fragmentos recuperados.

| Fragmento | Como desbloquear |
| --- | --- |
| A Batalha | Curiosidade ≥ 3 |
| O Medalhão | Lealdade ≥ 3 |
| Darian | Confiança de Darian ≥ 40 |
| Mãos Manchadas | Agressividade ≥ 2 |

**Desfecho:** o atributo mais alto define o título (Protetor, Companheiro, Buscador, Implacável ou
Sobrevivente; empate segue essa ordem). A intenção da última escolha e a confiança definem o destino de Darian.

### Roteiro offline e falhas da IA

O arquivo `data/roteiro_offline.json` tem uma conversa **ramificada**, escrita com o Claude Code e editável pelo grupo. Cada escolha
leva a um **caminho** conforme a intenção: empatia/lealdade → **Cuidado**, curiosidade → **Perguntas**,
agressividade → **Confronto**, egoísmo → **Abandono**. Em cada turno, a fala de Darian e as 4 opções
dependem do caminho da última escolha (ex.: “Ajudar o soldado” leva a curativos e confiança;
“Ir embora” leva a “Vai me deixar aqui para morrer, Kael?”). O roteiro também oferece
“Perguntar sobre o passado” e “Ameaçar Darian” com os efeitos da tabela da CP4.

- **Sem chave/modelo no `.env`:** o menu mostra “Modo: roteiro offline” e a partida inteira segue o roteiro,
  identificado como “roteiro offline” na caixa de diálogo. Nenhuma chamada de rede é feita.
- **Com a API configurada:** a IA gera falas e opções. Se uma geração falhar (sem internet, timeout,
  resposta inválida), aquele turno segue pelo roteiro, com o aviso “IA indisponível — roteiro offline”, e
  **Tentar IA de novo / R** faz uma nova solicitação sem reaplicar efeitos. Não há tentativas automáticas.
- Fragmentos sem IA usam o texto do roteiro, identificado como “Texto do roteiro (sem IA)”.

A cena acima da caixa de diálogo também pode mudar por caminho: basta colocar `cuidado.png`,
`perguntas.png`, `confronto.png` ou `abandono.png` em `assets/scenes/` (prompts sugeridos em
`assets/scenes/LEIA-ME.md`). Sem esses arquivos, usa-se a composição padrão.

## Arquitetura

```text
GameplayScreen → Encounter → choices.apply_choice (estado atualizado)
                         ↓ thread + fila de resultados
                  DialogueService
                         ↓
                    PromptBuilder
                         ↓
                    OpenAIClient → Responses API da OpenAI
                         ↓
                validação → fila → GameplayScreen
```

- `game/models/`: estado imutável de Kael e Darian. JSONs de `data/` são dados iniciais, não saves.
- `game/systems/choices.py`: opções fixas do turno 1, tabela intenção → efeitos e opções/falas de reserva.
- `game/systems/script.py` + `data/roteiro_offline.json`: roteiro ramificado por caminho (modo offline e falhas).
- `game/systems/fragments.py`: fragmentos de memória, condições de desbloqueio e textos de reserva.
- `game/systems/ending.py`: cálculo do desfecho a partir do estado.
- `game/systems/prompt_builder.py`: regras fixas e contexto JSON com os atributos já atualizados.
- `game/systems/openai_client.py`: único local que usa o SDK. Timeout de 25 segundos,
  `max_retries=0`, limite de 512 tokens de saída e `store=False`. Apenas `output_text` sai do adaptador.
- `game/systems/dialogue.py`: coordenação; `converse` valida o JSON do turno (fala + 4 opções); rejeição de respostas vazias,
  maiores que 360 caracteres, com mais de duas frases ou formatos/metalinguagem obviamente inválidos.
- `game/systems/encounter.py`: conduz os 5 turnos, aplica uma escolha por turno, decide os fragmentos
  desbloqueados, impede duplicação e coordena a thread (fala + textos de fragmentos na mesma tarefa).
  Somente o loop principal atualiza o estado e desenha; o worker devolve um resultado pela fila.
- `game/screens/`: menu, gameplay, fragmentos e desfecho.
- `game/app.py`: conecta o provedor ao serviço e navega entre telas. As telas não conhecem a OpenAI.

O conhecimento privado do NPC não é serializado integralmente. O prompt recebe apenas fatos
conhecidos **e explicitamente permitidos**, a política de revelação e temas proibidos.
Os temas de segredo não contêm fatos inéditos da história. `pode_revelar_passado` permanece `false`.
Nenhuma saída da IA é executada, convertida em atributos ou utilizada para liberar progressão.

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
pytest -q tests/test_state.py tests/test_choices.py tests/test_prompt_builder.py tests/test_cp5_mechanics.py
```

## Validação manual real

Depois de configurar a credencial e o modelo, execute o jogo e escolha **Ajudar o soldado**.
Observe Empatia **2**, Lealdade **1**, Confiança **30**, a mensagem de espera e, finalmente,
a fala gerada. Fechar a janela deve continuar possível durante a espera.
Uma escolha faz uma requisição para a fala de Darian e, se desbloquear fragmentos, uma por fragmento.
Uma partida completa faz de 5 a 9 requisições; uma nova tentativa explícita pode gerar nova cobrança.

Uma chamada real com **gpt-5.6-luna**, usando **Ajudar o soldado**, retornou HTTP 200.
Foi corrigida a contagem de frases quando a fala vem entre aspas externas; a mesma resposta
recebida foi validada e exibida na janela nativa, sem nova solicitação. O estado permaneceu
Empatia 2, Lealdade 1, Confiança 30. Evidências e limites estão no relatório.

## Limites desta entrega

Há um único encontro (Kael × Darian, 5 turnos). Dos 12 fragmentos, 4 existem no MVP; os demais
aparecem bloqueados. Lira, exploração livre, combate e save/load não foram implementados; as
memórias recuperadas ficam disponíveis apenas até fechar o jogo. As mudanças em relação à CP4
estão justificadas em `ENTREGA_CP5.md`, junto com o Diário de Vibe Coding e o checklist de testes.
O histórico da primeira entrega do MVP está em `RELATORIO_MVP.md`.
