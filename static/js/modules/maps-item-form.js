import { closeDrawer } from './maps-drawer.js';
import { getLastMapsItems, buildQueryPayload } from './maps-cache.js';
import { updateBtnBuscarCnpjGoogle } from './maps-search.js';
const updatePhoneBadge = (tel) => {
    const badge = document.getElementById('f_telefone_badge');
    if (!badge) return;
    if (!tel) {
        badge.classList.add('hidden');
        badge.innerHTML = '';
        return;
    }
    const clean = tel.replace(/\D/g, '');
    const hasDDD = clean.length >= 10;
    const first = hasDDD ? clean.charAt(2) : clean.charAt(0);

    badge.classList.remove('hidden', 'text-brand-700', 'bg-brand-50', 'border-brand-100', 'text-gray-600', 'bg-gray-100', 'border-gray-200');
    badge.className = 'text-[9px] font-bold px-1.5 py-0.5 rounded border ';

    if (['2','3','4','5'].includes(first)) {
        badge.textContent = '📞 FIXO';
        badge.classList.add('text-brand-700', 'bg-brand-50', 'border-brand-100');
        badge.classList.remove('hidden');
    } else if (first === '9') {
        badge.textContent = '📱 CELULAR';
        badge.classList.add('text-gray-600', 'bg-gray-100', 'border-gray-200');
        badge.classList.remove('hidden');
    } else {
        badge.classList.add('hidden');
    }
};

export const useItem = async (it) => {
    const form = document.getElementById('formLead');
    if (!form) return;

    const setVal = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.value = val || '';
        if (id === 'f_site') {
            try { updateSiteLink(); } catch (e) {}
        }
    };

    const updateSiteLink = () => {
        const input = document.getElementById('f_site');
        const btn = document.getElementById('f_site_btn');
        if (!input || !btn) return;

        const normalizeWebsite = (value) => {
            const raw = String(value || '').trim();
            if (!raw) return '';
            const cleaned = raw.replace(/\s+/g, ' ').trim();
            const urlMatch = cleaned.match(/(https?:\/\/[^\s]+)/i);
            if (urlMatch && urlMatch[1]) return urlMatch[1].trim();
            const domainMatch = cleaned.match(/([a-z0-9][a-z0-9\-.]+\.[a-z]{2,})(\/[^\s]*)?/i);
            if (domainMatch && domainMatch[0]) return domainMatch[0].trim();
            return cleaned.replace(/^[^a-z0-9]+/i, '').trim();
        };

        const normalized = normalizeWebsite(input.value);
        if (!normalized) {
            btn.classList.add('hidden');
            btn.onclick = null;
            return;
        }

        const href = (normalized.startsWith('http://') || normalized.startsWith('https://')) ? normalized : `https://${normalized}`;
        btn.classList.remove('hidden');
        btn.onclick = () => {
            // Usar globalThis.open para evitar conflito com sandbox/extensões
            const opener = typeof globalThis !== 'undefined' ? globalThis.open : window.open;
            if (typeof opener === 'function') {
                opener(href, '_blank', 'noopener,noreferrer');
            } else {
                // Fallback: criar link e clicar
                const a = document.createElement('a');
                a.href = href;
                a.target = '_blank';
                a.rel = 'noopener,noreferrer';
                a.click();
            }
        };
    };

    const currentKey = String(it.maps_place_id || it.id || '').trim();
    window.__mapsUseCurrentKey = currentKey;

    let enriched = it;
    setVal('f_nome', enriched.nome || '');
    setVal('f_endereco', enriched.endereco || '');
    setVal('f_telefone', enriched.telefone || '');
    setVal('f_whatsapp', enriched.whatsapp || '');
    setVal('f_email', enriched.email || '');
    setVal('f_site', enriched.website || enriched.site || '');
    setVal('f_maps_place_id', enriched.maps_place_id || enriched.id || '');
    setVal('f_maps_url', enriched.maps_url || '');
    setVal('f_cidade', it.cidade || (document.getElementById('mapCidade')?.value || ''));
    setVal('f_estado', it.estado || (document.getElementById('mapEstado')?.value || ''));

    // Atualiza badge de telefone
    updatePhoneBadge(enriched.telefone || '');
    const inputTel = document.getElementById('f_telefone');
    if (inputTel) {
        inputTel.oninput = (e) => updatePhoneBadge(e.target.value);
    }

    try {
        const inputSite = document.getElementById('f_site');
        if (inputSite) inputSite.addEventListener('input', updateSiteLink);
        updateSiteLink();
    } catch (e) {}

    try { updateBtnBuscarCnpjGoogle(); } catch (e) {}

    const checks = form.querySelectorAll('input[name="segmento"]');
    if (checks && enriched.segmentos && Array.isArray(enriched.segmentos)) {
        checks.forEach((el) => {
            el.checked = enriched.segmentos.includes(el.value);
        });
    }

    const statusEl = document.getElementById('mapsDrawerStatus');
    const needsDetails = (!enriched.website) && !!enriched.maps_url;
    if (needsDetails) {
        try {
            if (statusEl) statusEl.textContent = 'Buscando detalhes...';
            fetch('/api/maps/detalhe', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ maps_url: enriched.maps_url })
            })
                .then(async (resp) => ({ ok: resp.ok, data: await resp.json().catch(() => null) }))
                .then(({ ok, data }) => {
                    if (window.__mapsUseCurrentKey !== currentKey) return;
                    if (!ok || !data || !data.ok || !data.item) return;
                    const d = data.item;
                    if (d.endereco) setVal('f_endereco', d.endereco);
                    if (d.telefone) {
                        setVal('f_telefone', d.telefone);
                        const curWa = (document.getElementById('f_whatsapp')?.value || '').trim();
                        if (!curWa) setVal('f_whatsapp', d.telefone);
                    }
                    if (d.website) setVal('f_site', d.website);
                    if (statusEl) statusEl.textContent = 'OK';
                    try { updateBtnBuscarCnpjGoogle(); } catch (e) {}
                })
                .catch(() => {});
        } catch (e) {}
    }

    // Fecha o drawer para revelar o formulário
    try {
        window.__mapsResultsCache = Array.isArray(getLastMapsItems()) ? getLastMapsItems() : [];
        window.__mapsLastPayloadCache = buildQueryPayload();
    } catch (e) {}
    closeDrawer();
};

/**
 * Carrega resultados da API
 */
