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
