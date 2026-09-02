# Decisões de projeto

## Fronteira entre o relato real e esta implementação

O relato fornece Python/Selenium, o problema de preços e o escopo numérico. A arquitetura, fixture, identificadores, política comercial e estratégias de auditoria/retomada deste repositório foram criados especificamente para o portfólio. Não se afirma que a automação original adotava estas mesmas escolhas.

## Referência e decisão

`baseline.json` representa uma referência previamente aprovada, sintética e imutável durante o lote. Não é derivada do POR possivelmente alterado. Cada canal tem preços e custo próprios. A grade esperada permite detectar cores/tamanhos ausentes, adicionais e duplicados; XG precisa existir e ter estoque para uma correção.

DE e POR precisam ser positivos e ordenados. O preço DE tem tolerância de um centavo; fora dela, o processo exige revisão. POR dentro da mesma tolerância é mantido. A origem precisa estar explicitamente marcada como desvio da API fictícia. Fora do mock, essa marcação exigiria evidência independente; nenhuma API é acessada aqui.

As regras de margem (10%) e variação (25%) são convenções demonstrativas. A margem é `(POR esperado − custo sintético) / POR esperado`. Não modela impostos, frete ou margem líquida. A exposição é `(POR esperado − POR atual) × estoque da grade` e não equivale a vendas ou perda financeira.

## Escrita e falha

O executor recebe uma interface pequena (`keys`, `read`, `write`, `refresh`), implementada pelo adapter Selenium e por fakes de testes. A igualdade imutável verifica todos os campos coletados antes da correção. Registra-se uma intenção com flush/fsync antes de tocar no preço. Uma falha impede a continuação do lote; bloqueios de negócio são registrados e permitem analisar as próximas ofertas.

O alvo é escrito por interação DOM. Ler o campo de entrada não basta: o adapter aguarda o valor salvo e o executor recarrega a página antes de comparar o estado observado com o esperado. O mock persiste somente o POR, mantendo os demais campos.

## Retomada

Uma intenção sem confirmação não determina se houve gravação. Por isso, cada nova passagem reconcilia o estado observado com a referência. Se a gravação anterior persistiu, a decisão será manter, sem nova escrita. Se não persistiu e as condições ainda forem válidas, pode corrigir. O histórico auxilia revisão humana; não é um cache de decisões.

O JSONL é incremental, não assinado nem transacional com o mock. Um encerramento no meio da escrita do arquivo pode deixar a última linha incompleta; preserve o original e inspecione-a antes de consumir o relatório. Uma falha ao registrar confirmação depois de salvar exige reconciliação. O sistema não promete exactly-once nem imunidade a agentes externos alterando os dados entre leitura e clique.

## Pequeno por escolha

Sem framework web, banco de dados, fila, servidor externo ou abstrações de produção. O HTML funciona por `file://`; a instalação suportada é editável no checkout, onde as fixtures estão disponíveis. A automação não injeta JavaScript para alterar preços; os testes usam scripts somente para provocar falhas e ambiguidades controladas no DOM.
