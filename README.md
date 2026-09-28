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
Não há modelo local. Sem a API, o jogo usa falas de reserva roteirizadas, sempre identificadas como tais.

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

1. **Novo Jogo** abre as ruínas com Kael e Darian. A frase inicial roteirizada é **“Você... está vivo?”**.
2. O encontro tem **3 rodadas** com 4 escolhas cada (mouse ou teclas 1–4). O Python aplica os efeitos
   imediatamente em atributos, vida, energia e confiança de Darian.
3. As opções ficam bloqueadas e aparece **“Darian está pensando...”**. A rede roda em uma thread separada.
4. A resposta validada aparece como **“Resposta narrativa — ChatGPT (LLM)”**. O histórico das falas
   anteriores é enviado à IA para manter coerência entre as rodadas.
5. Algumas escolhas desbloqueiam **Fragmentos de Memória** (regra em Python). O texto de cada lembrança
   é escrito pelo LLM e pode ser lido na tela **Fragmentos** (F), com 12 espaços como no mockup da CP4.
6. Após a 3ª rodada, **Ver desfecho** mostra quem Kael se tornou (atributo dominante), o destino de Darian
   e os fragmentos recuperados. Dali é possível iniciar um Novo Jogo, ver os Fragmentos ou voltar ao menu.

| Rodada | Escolha | Efeitos |
| --- | --- | --- |
| 1 | Quem é você? | Curiosidade +1 |
| 1 | Você me conhece? | Curiosidade +2 |
| 1 | Ajudar o soldado | Empatia +2, Lealdade +1, Confiança +10 |
| 1 | Ir embora | Egoísmo +2, Confiança −10 |
| 2 | Perguntar sobre o passado | Curiosidade +2 |
| 2 | Ameaçar Darian | Agressividade +2, Empatia −1, Vida −10, Confiança −15 |
| 2 | Estancar o ferimento | Empatia +1, Lealdade +1, Energia −15, Confiança +10 |
| 2 | Examinar o medalhão | Curiosidade +1 |
| 3 | Levar Darian ao abrigo | Lealdade +2, Empatia +1, Energia −25, Confiança +10 |
| 3 | Exigir a verdade | Agressividade +1, Curiosidade +1, Confiança −5 |
| 3 | Prometer voltar com ajuda | Lealdade +1, Confiança +5 |
| 3 | Partir sozinho | Egoísmo +2, Confiança −10 |

Valores ficam entre 0 e 100. Confiança inicial de Darian: 20.

| Fragmento | Como desbloquear |
| --- | --- |
| A Batalha | Perguntar sobre o passado ou Exigir a verdade |
| O Medalhão | Examinar o medalhão ou Curiosidade ≥ 4 |
| Darian | Confiança de Darian ≥ 40 |
| Mãos Manchadas | Agressividade ≥ 2 |

**Desfecho:** o atributo mais alto define o título (Protetor, Companheiro, Buscador, Implacável ou
Sobrevivente; empate segue essa ordem). A escolha final e a confiança definem o destino de Darian.

### Falhas da IA e fallback

Se a geração falhar (sem internet, sem chave, timeout, resposta inválida), o jogo **não trava**:
exibe uma **fala de reserva roteirizada**, sempre identificada em vermelho como
“fala de reserva (roteirizada) — IA indisponível”, e o jogador pode seguir para a próxima rodada.
**Tentar IA de novo / R** faz uma nova solicitação explícita para a mesma ação e o mesmo estado,
sem reaplicar efeitos. Fragmentos cuja geração falhar usam um texto de reserva, também identificado.
Não há tentativas automáticas. Nenhuma reserva é apresentada como gerada pela IA.

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
- `game/systems/choices.py`: as 12 escolhas (3 rodadas), seus efeitos e falas de reserva, sem Pygame.
- `game/systems/fragments.py`: fragmentos de memória, condições de desbloqueio e textos de reserva.
- `game/systems/ending.py`: cálculo do desfecho a partir do estado.
- `game/systems/prompt_builder.py`: regras fixas e contexto JSON com os atributos já atualizados.
- `game/systems/openai_client.py`: único local que usa o SDK. Timeout de 25 segundos,
  `max_retries=0`, limite de 512 tokens de saída e `store=False`. Apenas `output_text` sai do adaptador.
- `game/systems/dialogue.py`: coordenação, normalização e rejeição de respostas vazias,
  maiores que 360 caracteres, com mais de duas frases ou formatos/metalinguagem obviamente inválidos.
- `game/systems/encounter.py`: conduz as 3 rodadas, aplica uma escolha por rodada, decide os fragmentos
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
Uma partida completa faz de 3 a 7 requisições; uma nova tentativa explícita pode gerar nova cobrança.

Uma chamada real com **gpt-5.6-luna**, usando **Ajudar o soldado**, retornou HTTP 200.
Foi corrigida a contagem de frases quando a fala vem entre aspas externas; a mesma resposta
recebida foi validada e exibida na janela nativa, sem nova solicitação. O estado permaneceu
Empatia 2, Lealdade 1, Confiança 30. Evidências e limites estão no relatório.

## Limites desta entrega

Há um único encontro (Kael × Darian, 3 rodadas). Dos 12 fragmentos, 4 existem no MVP; os demais
aparecem bloqueados. Lira, exploração livre, combate e save/load não foram implementados; as
memórias recuperadas ficam disponíveis apenas até fechar o jogo. As mudanças em relação à CP4
estão justificadas em `ENTREGA_CP5.md`, junto com o Diário de Vibe Coding e o checklist de testes.
O histórico da primeira entrega do MVP está em `RELATORIO_MVP.md`.
