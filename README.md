# Robôs de conferência e correção de preços com Selenium

Reconstrução sanitizada da arquitetura de robôs de e-commerce: conferência de preços normais, leitura de grades XG por cor/tamanho, cruzamento com estoque e correção seletiva em sete etapas.

O problema operacional é identificar divergências entre os preços esperados e o painel, analisar grades e estoque e corrigir seletivamente.

**Este repositório não é o código de produção.** Não integra um painel comercial. Dados, produtos, interface, HTML, CSS e seletores foram criados do zero. A fidelidade pretendida é de fluxo e comportamento, não de aparência ou implementação interna.

## Contexto real

Registros de execuções reais fornecidos pelo usuário, usados somente como contexto:

| Rotina observada | Registro fornecido |
| --- | --- |
| Conferência normal | 245 referências: 143 iguais, 101 divergentes e 1 erro de leitura em uma execução |
| Conferência XG | 244 referências; um recorte apresentou 48 grades corretas e 20 divergentes |
| Correção XG | Rotina percorrendo 192 grades em um fluxo |
| Divergências × estoque | 20 divergências: 2 com divergência ativa e 18 somente sem estoque em uma execução mostrada |

Os números não são resultados desta demo, garantia geral, taxa de sucesso, nem prova de que todas as referências foram corrigidas. Os recortes não devem ser somados como uma única execução. Nenhuma tela, referência comercial ou dado interno acompanha o projeto.

## Fluxos reconstruídos

**A — Conferência normal:** abrir Gerenciar Produtos → Preços → pesquisar cada referência → ler quatro campos → comparar com CSV esperado → emitir OK, DIVERGENTE ou ERRO_LEITURA. O CSV preserva os valores observados e esperados por campo, inclusive o texto ilegível, com estado de leitura LIDO, VAZIO, ILEGIVEL ou NAO_LIDO. Uma falha de interpretação mantém os outros valores e marca a referência como ERRO_LEITURA; uma falha anterior à leitura não reaproveita valores da referência anterior.

**B — Conferência XG:** pesquisar referência, alternar entre atacado e varejo, ler a matriz cor × tamanho e registrar cada lado separadamente. Cada lado recebe OK, DIVERGENTE, SEM_VALORES ou ERRO_LEITURA e a lista de células divergentes. Um lado vazio não é tratado como correto.

**C — Estoque:** cruzar somente as células divergentes com o estoque da mesma cor/tamanho. Estoque em outra variante não torna aquela divergência ativa. A mesma célula divergente nos dois lados é contada uma vez. Relatório distingue DIVERGENCIA_ATIVA, DIVERGENTE_SEM_ESTOQUE e ERRO_LEITURA; isso não concede autorização de escrita.

**D — Corretor XG:** somente as referências explicitamente listadas em `fixtures/approved.json`. As sete etapas são:

1. Abrir Gerenciar Produtos.
2. Selecionar Preços.
3. Pesquisar e selecionar a referência.
4. Validar os quatro campos de preço contra a fixture esperada.
5. Abrir Alterar Preços em Lote.
6. Conferir seleção única e preparar valores absolutos esperados.
7. Salvar, reabrir e validar a persistência.

**E/F — Retomada e proteção:** intenção durável antes da escrita, releitura após salvar, estado local persistente entre processos e identificação única da operação. Incerteza de referência, seleção, grade, preço, revisão ou confirmação interrompe o corretor inteiro. Não há tentativa de clicar novamente às cegas.

## Arquitetura

```text
src/price_demo/
├── checkers/
│   ├── regular_prices.py
│   ├── xg_prices.py
│   └── stock.py
├── correctors/xg_corrector.py
├── domain/
│   ├── prices.py
│   └── fixtures.py
├── browser/
│   ├── product_page.py
│   └── local_admin.py
├── reports/
│   ├── csv_report.py
│   └── journal.py
└── cli.py
fixtures/
├── admin.html / admin.css / admin.js
├── expected.csv
├── scenarios.json
└── approved.json
tests/
```

Selenium controla a interface por DOM. A aplicação fictícia usa HTTP exclusivamente em loopback e salva seu estado em JSON por substituição atômica. O robô lê campos e grades da tela, não a API de dados. A API serve apenas ao próprio painel fictício. SQLite registra intenções e confirmações; os relatórios CSV são snapshots substituídos atomicamente.

## Escolhas da reconstrução

- Quatro campos conceituais: atacado de/por e varejo de/por. Os nomes são novos; não afirmam o mapeamento exato de campos internos.
- Duas cores inventadas e dois tamanhos fictícios T1/T2.
- A fixture esperada contém 245 referências DEMO-001 a DEMO-245. Cada referência tem quatro preços distintos dos de outras referências, gerados deterministicamente em centavos: para o índice i de 1 a 245, 4200+17i, 3600+13i, 7400+23i e 6800+19i. XG tem dois lados por referência: 490 linhas de conferência.
- O preço XG esperado de cada lado vem do campo “por” da fixture, aplicado às quatro células. Essa simplificação é da demo, não uma afirmação sobre regras comerciais reais.
- Lote aplica valores absolutos esperados, sem reproduzir um mecanismo interno ou fórmula percentual do painel observado.
- Comparação monetária exata com Decimal; sem tolerância oculta.
- Célula parcialmente vazia é divergente; lado inteiro vazio é SEM_VALORES e bloqueia correção. Estrutura ausente, duplicada ou inválida é ERRO_LEITURA.
- Estoque é compartilhado pelos dois lados. A aprovação é uma lista separada, revisável manualmente.

## Executar localmente

Python 3.11+ e Google Chrome. A execução é a partir de um checkout do repositório; distribuição por wheel não foi preparada.

