import { renderResults } from './maps-renderer.js';
export { renderResults } from './maps-renderer.js';
import { pagination } from './maps-pagination.js';
import { deriveMapsKey, mapsLog } from './maps-utils.js';
import { useItem } from './maps-item-form.js';
/**
 * Módulo de resultados do Maps
 * Gerencia renderização e carregamento de resultados da API
 */

import { writeMapsCache, readMapsCache, clearMapsCache, buildQueryPayload, getLastMapsItems, setLastMapsItems, removeItemByKey } from './maps-cache.js';
import { closeDrawer } from './maps-drawer.js';
import { submitLeadFormAsJsonIfFromMaps } from './form.js';



export const loadResults = async () => {
    const statusEl = document.getElementById('mapsDrawerStatus');
    const subEl = document.getElementById('mapsDrawerSub');
    const statsEl = document.getElementById('mapsDrawerStats');
    const statsUniqueEl = document.getElementById('mapsStatsUnique');
    if (!statusEl || !subEl) return;

    const { segmentosSelecionados, cidade, estado, query } = buildQueryPayload();
    subEl.textContent = query ? query : '';

    mapsLog('loadResults:start', { query, cidade, estado, segmentosSelecionados });

    statusEl.textContent = 'Carregando...';
    if (statsEl) statsEl.classList.add('hidden');

    try {
        const params = new URLSearchParams();
        if (query) params.set('query', query);
        if (cidade) params.set('cidade', cidade);
        if (estado) params.set('estado', estado);
        params.set('limit', '200');
        (segmentosSelecionados || []).forEach((s) => params.append('segmentos', s));
        const resp = await fetch(`/api/maps/resultados?${params.toString()}`);
        const data = await resp.json();
        if (!resp.ok || !data.ok) throw new Error(data.message || 'Erro');

        // Atualizar status e estatísticas
        const totalQueries = (data.executed_queries || []).length;
        const collected = (data.query_stats || []).reduce((n, item) => n + (Number(item.collected) || 0), 0);
        const mergedBefore = data.merged_before_dedupe || 0;
        const mergedAfter = data.merged_after_dedupe || 0;

        if (data.modo === 'mock' && data.message) {
            const failureText = `Falha na busca: ${data.message}`;
            clearMapsCache();
            statusEl.textContent = failureText;
            renderResults([]);
            try {
                if (window.ProspeccaoState && typeof window.ProspeccaoState.save === 'function') {
                    window.ProspeccaoState.save({ mapsSearchPending: false });
                } else {
                    localStorage.setItem('mapsSearchPending', '0');
                }
            } catch (e) {}
            return;
        } else {
            statusEl.textContent = data.modo === 'mock' ? 'Modo: mock' : `OK - ${totalQueries} queries`;
        }

        // Alinhar "Abrir no Google Maps" com a query principal executada
        if (Array.isArray(data.executed_queries) && data.executed_queries.length > 0) {
            const primaryQuery = data.executed_queries[0];
            window.__mapsPrimaryQuery = primaryQuery;
            try {
                const payload = { cidade, estado, segmentos: segmentosSelecionados || [] };
                window.__mapsPrimaryPayload = payload;
                localStorage.setItem('mapsPrimaryQuery', primaryQuery);
                localStorage.setItem('mapsPrimaryPayload', JSON.stringify(payload));
            } catch (e) {}
            if (subEl) subEl.textContent = primaryQuery;
            const openGoogleMaps = document.getElementById('openGoogleMaps');
            const mapFrame = document.getElementById('mapFrame');
            if (openGoogleMaps) {
                openGoogleMaps.href = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(primaryQuery)}`;
                if (!openGoogleMaps.dataset.primaryQueryBound) {
                    openGoogleMaps.dataset.primaryQueryBound = '1';
                    openGoogleMaps.addEventListener('click', (ev) => {
                        const q = window.__mapsPrimaryQuery || primaryQuery;
                        if (!q) return;
                        ev.preventDefault();
                        ev.stopPropagation();
                        const href = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(q)}`;
                        window.open(href, '_blank', 'noopener,noreferrer');
                    });
                }
            }
            if (mapFrame) {
                mapFrame.src = `https://www.google.com/maps?q=${encodeURIComponent(primaryQuery)}&output=embed`;
            }
        }

        // Mostrar estatísticas de lojas únicas
        if (statsEl && statsUniqueEl && mergedAfter > 0) {
            statsUniqueEl.textContent = mergedAfter;
            statsEl.classList.remove('hidden');
            statsEl.title = `${mergedBefore} encontradas, ${mergedAfter} únicas após deduplicação`;
        }

        mapsLog('loadResults:success', { modo: data.modo, items: (data.items || []).length, mergedBefore, mergedAfter, totalQueries });
        const nextItems = Array.isArray(data.items) ? data.items : [];
        // Não filtramos mais os itens já adicionados, deixamos a UI mostrar eles desabilitados

        if (data.modo !== 'mock') {
            if (mergedAfter > 0) {
                // Conta quantos são novos apenas para mostrar no status
                const novos = nextItems.filter(it => !it?.already_added).length;
                statusEl.textContent = `OK - ${novos} novos / ${mergedAfter} totais`;
            } else {
                statusEl.textContent = `OK - ${totalQueries} queries`;
            }
        }
        // A zero-result search is shown as empty; never reuse another city's contacts.
        writeMapsCache(nextItems, buildQueryPayload());
        statusEl.textContent = `${collected} registros coletados em ${totalQueries} consultas; ${nextItems.length} lojas na lista após filtros e duplicados.`;
        pagination.currentPage = 1;
        renderResults(nextItems);
        try {
            if (window.ProspeccaoState && typeof window.ProspeccaoState.save === 'function') {
                window.ProspeccaoState.save({ mapsSearchPending: false });
            } else {
                localStorage.setItem('mapsSearchPending', '0');
            }
        } catch (e) {}
    } catch (e) {
        mapsLog('loadResults:error', { error: String(e && e.message ? e.message : e) });
        clearMapsCache();
        statusEl.textContent = `Falha na busca: ${String(e?.message || 'Não foi possível carregar os resultados.')}`;
        renderResults([]);
    }
};

