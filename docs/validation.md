# Evidência de validação local

Data: 2026-09-02. Ambiente: Windows, Python 3.14.7, Selenium 4.47.0, pytest 8.4.2 e Google Chrome em modo headless. Todos os dados de catálogo são sintéticos.

## Resultado

- 38 testes aprovados: 35 casos sem navegador e 3 integrações com Chrome real.
- Integração DOM: simular, corrigir varejo/atacado, recarregar, reconciliar sem novas correções, preservar itens bloqueados e tolerância de um centavo.
- Integração de falhas: catálogo duplicado, navegação fora da fixture e botão de salvar desabilitado com timeout auditado.
- Fakes: interrupção depois da gravação, persistência que falha, mudança antes da escrita, falha de auditoria e trava concorrente.
- Regras: limites monetários e comerciais, dados inválidos, grade XG, cores, duplicatas, estoque e origem incerta.

Execução completa:

```text
python -m pytest -q -p no:cacheprovider --basetemp <pasta-temporaria-exclusiva> --tb=short
38 passed
```

O ambiente de execução exigiu acesso autorizado à rede para instalar dependências/adquirir o driver e uma pasta temporária exclusiva devido a permissões do Windows. Essas restrições iniciais de ambiente foram resolvidas; nenhum teste foi pulado para obter o resultado.

## Comandos do README executados

```text
price-demo
{"mode": "dry_run", "results": ["correct", "correct", "unchanged", "blocked", "blocked", "blocked"]}

price-demo --apply --repeat
{"mode": "apply", "results": ["correct", "correct", "unchanged", "blocked", "blocked", "blocked"]}
{"mode": "apply", "results": ["unchanged", "unchanged", "unchanged", "blocked", "blocked", "blocked"]}
```

O relatório JSONL foi gerado localmente e excluído do versionamento. O catálogo foi reiniciado em cada novo processo do navegador; a segunda passagem acima usou a mesma sessão.

## Estado da publicação

O repositório público foi criado vazio. O código e os commits permanecem locais, aguardando autorização explícita de push. O workflow está preparado, mas **não foi executado no GitHub**. Python 3.11–3.13 e Linux ainda dependem dessa execução de CI; os testes locais foram em Python 3.14 no Windows.

## Limites da evidência

Não houve validação em loja real, API externa, backend transacional, campanha, implantação ou execução com as 245/101/193 referências citadas como contexto. A retomada entre processos é testada com fake que preserva o estado; o mock HTML demonstra persistência apenas na sessão do navegador.