```bash
python -m venv .venv
# Ative o ambiente virtual conforme seu sistema operacional.
python -m pip install -e ".[test]"

# Conferência completa e simulação de correção; sem salvar preços:
price-demo all

# Execuções individuais:
price-demo regular
price-demo xg
price-demo stock
price-demo correct

# Salva apenas as correções fictícias explicitamente aprovadas:
price-demo correct --apply

# Repete, usando o mesmo estado: não salva novamente:
price-demo correct --apply

# Ensaio curto, com estado independente:
price-demo all --limit 12 --output reports/ensaio
```

`--apply` é a autorização de escrita **na demo local**, nunca em produção. O programa não aceita URL externa nem credenciais. Chrome funciona sem janela; Selenium Manager pode precisar de rede para localizar/baixar um driver compatível. Os dados do painel não saem da máquina.

Grave saídas em `reports/` (ignorado na raiz do repositório) ou em outro caminho explicitamente ignorado. Um `--output` arbitrário não fica automaticamente fora do Git; confira com `git check-ignore` e `git status` antes de adicionar arquivos.

Para começar outro ensaio, use outro diretório `--output` sob `reports/`. Para retomar, mantenha o mesmo diretório, com `state.json` e `audit.sqlite` juntos. Não apague o diário isoladamente para contornar um bloqueio. A diversificação das fixtures altera os alvos: estados de ensaios da versão anterior não são migrados automaticamente. Preserve esses ensaios e inicie a nova fixture em outro diretório sob `reports/`.

## Saída sintética

Trechos ilustrativos (não uma transcrição dos robôs originais):

```text
[12/245] Conferindo DEMO-012
OK
[2/245] Conferindo XG DEMO-002
atacado: DIVERGENTE; 1 divergentes
varejo: OK; 0 divergentes
[4/245] Conferindo XG DEMO-004
atacado: SEM_VALORES; 0 divergentes
varejo: SEM_VALORES; 0 divergentes
[1/2] Corrigindo grade DEMO-002
Etapa 1/7: abrindo Gerenciar Produtos
Etapa 2/7: selecionando Precos
Etapa 3/7: pesquisando e selecionando a referencia
Etapa 4/7: validando os quatro campos de preco
Etapa 5/7: abrindo Alterar Precos em Lote
Etapa 6/7: conferindo selecao e preparando
Etapa 7/7: salvando
OK
```

No estado inicial **sintético**, conferência normal: 243 OK, 1 DIVERGENTE e 1 ERRO_LEITURA. XG: 482 lados OK, 5 DIVERGENTE, 2 SEM_VALORES e 1 ERRO_LEITURA. As cinco divergências pertencem a quatro referências: três têm célula divergente com estoque e uma somente sem estoque. Apenas DEMO-002 e DEMO-007 estão aprovadas; a aprovação não abrange toda divergência ativa.

## Relatórios e retomada

- `regular.csv`: uma linha por referência e os quatro pares observado/esperado, com estado de leitura por campo.
- `xg.csv`: uma linha por referência/lado; células e contagem de divergências.
- `stock.csv`: uma linha por referência divergente e contagens de variantes.
- `simulation.csv` / `corrections.csv`: resultados da última execução concluída daquela modalidade.
- `audit.sqlite`: uma operação por referência + alvo; estados pending/verified.
- `state.json`: catálogo persistente da aplicação fictícia.

Relatórios não são anexados repetidamente. Se houver interrupção, um CSV anterior pode permanecer; o diário é a fonte de retomada do corretor. Conferências reiniciam a leitura e substituem o snapshot somente ao concluir. Não há checkpoint por linha de conferência.

Uma interrupção depois de salvar e antes de confirmar no diário é reconciliada por releitura. Se o estado coincidir com a intenção e a revisão esperada, a operação é confirmada sem novo save. Alterações inesperadas exigem revisão manual. Uma operação pending para a mesma referência bloqueia automaticamente outro alvo, inclusive em simulação e quando o painel já coincide com o novo alvo. Para retomar, restaure o alvo original e reconcilie a intenção; para um novo ensaio após revisão, preserve o par estado/diário anterior e use outro diretório sob `reports/`. Não há comando para descartar uma intenção pendente. Há bloqueio de execução concorrente por diretório de saída.

## O que mudou da primeira versão

Foram removidos o motor genérico de margem/custo, os limites de 25% de variação e 10% de margem, a tolerância monetária e a estimativa de exposição financeira como decisão de correção. Também saíram o catálogo de ofertas isoladas, os identificadores antigos e a persistência limitada à sessão do navegador.

Foram preservados o nome do projeto, histórico Git, licença MIT, configuração Python, Selenium, pytest e a estrutura de CI. Os testes do modelo anterior foram substituídos por testes dos novos robôs.

## Testes e limites

```bash
python -m pytest -q
python -m pytest -m "not browser" -q
python -m pytest -m browser -q
git diff --check
```

A integração usa Chrome real, sem substituir WebDriver por fake. As falhas artificiais de DOM são injetadas somente nos testes. A CI mantém uma matriz de Python e uma etapa separada com Chrome; ausência de Chrome é falha, não teste silenciosamente ignorado.

Validação local em 2026-09-02: **97 testes aprovados — 82 unitários e 15 com Chrome real**, incluindo as 245 referências, retomada e idempotência. CI remota ainda não executada; sem push.

Veja [validação](docs/validation.md), [decisões de projeto](docs/design.md) e [segurança](docs/security.md). Esta demo não testa autenticação, painel real, latência comercial, concorrência externa ou recuperação de queda de energia. Não representa prontidão para produção.

Licença MIT.