/**
 * Inicializa listeners de botões do drawer
 */
export function initDrawerButtonListeners() {
    const statusEl = document.getElementById('mapsDrawerStatus');
    const useSelectedBtn = document.getElementById('mapsUseSelected');
    const addSelectedBtn = document.getElementById('mapsAddSelected');

    // Botão Atualizar
    if (!window.__MAPS_RELOAD_DELEGATION_INSTALLED) {
        window.__MAPS_RELOAD_DELEGATION_INSTALLED = true;
        document.body.addEventListener('click', (e) => {
            const btn = e.target?.closest?.('#mapsDrawerReload');
            if (!btn) return;
            e.preventDefault();
            e.stopPropagation();
            mapsLog('reload:click', {});
            clearMapsCache();
            loadResults();
        });
    }

    // Botão Fechar
    if (!window.__MAPS_CLOSE_DELEGATION_INSTALLED) {
        window.__MAPS_CLOSE_DELEGATION_INSTALLED = true;
        document.body.addEventListener('click', (e) => {
            const btn = e.target?.closest?.('#mapsDrawerClose');
            if (!btn) return;
            e.preventDefault();
            e.stopPropagation();
            mapsLog('close:click', {});
            closeDrawer();
        });
    }

    // Overlay
    if (!window.__MAPS_OVERLAY_DELEGATION_INSTALLED) {
        window.__MAPS_OVERLAY_DELEGATION_INSTALLED = true;
        document.body.addEventListener('click', (e) => {
            const el = e.target?.closest?.('#mapsDrawerOverlay');
            if (!el) return;
            mapsLog('overlay:click', {});
            closeDrawer();
        });
    }

    // Botão Usar selecionado
    if (useSelectedBtn) {
        useSelectedBtn.addEventListener('click', () => {
            const picked = document.querySelector('input[name="mapsPick"]:checked');
            if (!picked) return;
            const id = picked.value;
            const it = (getLastMapsItems() || []).find((x) => String(x.id || '') === String(id));
            if (!it) return;
            useItem(it);
        });
    }

    // Botão Adicionar selecionados
    if (addSelectedBtn) {
        addSelectedBtn.addEventListener('click', async () => {
            const items = getPickedItems();
            if (!items || items.length === 0) return;

            if (statusEl) statusEl.textContent = 'Adicionando...';
            try {
                const resp = await fetch('/api/maps/adicionar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ items })
                });
                const data = await resp.json();
                if (!resp.ok || !data.ok) throw new Error(data.message || 'Erro');

                if (statusEl) statusEl.textContent = `Adicionados: ${data.added_count} | Já existiam: ${data.duplicate_count}`;

                const addedKeySet = new Set([].concat(data.added_keys || [], data.duplicate_keys || []).map((k) => String(k || '').trim()).filter(Boolean));
                const updatedItems = (getLastMapsItems() || []).map((it) => {
                    const key = deriveMapsKey(it.maps_url, it.maps_place_id, it.id);
                    if (key && addedKeySet.has(key)) return { ...it, already_added: true };
                    return it;
                });
                setLastMapsItems(updatedItems);
                renderResults(updatedItems);
            } catch (e) {
                if (statusEl) statusEl.textContent = 'Erro ao adicionar selecionados.';
            }
        });
    }

    const prevBtn = document.getElementById('mapsPagePrev');
    const nextBtn = document.getElementById('mapsPageNext');
    const sizeSel = document.getElementById('mapsPageSize');
    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            if (pagination.currentPage > 1) {
                pagination.currentPage -= 1;
                renderResults(getLastMapsItems());
            }
        });
    }
    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            const total = Array.isArray(getLastMapsItems()) ? getLastMapsItems().length : 0;
            const totalPages = Math.max(1, Math.ceil(total / pagination.pageSize));
            if (pagination.currentPage < totalPages) {
                pagination.currentPage += 1;
                renderResults(getLastMapsItems());
            }
        });
    }
    if (sizeSel) {
        sizeSel.addEventListener('change', () => {
            const n = parseInt(sizeSel.value, 10);
            if (!Number.isNaN(n) && n > 0) {
                pagination.pageSize = n;
                pagination.currentPage = 1;
                renderResults(getLastMapsItems());
            }
        });
    }
}

