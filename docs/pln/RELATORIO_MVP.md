# Relatório — Memórias Perdidas / MVP

## Estado atual — integração de assets e validação real

Esta seção registra a continuação do MVP. As seções numeradas abaixo são o histórico
da primeira entrega e descrevem as condições daquela etapa, não as pendências atuais.

### Assets integrados e arquivos alterados

O README de `memorias_perdidas_pacote_completo/` foi lido. Foram inspecionados os assets
de Kael, Darian, ruínas, logo, botão, caixa de diálogo, menu pronto e mockup de gameplay.
Foram adicionadas seis cópias exatas, verificadas por SHA-256 contra os arquivos do pacote:

```text
assets/characters/kael.png
assets/characters/darian.png
assets/backgrounds/bg_ruinas_principal.png
assets/ui/logo_memorias_perdidas.png
assets/ui/botao_menu_base.png
assets/ui/caixa_dialogo_base.png
```

Os placeholders geométricos dos personagens e do cenário foram substituídos. O menu usa
o cenário, Kael, o logo e os botões oficiais separados. `menu_principal.png` foi usado
como referência: sua composição inclui Continuar, Fragmentos e Configurações, que não
foram introduzidos nesta etapa. Nenhum outro NPC foi integrado e nenhuma imagem foi gerada.

Personagens, logo e cenário são exibidos inteiros, com escala uniforme. As faixas de
preenchimento preservam a proporção do cenário. Para botões/diálogo, apenas as faixas
de textura são adaptadas horizontalmente, mantendo cantos e ornamento central proporcionais.
As margens transparentes com ruído quase invisível de alpha são desconsideradas somente
na renderização das molduras; os arquivos originais permanecem idênticos.

Arquivos existentes alterados nesta etapa:

```text
game/screens/ui.py
game/screens/menu.py
game/screens/gameplay.py
game/systems/dialogue.py
README.md
RELATORIO_MVP.md
```

Novo teste: `tests/test_dialogue_quotes.py`. Os arquivos dos 44 testes existentes foram
preservados, verificados contra seus hashes antes da alteração. Modelos, escolhas, efeitos,
PromptBuilder, OpenAIClient e coordenação do encontro não foram modificados.

### Única chamada real

- Modelo configurado, solicitado e retornado: **gpt-5.6-luna**.
- Ação enviada pela tela de gameplay: **Ajudar o soldado**.
- Requisições HTTP à API: **1**; retorno **HTTP 200**, status **completed**.
- Tempo observado entre escolha e resultado: **5,734 segundos**.
- Interface nativa: driver SDL **windows**, com **288 frames** durante a espera.
- Estado após a escolha e no contexto enviado: **Empatia 2, Lealdade 1, Confiança 30**.
- O estado completo permaneceu igual após a geração; passado bloqueado e fragmentos em zero.
- O `.env` configurado pelo responsável foi utilizado sem editar, mostrar ou registrar a chave.

Resposta recebida, com aspas externas fornecidas pelo modelo:

> “Pare… não sei se devo confiar em você, Kael. Mas se realmente veio me ajudar, estanque o sangue e não faça movimentos bruscos.”

A resposta está em português e contém duas frases, reconhece a oferta de ajuda e o ferimento,
mantém a desconfiança de Darian, não cria personagens/cidades/facções, não revela o passado
e não menciona IA/modelo/prompt. A comparação do estado antes e depois confirmou que a geração
não alterou nenhuma regra ou atributo.

Foi encontrado um problema no guardrail: a aspa final isolada após o ponto era contada
como uma terceira frase, causando uma falha controlada na primeira exibição. O único ajuste
foi normalizar pares de aspas externas antes da validação. Não houve mudança de prompt nem
afrouxamento do limite de duas frases. Foi adicionado um teste de regressão com esse retorno.

**Não foi feita outra chamada.** O texto exato da única resposta real foi reapresentado
ao DialogueService, com o mesmo contexto, validado e exibido na janela nativa. Apenas as
aspas externas foram removidas. Esse procedimento não constitui uma segunda geração nem
uma resposta fictícia. O primeiro resultado com erro e a verificação corrigida foram preservados
em arquivos separados para manter a evidência fiel.

