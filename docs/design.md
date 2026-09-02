# Decisões e limites de fidelidade

## Separação dos robôs

Conferência normal, conferência XG, cruzamento com estoque e corretor são componentes independentes. A CLI os orquestra. O corretor não transforma automaticamente um relatório de divergências em aprovação.

O domínio recebe valores lidos do DOM, usa Decimal e compara igualdade. Identidade, quatro campos únicos e topologia de matriz são precondições, não regras comerciais.

## Fluxo observado versus reconstrução

O contexto descreve navegação por referência, leitura dos quatro campos, alternância atacado/varejo e correção em sete etapas. O repositório reconstrói esse fluxo com interface nova, não os detalhes internos de seleção, cálculo ou gravação do sistema observado.

Na demo, “de/por” em atacado/varejo são nomes conceituais; os alvos das grades vêm do CSV esperado. Preparar um lote significa preencher os valores absolutos dessas células. Não foi copiado um mecanismo percentual interno.

Uma grade é um dicionário cor|tamanho → preço. Divergência em uma célula com estoque zero continua sendo divergência de preço, mas não tem impacto sobre estoque disponível naquela variante. O relatório não calcula faturamento nem perda.

## Integridade e retomada

1. Ler estado atual, validar quatro campos e grades.
2. Construir alvo apenas para referências aprovadas.
3. Bloquear alvo diferente se a referência tiver intenção pendente; verificar seleção exata e valores preparados.
4. Persistir intenção SQLite (chave SHA-256 de referência e valores esperados).
5. Salvar via DOM; servidor fictício recusa seleção múltipla e revisão antiga.
6. Recarregar a tela e comparar grades, preços normais, estoque e revisão.
7. Marcar a operação como verificada.

Interrupção antes de salvar permite tentar a intenção pendente quando o estado está intacto. Interrupção depois do save permite confirmar por releitura sem novo save. Estado diferente do antes/alvo interrompe a rotina. Não há rollback automático nem garantia de transação distribuída entre SQLite e JSON: a reconciliação explícita cobre a janela entre ambos.

O bloqueio da CLI é liberado pelo sistema operacional quando o processo termina. A API Python pressupõe uso serial; múltiplos servidores editando o mesmo arquivo fora da CLI não são suportados.

## Relatórios

Os CSVs são snapshots com identidade referência/lado, escapam prefixos de fórmulas e usam substituição atômica. Um erro de escrita preserva o snapshot anterior. O corretor mantém o diário como fonte persistente; CSV não é controle de execução.

A conferência é somente leitura dos preços, mas cria os arquivos locais da demo. Reexecução refaz a conferência inteira, sem anexar duplicatas.

## Ambiente

HTTP local em porta efêmera, caminho aleatório por sessão, proteção de origem no save e política de conteúdo restrita. Essas proteções não transformam o servidor didático em serviço de produção. A origem do navegador é local; o download do driver pode depender de conexão.

Fixture esperada e catálogo compartilham uma base sintética, com divergências injetadas em arquivo separado. Isso facilita reprodução e testes; não simula fontes independentes de produção.
