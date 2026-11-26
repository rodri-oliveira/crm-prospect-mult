# Avisos de retornos no menu

O menu usa as mesmas listas de retornos pendentes da agenda, para prospecções e leads, inclusive quando a tabulação é Enviado Portfólio Whats. Retornos arquivados ou encerrados seguem as exclusões da agenda. Não são criados novos agendamentos nem alteradas datas.

- **Vermelho com contador pulsante:** existe retorno com data anterior ou horário já vencido hoje.
- **Laranja:** existe retorno nos próximos 60 minutos, sem atrasados.
- **Contador sem urgência:** existem outros retornos para hoje. Sem horário definido não é considerado vencido antes do fim do dia.
- A legenda detalha `Atrasados: N · Em até 1h: N`. O total conta cada retorno uma vez, mesmo que tenha vencido hoje.
- A janela de uma hora atravessa a meia-noite; quando necessário, o link da agenda inclui a exibição de futuros.
- O relógio de referência é America/Sao_Paulo. Em Windows sem a base IANA, usa UTC-3 como alternativa. A data da tela da agenda usa a mesma referência.

O indicador existe mesmo quando começa vazio, tanto no menu lateral quanto no cabeçalho móvel. Atualiza ao carregar, a cada 30 segundos, ao voltar para a aba e após navegação HTMX. Uma única rotina permanece ativa. A página não é recarregada e falhas de rede preservam o último indicador válido. Usuários com preferência por movimento reduzido não recebem animação.

Validação: testes com SQLite temporário reproduzem um retorno antigo e outro vencendo em 16 minutos, status de portfólio, leads, retornos encerrados, arquivamento, limites de horário, fuso e meia-noite. A API e o HTML inicial são conferidos em diferentes telas. O JavaScript é executado com DOM/rede controlados para validar transições vazio/próximo/atrasado, recuperação de rede, desktop/móvel e ausência de recarga/intervalos duplicados. Não houve conferência visual em navegador neste ambiente.


O aviso também tem um bloco fixo diretamente abaixo de CRM Multi, antes dos links do menu lateral, em todas as telas. Mostra RETORNOS ATRASADOS ou RETORNOS PRÓXIMOS com a contagem e um atalho para a agenda. O bloco usa cores inline, e o JavaScript também aplica cores no item Agendamentos, para manter a sinalização em navegação HTMX quando o cabeçalho da página não é recarregado. Uma falha na contagem deixa um aviso visível para consultar a agenda, em vez de aparentar ausência de retornos. As rotinas de atualização têm versão e limpeza de listeners/intervalo para atualizações posteriores.