### Interface verificada

As superfícies da janela nativa foram salvas e inspecionadas: menu, abertura Kael × Darian,
espera na chamada real e resposta real após a normalização. Foram conferidos os personagens
inteiros, proporção do cenário, HUD, quatro escolhas, atributos 2/1/30, caixa de diálogo,
“Darian está pensando...” e “Resposta narrativa — ChatGPT (LLM)”.

Os eventos de mouse foram enviados programaticamente à aplicação; não se trata de uma
sessão manual de cliques físicos. O teste utilizou a janela nativa Windows, além dos testes
automatizados que continuam usando SDL dummy. A suíte verifica também redimensionamento.

Evidências locais, ignoradas pelo Git, em `artifacts/etapa-assets-api/`:

```text
assets-verificados.json
baseline.json
chamada-real.json
validacao-resposta-real.json
menu-oficial.png
gameplay-oficial-inicial.png
gameplay-api-pensando.png
gameplay-api-resultado.png
gameplay-resposta-real-validada.png
compileall.log
pytest.log
validar_uma_chamada.py
```

O script de validação pontual bloqueia solicitações adicionais e recusa executar novamente
se o registro da chamada já existir. Os registros contêm somente contexto do jogo, texto
recebido e metadados selecionados; não incluem credenciais ou cabeçalhos de autenticação.

### Validação final desta etapa

Executados nesta ordem no ambiente Python 3.12.14:

| Comando | Resultado comprovado |
| --- | --- |
| `python -m compileall .` | Código 0, sem erro de compilação |
| `pytest -q` | **45 aprovados, 0 falhas**, em 1,55 s; código 0 |

Os 45 testes correspondem aos **44 testes existentes + 1 regressão de aspas externas**.
A suíte não acessa a API; a chamada real foi feita separadamente e uma única vez.

### Limitações restantes

- Foi avaliada uma resposta real; isso não garante a qualidade de todas as futuras gerações.
- Após a correção das aspas, foi usada a resposta real já recebida; não houve uma nova
  execução de rede com o guardrail corrigido, para manter o total de uma chamada.
- A inspeção visual foi feita nas superfícies renderizadas da janela Windows; outros
  sistemas operacionais não foram executados.
- O jogo permanece limitado ao primeiro encontro, sem novos NPCs, cenas, fragmentos,
  combate, inventário, quests ou save/load.

---

## Histórico — primeira entrega do MVP

## 1. Estado inicial encontrado

A pasta `D:\THIAGO\FIAP\PLN\memorias-perdidas` estava vazia, incluindo arquivos ocultos.
Não havia `.git`, `AGENTS.md` aplicável, código, estrutura, assets, mockups, testes,
dependências, `.gitignore` ou integração de IA. A auditoria foi concluída antes de criar arquivos.
O Python global era 3.14.7. Foi criado um `.venv` com Python 3.12.14 disponível no ambiente.
Não foi inicializado um repositório Git na raiz, nem efetuado commit ou publicação.

## 2. Arquivos criados

Lista exata dos **34 arquivos do projeto**, incluindo documentação:

```text
.env.example
.gitignore
README.md
RELATORIO_MVP.md
main.py
pytest.ini
requirements.txt
data/characters.json
data/game_state.json
game/__init__.py
game/app.py
game/config.py
game/models/__init__.py
game/models/npc.py
game/models/player.py
game/models/state.py
game/screens/__init__.py
game/screens/gameplay.py
game/screens/menu.py
game/screens/ui.py
game/systems/__init__.py
game/systems/choices.py
game/systems/dialogue.py
game/systems/encounter.py
game/systems/openai_client.py
game/systems/prompt_builder.py
tests/conftest.py
tests/test_choices.py
tests/test_dialogue.py
tests/test_encounter.py
tests/test_gameplay.py
tests/test_openai_client.py
tests/test_prompt_builder.py
tests/test_state.py
```