const getPickedItems = () => {
    const picked = Array.from(document.querySelectorAll('input[name="mapsPick"]:checked'));
    const ids = picked.map((el) => String(el.value || '')).filter(Boolean);
    const items = (getLastMapsItems() || []).filter((x) => ids.includes(String(x.id || '')));
    return items;
};

/**
 * Inicializa listener de submit do formulário
 */
export function initFormSubmitListener() {
    const formLead = document.getElementById('formLead');
    const statusEl = document.getElementById('mapsDrawerStatus');
    if (!formLead) return;

    formLead.addEventListener('submit', async (e) => {
        try {
            const mapsPlaceId = (document.getElementById('f_maps_place_id')?.value || '').trim();
            const mapsUrl = (document.getElementById('f_maps_url')?.value || '').trim();
            const fromMaps = !!mapsPlaceId || !!mapsUrl;
            mapsLog('form:submit', { fromMaps, mapsPlaceId: mapsPlaceId || null, hasMapsUrl: !!mapsUrl });
            if (!fromMaps) return;

            e.preventDefault();
            const res = await submitLeadFormAsJsonIfFromMaps();
            if (!res || !res.handled) return;

            mapsLog('form:submit:api_done', { created: res.data ? res.data.created : null, maps_place_id: res.data ? res.data.maps_place_id : null });

            if (res.data && res.data.redirect_to) {
                window.location.assign(res.data.redirect_to);
                return;
            }

            if (res.data && res.data.created === false) {
                if (statusEl) statusEl.textContent = 'Já existia na sua lista.';
                alert('Este item já existe na sua lista de prospecção.');
                const elMpid = document.getElementById('f_maps_place_id');
                const elMurl = document.getElementById('f_maps_url');
                if (elMpid) elMpid.value = '';
                if (elMurl) elMurl.value = '';
                return;
            }

            const mpid = (res.data && res.data.maps_place_id) ? String(res.data.maps_place_id).trim() : '';
            if (mpid) removeItemByKey(mpid);

            mapsLog('form:submit:remove_item', { mpid: mpid || null, remaining: Array.isArray(getLastMapsItems()) ? getLastMapsItems().length : null });

            const elMpid = document.getElementById('f_maps_place_id');
            const elMurl = document.getElementById('f_maps_url');
            const elCnpj = document.getElementById('f_cnpj');
            const elCnpjStatus = document.getElementById('cnpjStatus');
            if (elMpid) elMpid.value = '';
            if (elMurl) elMurl.value = '';
            if (elCnpj) elCnpj.value = '';
            if (elCnpjStatus) elCnpjStatus.textContent = '';

            try {
                const restore = {
                    items: Array.isArray(getLastMapsItems()) ? getLastMapsItems() : [],
                    payload: buildQueryPayload(),
                    remove_key: mpid,
                };
                sessionStorage.setItem('mapsDrawerRestore', JSON.stringify(restore));
                mapsLog('restore:write_sessionStorage', { items: restore.items.length, hasPayload: !!restore.payload, remove_key: restore.remove_key || null });
            } catch (e) {}

            try {
                formLead.reset();
                if (elMpid) elMpid.value = '';
                if (elMurl) elMurl.value = '';
                if (elCnpjStatus) elCnpjStatus.textContent = '';
            } catch (e) {}

            if (statusEl) statusEl.textContent = 'Adicionado.';

            // Limpa cache do drawer e fecha
            try {
                clearMapsCache();
            } catch (e) {}
            closeDrawer();

            // Recarrega apenas a lista de prospecção
            window.location.reload();
        } catch (err) {
            e.preventDefault();
            mapsLog('form:submit:error', { error: String(err && err.message ? err.message : err) });
            alert(err && err.message ? err.message : 'Erro ao adicionar');
        }
    });
}

// Expõe loadResults globalmente para maps-drawer (evitar dependência circular)
window.__loadMapsResults = loadResults;
window.__renderMapsResults = renderResults;
