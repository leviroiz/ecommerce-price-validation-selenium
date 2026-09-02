# Fronteira de sanitização

Este projeto foi construído exclusivamente a partir dos requisitos textuais e dados novos. Não houve leitura de repositórios, arquivos, páginas autenticadas ou material de produção da operação de e-commerce.

Publicável neste escopo:

- Conceitos de comparação DE/POR, varejo/atacado, grade XG, estoque, correção seletiva e auditoria.
- Métricas reais fornecidas pelo autor, claramente rotuladas como contexto no README.
- Código novo, página local, seletor novo e dados fictícios `SYN-*`.

Não incluir em contribuições:

- Código ou organização confidencial de sistemas reais.
- URLs internas, endpoints, seletores, cookies, tokens ou perfis autenticados.
- Identificadores, nomes de empresa ou dados de clientes/produtos reais.
- Capturas, logs ou relatórios oriundos da operação real.

O CLI não aceita endereço remoto e abre um perfil temporário de Chrome. O adapter verifica o endereço antes de coletar ou interagir. A página tem CSP sem conexões remotas. Isso limita o demo; não transforma código modificado por terceiros em sandbox de segurança. Instalação de pacotes e aquisição do driver podem acessar os serviços públicos dos fornecedores.

Relatórios e ambiente virtual são ignorados pelo Git. Logs de erro armazenam a classe da exceção, sem copiar mensagens arbitrárias do navegador. Nenhum segredo é necessário no workflow. Antes de publicar alterações futuras, revise tanto o diff quanto o histórico para preservar esta fronteira.