Arquivos locais ignorados pelo Git: `.env` com os dois campos vazios; ambiente instalado `.venv/`;
caches do Python/pytest; e os seguintes registros de validação:

```text
artifacts/menu.png
artifacts/gameplay-inicial.png
artifacts/gameplay-pensando-mock.png
artifacts/gameplay-resposta-mock.png
artifacts/gameplay-sem-credencial.png
artifacts/compileall.log
artifacts/pytest.log
```

`artifacts/gitignore-check/` contém apenas o repositório local descartável usado para testar
as regras de exclusão, com uma cópia do `.gitignore` e os arquivos administrativos gerados pelo Git.
Ele também está dentro de `artifacts/`, que é ignorado. Nenhuma credencial foi colocada nele.

## 3. Arquivos existentes modificados

Nenhum: não existiam arquivos antes da implementação. Os ajustes durante o desenvolvimento
foram feitos somente nos arquivos novos listados acima.

## 4. Arquitetura implementada

```text
GameplayScreen
  → Encounter → sistema de escolhas → novo estado Python
  → worker → DialogueService → PromptBuilder → OpenAIClient → API
  ← loop principal ← fila ← resultado validado ou falha controlada
```

O ponto de composição é `game/app.py`. As telas não importam o cliente OpenAI.
O estado usa dataclasses imutáveis, os dados iniciais vêm de JSON e os efeitos ficam
centralizados em `choices.py`. O cliente recebe exclusivamente instruções e contexto textual;
a resposta nunca é executada nem aplicada ao estado.

## 5. Fluxo implementado

Menu com Novo Jogo/Sair → ruínas → Kael e Darian → abertura roteirizada
“Você... está vivo?” → quatro escolhas → efeitos imediatos → “Darian está pensando...”
→ geração em thread → validação → diálogo ou mensagem de erro.

Há Vida, Energia, Fragmentos, atributos, confiança e identificação de Darian.
As gerações são identificadas como “Resposta narrativa — ChatGPT (LLM)”.
A abertura é explicitamente identificada como roteirizada; falhas não são apresentadas como falas.

Uma escolha encerra este encontro após a resposta. O menu permite começar novamente e resetar o estado.
Durante a geração, escolhas, atalhos e retorno ao menu ficam bloqueados; a janela continua desenhando
e pode ser fechada. Em caso de falha, R ou Tentar novamente reenvia a mesma ação, sem reaplicar efeitos.

## 6. Efeitos das escolhas

| Escolha | Alterações exatas |
| --- | --- |
| Quem é você? | Curiosidade +1 |
| Você me conhece? | Curiosidade +2 |
| Ajudar o soldado | Empatia +2; Lealdade +1; Confiança +10 |
| Ir embora | Egoísmo +2; Confiança −10 |

Todos os demais campos permanecem iguais. Darian começa com confiança 20 e
`pode_revelar_passado=false`; Kael começa com Vida/Energia 100 e demais valores 0.

## 7. Integração com IA

Isolada em `game/systems/openai_client.py`, usando o SDK oficial e a Responses API.
Configuração por `OPENAI_API_KEY` e `OPENAI_MODEL`; ambas são validadas antes de construir
o cliente. Timeout de 25 segundos, sem retries automáticos, uma chamada por solicitação,
512 tokens de saída como limite e sem armazenamento solicitado da resposta (`store=False`).

O PromptBuilder recebe o estado atualizado, ação, situação, personalidade e fatos autorizados.
Ele omite conhecimentos privados não liberados e inclui a política de revelação e os tópicos
bloqueados. O serviço normaliza espaços e rejeita texto vazio, excesso de tamanho/frases,
metalinguagem e formatos obviamente inválidos. Exceções não expõem detalhes privados.

**Não houve chamada real à API. Integração implementada e coberta por mocks, mas chamada real
pendente por ausência de credencial configurada.** Não havia modelo configurado tampouco.

