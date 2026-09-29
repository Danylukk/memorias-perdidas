# Cenas por caminho

Coloque aqui uma imagem por caminho da história. O jogo troca a cena automaticamente quando o
arquivo existe; sem ele, usa a composição padrão (ruínas + Kael + Darian).

| Arquivo | Caminho | Quando aparece |
| --- | --- | --- |
| `cuidado.png` | Cuidado | Última escolha com intenção empatia ou lealdade |
| `perguntas.png` | Perguntas | Última escolha com intenção curiosidade |
| `confronto.png` | Confronto | Última escolha com intenção agressividade |
| `abandono.png` | Abandono | Última escolha com intenção egoísmo |

A área da cena tem 800 × 280 px. Imagens panorâmicas (21:9 ou 16:9) aparecem inteiras, com faixas
laterais se necessário. Siga a estratégia da CP4 (§2.1 e §6.2): gere no ChatGPT anexando as imagens
oficiais de Kael, Darian e do cenário das ruínas como referência, aprove a versão final e registre o
prompt usado no relatório.

## Prompts sugeridos (anexar kael.png, darian.png e bg_ruinas_principal.png)

Base comum para todos:

> Use the attached images as direct visual references for Kael, Darian and the ruined city background
> from the dark fantasy RPG “Memórias Perdidas”. Preserve their faces, outfits, colors and the detailed
> 16-bit pixel-art style exactly. Wide panoramic scene (21:9), dramatic lighting, burning ruins at night,
> limited dark color palette, no text.

- **cuidado.png** — `...Kael kneels beside the wounded soldier Darian, pressing a torn piece of his own cloak against Darian's bleeding leg; Darian looks at him with cautious surprise. Warm firelight between them.`
- **perguntas.png** — `...Kael crouches in front of Darian, holding the old medallion around his neck and looking at it with confusion, while Darian, still sitting wounded against the rubble, watches him with a guarded expression.`
- **confronto.png** — `...Kael stands over Darian with a clenched fist and his sword lowered but ready; Darian, wounded on the ground, grips a dagger defensively. Tense atmosphere, harsh red light.`
- **abandono.png** — `...Kael walks away into the smoke with his back turned, while Darian remains alone, wounded, sitting among the ruins and watching him leave. Cold, lonely lighting.`
