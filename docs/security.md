# Revisão de segurança e sanitização

## Escopo publicável

Somente código reconstruído, fixtures fictícias, testes e documentação. Referências válidas seguem DEMO-NNN. Produtos são objetos fictícios numerados; cores e tamanhos são didáticos. Não foram incluídos anexos, capturas, imagens, planilhas comerciais, nomes de empresas, plataformas internas, referências reais ou seletores de produção.

A interface foi escrita do zero. O prefixo data-demo identifica atributos próprios, não elementos importados. Os únicos números reais documentados são métricas agregadas fornecidas pelo usuário, separadas no contexto do README.

## Escrita segura

- DOM controlado via Selenium; sem automação de mouse/teclado por coordenadas.
- CLI não aceita URL remota, login ou credenciais.
- Seleção de um único produto, identidade exata, quatro campos únicos e matriz sem células duplicadas.
- Valores esperados explícitos, sem cálculo de margem ou variação percentual.
- Intenção durável, revisão de estado, rejeição de save repetido e releitura pós-escrita.
- Lado totalmente vazio, conteúdo ilegível ou estado incerto bloqueiam o corretor.
- Estoque desconhecido não é convertido em zero.
- CSV escapa possíveis fórmulas; relatórios e estado gerados não são versionados.
- Interrupção de confirmação não dispara repetição automática de clique.

## Revisão pré-publicação

Verificar arquivos versionados e histórico alcançável, não apenas a pasta atual. Procurar segredos, nomes internos, caminhos pessoais, referências comerciais, URLs não locais e arquivos binários indevidos. Revisar manualmente os resultados: hashes Git e versões não são referências de produto.

Os diretórios de ambiente, caches e relatórios estão ignorados. Não adicionar logs brutos de testes do computador, que podem conter caminhos pessoais em traceback.

## Limites

Não há integração real nem teste de segurança de painel comercial. Proteções locais não são autenticação de produção. Estado, diário e fixture precisam permanecer coerentes; modificações manuais, restauração parcial ou alteração do alvo exigem revisão. O servidor HTTP é didático, somente loopback, não deve ser exposto em rede.