Referências consultadas: [Responses API](https://developers.openai.com/api/reference/python/resources/responses/methods/create)
e [SDK Python](https://developers.openai.com/api/reference/python).

## 8. Segurança

Nenhuma chave real ou fictícia foi adicionada ao código, testes, README, JSON ou exemplo.
O `.env` criado contém valores vazios. A representação de Settings omite o campo da chave;
logs e mensagens não incluem corpos de erro do provedor ou conteúdo da credencial.

As regras do `.gitignore` foram verificadas com `git check-ignore --no-index` em um
repositório local descartável: `.env` e `.env.local` foram ignorados; `.env.example`, não.
A raiz ainda não é um repositório Git. Nenhum arquivo foi enviado a um remoto.

## 9. Testes

Execução final em Python 3.12.14, com pygame 2.6.1, openai 2.54.0,
python-dotenv 1.2.3 e pytest 9.1.1:

| Comando | Executados | Aprovados | Falhas |
| --- | ---: | ---: | ---: |
| `pytest -q` | 44 | 44 | 0 |
| `pytest -q tests/test_state.py tests/test_choices.py tests/test_prompt_builder.py` | 9 | 9 | 0 |

A execução final completa terminou em 1,22 s, com código 0. O segundo comando é um
subconjunto da suíte, executado separadamente; os números não devem ser somados.

Cobertura funcional: estados iniciais, quatro efeitos exatos, contexto atualizado, omissão de
conhecimento privado, uma chamada ao adaptador, timeout, autenticação, erro HTTP/SDK,
ausência de configuração, resposta incompleta/vazia/inválida, duplicação de cliques,
falha do worker, retry sem duplicar efeitos, reset, renderização e saída durante geração.

Uma fixture bloqueia conexões de rede nos testes. Não foram consumidos créditos de API.
`python -m pip check` retornou **No broken requirements found**.

## 10. Compileall

`python -m compileall .` foi executado antes da suíte final e terminou com **código 0**.
O comando incluiu o projeto e o ambiente local `.venv`, sem erros de compilação.
O registro está em `artifacts/compileall.log`.

## 11. Teste manual e inspeção visual

Foram renderizadas e inspecionadas cinco imagens: menu, abertura, espera, resposta simulada
e falha real por configuração ausente. As imagens de espera/resposta com mock estão explicitamente
marcadas **TESTE COM MOCK / SEM CHAMADA REAL**. Foi conferida a exibição de Empatia 2,
Lealdade 1 e Confiança 30 após ajudar Darian, bem como a mensagem de erro e o botão de retry.

O ponto de entrada `main.py` também foi executado via `runpy` com SDL dummy;
o loop iniciou e encerrou normalmente após um evento QUIT. Os testes exercitaram eventos
de mouse, teclado, redimensionamento e fechamento, usando o SDL dummy.

Não houve sessão manual interativa numa janela nativa nem teste de fala com a API real.
A inspeção visual das superfícies e os testes de eventos não são apresentados como substitutos
dessa validação final. O procedimento para realizá-la está no README.

## 12. Limitações reais

- Sem credencial/modelo configurados, a validação real do provedor e da qualidade das falas permanece pendente.
- Assets e mockups oficiais ausentes: cenário e personagens são representações geométricas provisórias.
- Guardrails textuais e prompts não garantem impedir toda invenção narrativa; o estado Python permanece protegido.
- Um único encontro, sem persistência, combate, outras cenas ou desbloqueio de fragmentos, conforme o escopo.
- A execução foi validada em Windows/Python 3.12.14; outros sistemas/versões não foram executados.

## 13. Como executar

Na pasta do projeto, aproveitando o ambiente já preparado:

```powershell
.\.venv\Scripts\Activate.ps1
python main.py
```

Ou diretamente:

```powershell
.\.venv\Scripts\python.exe main.py
```

Preencha os dois campos do `.env` local antes de esperar uma resposta real e reinicie o jogo.
Sem eles, o jogo abre normalmente e apresenta uma falha controlada ao solicitar a geração.
Para conferir novamente:

```powershell
python -m compileall .
pytest -q
```

A implementação foi encerrada no primeiro encontro; não foram adicionados NPCs, combate,
save/load ou progressão além do pedido.
