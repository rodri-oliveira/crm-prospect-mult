# Manutenção e validação

## Responsabilidades

| Área | Local |
|---|---|
| Foco comercial atual e consultas de descoberta | `application/maps/accessories.py` |
| Orquestração da busca e compatibilidade das chamadas | `application/maps/search_results.py` |
| Construção das consultas dos segmentos anteriores | `application/maps/queries.py` |
| Vocabulários dos segmentos anteriores | `application/maps/profiles.py` |
| Filtros por segmento/geografia | `application/maps/filters/` |
| Vocabulário e validação comuns dos status | `application/shared/workflow.py` e `status.py` |
| Identidade de empresa | `application/shared/company_identity.py` |
| Prévia e validação CSV | `application/prospeccao/import_csv.py` |
| Gravação CSV atômica sem sobrescrever duplicados | `infrastructure/repositories/csv_prospect_repository.py` |
| Cadastro manual/Maps compartilhado | `infrastructure/repositories/prospeccao_creation.py` |
| Conversão atômica em lead | `infrastructure/repositories/prospeccao_conversion.py` |
| Relatórios completos e de prospecção | `infrastructure/reporting/complete.py` e `prospecting.py` |
| Interface da prospecção | `templates/prospeccao/` |
| Renderização, paginação e preenchimento do Maps | `static/js/modules/maps-renderer.js`, `maps-pagination.js`, `maps-item-form.js` |
| Acesso local/autenticação e CSRF | `interfaces/web/security.py` e `static/js/security.js` |

Os módulos antigos de relatórios permanecem como adaptadores, delegando à implementação única. As rotas existentes continuam disponíveis. Regras dos outros segmentos foram extraídas sem revisão comercial; testes antigos verificam sua compatibilidade.

## Verificações

- Inicialização de banco novo, inicialização repetida e tabelas de vendas.
- Fluxo de cada status de prospect, lead e resultado dos retornos.
- Conversão repetida, preservação de retorno e reversão da transação se falhar a migração do histórico.
- Retomada de um contato sem duplicar o lead original.
- Venda com cálculo decimal, validação numérica e agendamento de pós-venda.
- CSV com prévia assinada, linhas inválidas, duplicados em arquivados e repetição da importação.
- Proteção CSRF, autenticação configurada e bloqueio de acesso remoto sem configuração.
- Teste de navegador opcional, sem acessar serviços externos; habilite `CRM_BROWSER_TESTS=1`.

Nesta execução, a inicialização do navegador foi bloqueada pelas restrições do ambiente. A verificação visual completa e a coleta real do Google Maps não foram concluídas. O teste de navegador foi mantido como verificação explícita opcional, sem mascarar a limitação como teste aprovado.

## Resultado desta revisão

167 testes Python aprovados e 1 teste de navegador não executado (opt-in). O vínculo entre 15 módulos JavaScript, a sintaxe e os utilitários de escape/URL foram verificados separadamente com Node.

## Banco existente

Faça backup com `python -m scripts.backup_database` antes da atualização. Migrações são aditivas. O controle `retorno_encerrado` é criado nos contatos para encerrar pendências sem apagar as datas históricas. Conexões do runtime ativam chaves estrangeiras. A aplicação não reclassifica registros legados automaticamente.

O repositório público deve conter apenas código e dados sintéticos. Banco, backups, listas comerciais e relatórios exportados ficam fora do Git.

## Correção da regressão de descoberta — Adamantina

A revisão anterior restringiu indevidamente a descoberta a consultas específicas de acessórios e deixou passar faculdade e fornecedor de portões. Além disso, o filtro baseado no sufixo do nome descartava lojas como BSN Tecnologia, interpretando Tecnologia como uma cidade. Essa validação por nome foi retirada do fluxo de acessórios; localização explícita continua sendo conferida.

A descoberta usa categorias de lojas de informática, informática, suprimentos, periféricos, distribuidores e papelaria/informática. A atividade real é qualificada após a coleta. Categorias capturadas do cartão são separadas do segmento selecionado na busca. O coletor não lê contêineres com links de outros estabelecimentos. Ensino e portões/segurança sem evidência de comércio de informática são excluídos.

Os logs por consulta mostram `collected`, `after_activity` e `after_location`, além dos únicos após deduplicação. O mapa do Google e a lista coletada não são fontes idênticas; não se promete igualdade entre todos os marcadores visíveis e os resultados extraídos. O cache antigo dos resultados é invalidado; cadastros e histórico comercial não são apagados.

Os testes reproduzem os nomes e tipos dos casos relatados, com categorias de exemplo explicitamente declaradas. Não são uma medição da quantidade real disponível no Google Maps. A tentativa de abrir o Chromium neste ambiente foi bloqueada, portanto a coleta real permanece sem validação nesta execução.
