# Validação da reconstrução

## Escopo

Testes unitários para preços, estados de leitura, matriz XG, estoque por variante, aprovação, diário e relatórios; testes de integração com Chrome real contra o painel HTTP local.

A suíte antiga foi substituída: sua contagem não é somada à nova.

## Casos cobertos

- 245 referências sintéticas na conferência normal, com preços distintos por campo entre referências.
- Troca de preços entre referências detectada nas conferências normal e XG.
- Evidência preservada quando cada um dos quatro campos é ilegível; CSV mantém o escape de fórmula.
- Falha de leitura não reutiliza valores da referência anterior.
- 245 referências e dois lados XG: 490 linhas.
- Matriz parcial, vazia, inválida, com célula duplicada ou ausente.
- Estoque na variante divergente, estoque somente em outra variante e estoque desconhecido.
- Simulação sem escrita, correção de duas referências aprovadas, preservação das demais.
- Nova execução sem save duplicado.
- Reinício do navegador e do servidor com mesmo estado persistente.
- Interrupção antes/depois do save; reconciliação de intenção pendente.
- Interrupção após save real via Chrome, tentativa de alvo diferente bloqueada e retomada do alvo original sem novo save.
- Diário reaberto após interrupção antes/depois do save: alvo diferente bloqueado em simulação e aplicação, inclusive se coincidir com o painel; nenhuma operação paralela criada.
- Seleção vazia, múltipla, identidade incorreta, alvo adulterado e botão indisponível.
- Estado obsoleto recusado pelo servidor e erro na releitura pós-escrita.
- Relatórios sem append duplicado, escape de fórmula e bloqueio concorrente.

## Não executado / fora de escopo

A CI remota só pode ser confirmada após futura publicação autorizada. Painel comercial, autenticação, contas reais, importação de planilha interna, transações concorrentes externas e queda de energia não foram testados. A simulação de interrupção injeta exceções em pontos definidos; não equivale a todos os cenários possíveis de encerramento abrupto.

## Resultado local da lapidação

Validação em 2026-09-02: **97 testes aprovados, nenhum ignorado** — 82 unitários e 15 de integração com Chrome real. Rodada completa: 363.52 segundos. Houve um aviso não impeditivo ao gravar o cache do pytest (PytestCacheWarning); nenhum teste falhou. Código carregado da árvore atual via PYTHONPATH, reaproveitando o ambiente Python 3.14.7, Selenium 4.47.0 e pytest 8.4.2.

A primeira tentativa encontrou bloqueio de rede do Selenium Manager antes de iniciar Chrome (82 testes passaram, 15 falharam na preparação). A rodada completa foi repetida com acesso autorizado ao navegador e diretório temporário exclusivo; nenhum teste foi desativado.

A CLI regular com seis referências também foi executada no Chrome real: DEMO-006 preservou 43.02, 75.38 e 69.14 como LIDO, além de manter o texto ilegivel e marcar somente wholesale_sale como ILEGIVEL. A referência permaneceu ERRO_LEITURA. O CSV inclui as novas colunas de estado de leitura.

git diff --check e git diff --cached --check sem problemas. git check-ignore confirmou reports/regular.csv e reports/ensaio/state.json; um caminho arbitrário de saída não foi ignorado. Saídas do ensaio ficaram em reports/. A revisão do diff manteve apenas conteúdo sintético, sem dados reais novos, credenciais ou caminhos pessoais.

Arquitetura e histórico anterior preservados. Sem push; CI remota e matriz Linux continuam pendentes. A fixture diversificada requer novo ensaio para estados gerados na versão anterior, sem migração automática nem exclusão isolada do diário.

## Resultado anterior à lapidação

Validação em 2026-09-02: **83 testes aprovados, nenhum ignorado** — 68 unitários e 15 de integração com Chrome real. Rodada final completa: 486,71 segundos.

Ambiente: Windows, Python 3.14.7, Selenium 4.47.0, pytest 8.4.2 e Chrome 152.0.7977.65. As dependências existentes foram reaproveitadas; o código testado foi carregado da nova árvore src. Uma rodada anterior de 80 testes também passou; três verificações adicionais foram incluídas antes da rodada final.

A inicialização encontrou restrições de rede do gerenciador de driver e permissões do diretório temporário padrão. A execução foi repetida com acesso autorizado ao Chrome e diretório temporário exclusivo. Nenhum teste foi desabilitado para obter aprovação.

Os comandos da CLI foram exercitados por python -m price_demo.cli: all com 12 referências em simulação, correct --apply e uma segunda execução de correct --apply no mesmo diretório. Resultado: duas correções na primeira aplicação; ambas JA_CORRETO na segunda. As revisões persistidas de DEMO-002 e DEMO-007 permaneceram em 1, confirmando ausência de novos saves.

O ensaio gerou 12 linhas normais, 24 linhas XG, quatro referências no cruzamento de estoque e duas linhas de correção, além do diário persistente. Relatórios de execução permanecem locais e ignorados pelo Git.

git diff --check e git diff --cached --check: sem problemas. A revisão de conteúdo e histórico não encontrou termos privados, caminhos pessoais, referências comerciais, credenciais ou anexos indevidos. O histórico anterior contém apenas links públicos de documentação técnica; o código novo utiliza somente a origem HTTP local.

CI preservada, mas não executada no GitHub. A matriz Linux/Python 3.11–3.14 permanece pendente da futura publicação autorizada. Nenhum push foi realizado.
