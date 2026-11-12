# Fluxo comercial — acessórios de informática

Território atual: São Paulo, Rio de Janeiro, Minas Gerais e Espírito Santo. Uma loja descoberta é um prospect a conferir. Importação e coleta nunca comprovam interesse de compra.

## Prospecção

| Status/ação | Resultado esperado |
|---|---|
| Não contatado | Mantém na prospecção, sem qualificação automática. |
| Não atendeu | Registra tentativa; não cria lead. Na fila de retornos, conserva a data pendente. |
| Caixa postal | Mesmo tratamento de tentativa sem contato, sem inventar interesse. |
| Enviado Portfólio Whats | Registra envio; permanece prospect. O status não confirma leitura. |
| Enviado Portfólio por E-mail | Registra envio; permanece prospect. Não confirma leitura. |
| Aguard. Lista Prod. | Mantém pendência comercial; não cria venda nem lead automaticamente. |
| Não analisou ainda o material | Mantém acompanhamento. Na tabulação de retorno, exige nova data, hora e observação. |
| Pediu para retornar / Agendar retorno | Exige data e hora; aparece em agendamentos. Agendar é uma ação, não prova de interesse. |
| Solicitou portfólio | Registra solicitação; permanece prospect. |
| Pediu preço | Registra solicitação; não equivale a compra. Na tabulação, exige observação e encerra a data antiga se não houver novo retorno. |
| Aguardando dados para cadastro | Mantém acompanhamento de cadastro, sem venda automática. |
| Interessado | Qualifica e converte para lead com CNPJ válido, preservando histórico. Se faltar CNPJ, retorna erro antes da conversão. |
| Em negociação | Converte para lead no estágio Em negociação, preservando eventual retorno. A negociação pode existir antes da coleta do CNPJ. |
| Já tem consultor atendendo | Encerra o retorno pendente; não cria lead ou oportunidade de venda automaticamente. |
| Sem interesse | Encerra o retorno pendente, mantém prospect identificável e não o qualifica. |
| Descartado | Arquiva, encerra retorno e não cria lead. |
| Convertido em Lead | Resultado de uma conversão, não status aceito para simular conversão manualmente. |

Retornos vencidos continuam vencidos; não são movidos silenciosamente para hoje. Status intermediários sem nova data voltam à lista de acompanhamento após a tabulação. O usuário pode agendar um novo próximo passo. Uma data fornecida explicitamente precisa estar em formato válido.

## Leads

| Status | Resultado esperado |
|---|---|
| Novo Lead | Entrada no CRM, sem presumir venda. |
| Sem contato | Mantém estágio comercial; registra falta de contato. |
| Enviado Portfólio Whats | Registra envio; não confirma leitura ou compra. |
| Enviado Portfólio por E-mail | Registra envio; não confirma leitura ou compra. |
| Aguard. Lista Prod. | Mantém pendência de informações sobre produtos. |
| Não analisou ainda o material | Mantém acompanhamento comercial. |
| Envio de documentação | Atualiza etapa cadastral. |
| Em análise de documentação | Atualiza etapa cadastral. |
| Envio de orçamento | Atualiza etapa de proposta. |
| Falou com responsável | Registra contato com responsável; não ativa cliente. |
| Apresentação feita | Atualiza etapa de apresentação. |
| Solicitou portfólio | Registra solicitação. |
| Interessado | Atualiza interesse declarado, sem registrar faturamento. |
| Em negociação | Atualiza negociação; em interações, exige segmento informado. |
| Aguardando dados para cadastro | Mantém pendência cadastral. |
| Já tem consultor atendendo | Encerra retornos; sai da lista padrão de leads ativos. Continua recuperável por filtro. |
| Sem interesse | Encerra retornos; devolve a prospecção de origem quando houver, preservando o vínculo com o lead. Uma retomada reutiliza o mesmo lead. |
| Descartado | Encerra retornos; sai da lista padrão, mantendo ficha e histórico recuperáveis por filtro. |
| Cliente ativo | Depende de uma venda registrada no CRM. Não é permitido ativar um lead sem pedido. |

Resultados de interação e estágio são conceitos distintos. **Agendar retorno não muda o lead para Interessado.** Não atendeu, Caixa postal e Sem contato preservam a pendência existente e seu prazo. Um contato que conclui uma etapa encerra a pendência anterior e pode criar nova data. O encerramento preserva as datas históricas dos contatos; o campo `retorno_encerrado` determina se a pendência ainda está ativa.

## Venda e pós-venda

1. Escolher lead existente e informar data e itens completos.
2. O servidor valida quantidades positivas, preços finitos não negativos, estrutura das linhas e pelo menos um item.
3. Valores são calculados com decimal e arredondados em centavos antes de gravar. Não se aceita total enviado pelo navegador como fonte de verdade.
4. Pedido, itens e atualização para Cliente ativo são gravados na mesma transação.
5. A venda encerra o retorno comercial anterior. Uma data de pós-venda gera nova pendência na agenda.
6. Pedidos permanecem na ficha do lead e na carteira de clientes. O CRM registra valores informados pelo usuário; não confirma faturamento em ERP.

## Limites da atualização

- Os testes cobrem os status registrados e o ciclo com dados sintéticos; não substituem a conferência de uma cópia do banco existente.
- Classificações antigas, duplicados legados e conversões indevidas anteriores não são apagados ou corrigidos automaticamente.
- Relatórios de período misturam indicadores de atividade do período com contadores de estágio atual. Uma transição de status não deve ser interpretada como uma nova venda.
