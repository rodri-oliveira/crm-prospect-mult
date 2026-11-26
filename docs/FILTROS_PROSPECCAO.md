# Filtros da lista de prospecção

A lista tem filtros combináveis de loja/responsável, telefone/WhatsApp, cidade, UF, segmento, tipo de contato, datas e múltiplos status. Nome e cidade ignoram acentos e maiúsculas; palavras do nome podem estar em outra ordem. Telefones aceitam busca parcial e formatos com +55. O tipo de contato considera os campos telefone e WhatsApp; uma loja pode ter fixo e celular.

Ao abrir /prospeccao sem filtros, o período é hoje e aparece nos campos. Os atalhos Hoje, Últimos 7 dias (incluindo hoje), Este mês e Todo o histórico preservam os demais filtros. Datas se referem a data_prospeccao (atualizada nas interações), não à criação do cadastro. Limpar filtros consulta todo o histórico ativo; periodo=todos torna essa escolha explícita na URL, inclusive após uma ação no cartão. Datas inválidas ou invertidas recebem erro 400 com explicação.

Status/cidades não apagam outros filtros. Cada chip aplicado pode ser removido individualmente. Formulários dos cartões preservam telefone, tipo, múltiplos status e demais filtros. O botão Incluir arquivados adiciona esses registros ao mesmo recorte; Ocultar arquivados volta aos ativos. A busca por telefone respeita período e arquivamento, sem ampliar silenciosamente a consulta.

Sem status escolhido, retornos agendados permanecem na Agenda. Uma seleção explícita de status permite encontrá-los na lista. Contadores e lista usam o mesmo predicado SQLite, evitando totais que incluam agendamentos ocultos. Os números dos status refletem o recorte atual; Limpar status remove apenas essa seleção.

Não há alteração no banco nem serviço pago. O formulário usa uma grade que depende da largura disponível do painel, evitando oito campos apertados no notebook.

Validação: testes de integração com SQLite temporário para normalização, múltiplos status, WhatsApp sem telefone principal, arquivados, período, contagem, links e retorno após tabulação; ver tests/integration/test_prospect_filters.py. Teste visual em navegador é opcional e não foi executado neste ambiente.
