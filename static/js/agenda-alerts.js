/* Shared across pages and HTMX navigation; never reload a form to show an alert. */
(function () {
    const version = '20261126-sidebar-2';
    if (window.__crmAgendaAlerts?.version === version) {
        window.__crmAgendaAlerts.refresh();
        return;
    }
    window.__crmAgendaAlerts?.stop?.();
    let inFlight = false;
    let lastData = null;
    const controller = new AbortController();
    function paintSidebar(data, unavailable = false) {
        const box = document.getElementById('sidebar-agenda-callout');
        const link = document.getElementById('sidebar-agenda-callout-link');
        const title = document.getElementById('sidebar-agenda-callout-title');
        const text = document.getElementById('sidebar-agenda-callout-text');
        const overdue = (data?.atrasados || 0) > 0;
        const urgent = (data?.urgentes || 0) > 0;
        if (box) {
            box.hidden = !(overdue || urgent || unavailable);
            box.style.backgroundColor = overdue ? '#fef2f2' : '#fff7ed';
            box.style.borderColor = overdue ? '#dc2626' : '#ea580c';
            box.style.color = overdue ? '#991b1b' : '#9a3412';
        }
        if (title) title.textContent = overdue ? '⚠ RETORNOS ATRASADOS'
            : urgent ? '🔔 RETORNOS PRÓXIMOS' : '⚠ VERIFIQUE A AGENDA';
        const parts = [];
        if (overdue) parts.push(`Atrasados: ${data.atrasados}`);
        if (urgent) parts.push(`Em até 1h: ${data.urgentes}`);
        if (unavailable) parts.push('Atualização indisponível. Consulte a agenda.');
        if (text) text.textContent = parts.join(' · ');
        if (link) link.setAttribute('href', data?.mostrar_futuros ? '/agendamentos?todos=1' : '/agendamentos');
    }
    function render(data) {
        const keys = ['total', 'hoje', 'atrasados', 'urgentes'];
        if (!data || !keys.every(key => Number.isInteger(data[key]) && data[key] >= 0)) { paintSidebar(lastData, true); return; }
        lastData = data;
        paintSidebar(data);
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
                link.style.backgroundColor = overdue ? '#fef2f2' : urgent ? '#fff7ed' : '';
                link.style.borderLeft = overdue ? '4px solid #dc2626' : urgent ? '4px solid #ea580c' : '';
                link.style.color = overdue ? '#991b1b' : urgent ? '#9a3412' : '';
                link.classList.toggle('agenda-atrasado', overdue);
                link.classList.toggle('agenda-urgente', !overdue && urgent);
                link.title = summary || 'Nenhum retorno pendente para hoje';
                link.setAttribute('aria-label', `Agendamentos: ${data.total} pendente(s). ${summary}`);
            }
            if (badge) {
                badge.textContent = String(data.total);
                badge.style.backgroundColor = overdue ? '#dc2626' : '#b45309';
                badge.style.color = '#fff';
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
            if (!response.ok) { paintSidebar(lastData, true); return; }
            render(await response.json());
        } catch (error) {
            // Keep the last count and make the monitoring failure visible.
            paintSidebar(lastData, true);
        } finally {
            inFlight = false;
        }
    }
    const timer = setInterval(refresh, 30000);
    const options = { signal: controller.signal };
    document.addEventListener('visibilitychange', refresh, options);
    document.addEventListener('htmx:afterSwap', refresh, options);
    window.addEventListener('focus', refresh, options);
    window.__crmAgendaAlerts = { version, refresh, stop() { clearInterval(timer); controller.abort(); } };
    refresh();
})();
