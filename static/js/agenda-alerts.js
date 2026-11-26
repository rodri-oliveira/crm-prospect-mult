/* Shared across pages and HTMX navigation; never reload a form to show an alert. */
(function () {
    if (window.__crmAgendaAlerts) {
        window.__crmAgendaAlerts.refresh();
        return;
    }
    let inFlight = false;
    function render(data) {
        const keys = ['total', 'hoje', 'atrasados', 'urgentes'];
        if (!keys.every(key => Number.isInteger(data[key]) && data[key] >= 0)) return;
        const overdue = data.atrasados > 0;
        const urgent = data.urgentes > 0;
        const parts = [];
        if (overdue) parts.push(`Atrasados: ${data.atrasados}`);
        if (urgent) parts.push(`Em até 1h: ${data.urgentes}`);
        const summary = parts.join(' · ') || (data.total ? `Hoje: ${data.hoje}` : '');
        for (const suffix of ['', '-mobile']) {
            const link = document.getElementById('nav-agendamentos' + suffix);
            const badge = document.getElementById('badge-agendamentos' + suffix);
            const notice = document.getElementById('aviso-agendamentos' + suffix);
            if (link) {
                link.setAttribute('href', data.mostrar_futuros ? '/agendamentos?todos=1' : '/agendamentos');
                link.classList.toggle('agenda-atrasado', overdue);
                link.classList.toggle('agenda-urgente', !overdue && urgent);
                link.title = summary || 'Nenhum retorno pendente para hoje';
                link.setAttribute('aria-label', `Agendamentos: ${data.total} pendente(s). ${summary}`);
            }
            if (badge) {
                badge.textContent = String(data.total);
                badge.hidden = data.total === 0;
                badge.classList.toggle('agenda-badge-red', overdue);
                badge.classList.toggle('animate-pulse-red', overdue);
                badge.classList.toggle('agenda-badge-amber', !overdue);
            }
            if (notice) notice.textContent = summary;
        }
    }
    async function refresh() {
        if (inFlight || document.visibilityState === 'hidden') return;
        inFlight = true;
        try {
            const response = await fetch('/api/retornos/stats', { cache: 'no-store' });
            if (!response.ok) return;
            render(await response.json());
        } catch (error) {
            // Preserve the last valid indicator during temporary connection errors.
        } finally {
            inFlight = false;
        }
    }
    window.__crmAgendaAlerts = { refresh };
    setInterval(refresh, 30000);
    document.addEventListener('visibilitychange', refresh);
    document.addEventListener('htmx:afterSwap', refresh);
    window.addEventListener('focus', refresh);
    refresh();
})();
