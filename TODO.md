# Próximas melhorias

A revisão de novembro de 2026 entregou correções de status/agendamentos, vendas em banco novo, conversão atômica, importação CSV, proteção de acesso, extração dos módulos maiores e testes. Consulte [o fluxo atual](docs/FLUXO_COMERCIAL.md) e [a manutenção](docs/MANUTENCAO.md).

Pendências que dependem de validação adicional:

- [ ] Executar o teste visual em um ambiente que permita Chromium (`CRM_BROWSER_TESTS=1`).
- [ ] Conferir uma cópia do banco existente e os registros legados, sem reclassificação automática.
- [ ] Validar a coleta real do Google Maps; os testes não acessam serviços externos.
- [ ] Avaliar filtros por potencial de compra com critérios fornecidos pelo vendedor; não inferir porte ou faturamento apenas pelo nome da loja.
- [ ] Se houver necessidade de vários vendedores, projetar contas individuais e permissões.
