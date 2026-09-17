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
Não há modelo local nem resposta narrativa de emergência simulando uma geração real.

## Executar

Com o ambiente ativado:

```powershell
python main.py
```

Sem ativação:

```powershell
.\.venv\Scripts\python.exe main.py
```

O menu tem **Novo Jogo** e **Sair**. Enter inicia; Esc sai do menu ou volta a ele durante
o gameplay quando não há geração pendente. O botão de fechar a janela funciona durante a geração.
A janela pode ser redimensionada; o conteúdo mantém sua proporção.

## Fluxo demonstrável

1. Novo Jogo abre as ruínas com Kael e Darian. A frase inicial roteirizada é **“Você... está vivo?”**.
2. Escolha com o mouse ou teclas 1–4. O Python aplica os efeitos imediatamente.
3. As opções ficam bloqueadas e aparece **“Darian está pensando...”**. A rede roda em uma thread separada.
4. A resposta validada aparece como **“Resposta narrativa — ChatGPT (LLM)”**.
5. O encontro do MVP termina. Volte ao menu e inicie outro jogo para explorar outra escolha.

| Escolha | Efeito em Kael | Confiança de Darian |
| --- | --- | --- |
| Quem é você? | Curiosidade +1 | permanece 20 |
| Você me conhece? | Curiosidade +2 | permanece 20 |
| Ajudar o soldado | Empatia +2, Lealdade +1 | 20 → 30 |
| Ir embora | Egoísmo +2 | 20 → 10 |

Se a geração falhar, a caixa exibe explicitamente uma falha, sem fala inventada.
Os efeitos da escolha permanecem. **Tentar novamente / R** faz uma nova solicitação explícita
para a mesma ação e o mesmo estado, sem reaplicar efeitos. Não há tentativas automáticas.

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
- `game/systems/choices.py`: quatro escolhas e seus efeitos, sem Pygame.
- `game/systems/prompt_builder.py`: regras fixas e contexto JSON com os atributos já atualizados.
- `game/systems/openai_client.py`: único local que usa o SDK. Timeout de 25 segundos,
  `max_retries=0`, limite de 512 tokens de saída e `store=False`. Apenas `output_text` sai do adaptador.
- `game/systems/dialogue.py`: coordenação, normalização e rejeição de respostas vazias,
  maiores que 360 caracteres, com mais de duas frases ou formatos/metalinguagem obviamente inválidos.
- `game/systems/encounter.py`: aplica uma escolha por encontro, impede duplicação e coordena a thread.
  Somente o loop principal atualiza o estado e desenha; o worker devolve um resultado pela fila.
- `game/app.py`: conecta o provedor ao serviço. As telas não conhecem a OpenAI.

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
pytest -q tests/test_state.py tests/test_choices.py tests/test_prompt_builder.py
```

## Validação manual real

Depois de configurar a credencial e o modelo, execute o jogo e escolha **Ajudar o soldado**.
Observe Empatia **2**, Lealdade **1**, Confiança **30**, a mensagem de espera e, finalmente,
a fala gerada. Fechar a janela deve continuar possível durante a espera.
Uma escolha faz no máximo uma requisição; uma nova tentativa explícita pode gerar uma nova cobrança.

Uma chamada real com **gpt-5.6-luna**, usando **Ajudar o soldado**, retornou HTTP 200.
Foi corrigida a contagem de frases quando a fala vem entre aspas externas; a mesma resposta
recebida foi validada e exibida na janela nativa, sem nova solicitação. O estado permaneceu
Empatia 2, Lealdade 1, Confiança 30. Evidências e limites estão no relatório.

## Limites desta entrega

Os assets oficiais do pacote `memorias_perdidas_pacote_completo/` foram integrados:
Kael, Darian, cenário das ruínas, logo, base de botão e caixa de diálogo. As cópias em
`assets/characters/`, `assets/backgrounds/` e `assets/ui/` preservam os PNGs originais.
Personagens, logo e cenário usam escala proporcional, sem recorte; as faixas de preenchimento
mantêm a imagem inteira. As molduras da UI adaptam as faixas de textura conservando os ornamentos.
O menu foi montado com os elementos separados: o menu pronto do pacote inclui opções fora do MVP.
Nenhuma imagem nova foi gerada. Os assets oficiais foram produzidos previamente com ChatGPT.

Só há o primeiro encontro. Não há persistência, combate, novos NPCs ou desbloqueio de fragmentos.
O indicador 0/12 representa o conceito; os 12 fragmentos não foram implementados.
O relatório da entrega está em `RELATORIO_MVP.md`.
