import { escapeHtml, safeHttpUrl } from './dom-safety.js';
import { setLastMapsItems, getLastMapsItems, removeItemByKey } from './maps-cache.js';
import { deriveMapsKey, mapsLog } from './maps-utils.js';
import { useItem } from './maps-item-form.js';
import { _getPagedItems, _updatePaginationUI } from './maps-pagination.js';
export const renderResults = (items) => {
    const resultsNow = document.getElementById('mapsResults');
    const emptyNow = document.getElementById('mapsEmpty');
    if (!resultsNow || !emptyNow) {
        mapsLog('renderResults:missing_elements', { hasResultsEl: !!resultsNow, hasEmptyEl: !!emptyNow });
        return;
    }
    resultsNow.innerHTML = '';
    const list = Array.isArray(items) ? items : [];
    // Mantém todos os itens, mesmo os já adicionados, para que apareçam como desativados
    const normalized = list.map((it) => {
        const key = deriveMapsKey(it.maps_url, it.maps_place_id, it.id);
        const already = !!it.already_added;
        return { ...it, __key: key, __already: already };
    });

    setLastMapsItems(normalized);
    const paging = _getPagedItems(normalized);
    _updatePaginationUI(paging);

    if (normalized.length === 0) {
        emptyNow.classList.remove('hidden');
        return;
    }
    emptyNow.classList.add('hidden');

    paging.items.forEach((it) => {
        const card = document.createElement('div');
        card.className = 'border border-gray-200 rounded-lg p-3 bg-white hover:bg-gray-50';
        card.dataset.id = it.id || '';

        const nome = escapeHtml(it.nome);
        const endereco = escapeHtml(it.endereco);
        const telefone = escapeHtml(it.telefone);
        const website = safeHttpUrl(it.website);
        const mapsUrl = escapeHtml(safeHttpUrl(it.maps_url));
        const already = !!it.__already;
        const segmentos = Array.isArray(it.segmentos) ? it.segmentos.map(escapeHtml).join(', ') : '';

        const websiteHref = (website && (website.startsWith('http://') || website.startsWith('https://')))
            ? website
            : (website ? `https://${website}` : '');

        card.innerHTML = `
            <div class="flex items-start justify-between gap-4 p-1">
                <label class="flex items-start gap-3 flex-1 cursor-pointer group/label">
                    <div class="pt-1">
                        <input type="checkbox" name="mapsPick" value="${escapeHtml(it.id)}" class="rounded-full border-gray-300 text-brand-600 focus:ring-brand-500 w-4 h-4 transition-all group-hover/label:border-brand-400" ${already ? 'disabled' : ''}>
                    </div>
                    <div class="min-w-0 flex-1">
                        <div class="text-sm font-bold text-gray-900 group-hover/label:text-brand-700 transition-colors truncate">${nome}</div>
                        <div class="text-[11px] leading-relaxed text-gray-500 mt-0.5 line-clamp-1">${endereco || '-'}</div>
                        ${it.quality_priority ? `<p class="text-xs text-blue-800">${escapeHtml(it.quality_priority)} — contato ainda não confirmado</p>` : ''}

                         <div class="flex flex-wrap items-center gap-x-2 mt-1.5">
                            ${segmentos ? `
                                <span class="inline-flex items-center px-1.5 py-0.5 rounded-md bg-gray-100 text-gray-600 text-[10px] font-medium border border-gray-200">
                                    ${segmentos}
                                </span>
                            ` : ''}
                            ${telefone ? (function(tel){
                                const clean = tel.replace(/\D/g, '');
                                const hasDDD = clean.length >= 10;
                                const first = hasDDD ? clean.charAt(2) : clean.charAt(0);
                                let badge = '';
                                if (['2','3','4','5'].includes(first)) {
                                    badge = `<span class="text-[9px] font-bold text-brand-700 bg-brand-50 border border-brand-100 px-1 py-0.5 rounded mr-1">📞 FIXO</span>`;
                                } else if (first === '9') {
                                    badge = `<span class="text-[9px] font-bold text-gray-600 bg-gray-100 border border-gray-200 px-1 py-0.5 rounded mr-1">📱 CELULAR</span>`;
                                }
                                return `<span class="text-[11px] text-gray-400 flex items-center">${badge}${tel}</span>`;
                            })(telefone) : ''}
                        </div>

                        ${website ? `
                            <div class="mt-1">
                                <a href="${escapeHtml(websiteHref)}" target="_blank" class="text-[11px] text-brand-600 hover:text-brand-800 flex items-center gap-1 transition-colors">
                                    <svg class="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9"></path></svg>
                                    ${escapeHtml(website.length > 30 ? website.substring(0, 27) + '...' : website)}
                                </a>
                            </div>
                        ` : ''}

                        ${already ? '<div class="inline-flex items-center gap-1 text-[10px] text-emerald-600 font-semibold bg-emerald-50 px-1.5 py-0.5 rounded mt-1.5">✓ Já adicionado ' + (it.existing_status ? '(' + escapeHtml(it.existing_status) + ')' : '') + '</div>' : ''}
                    </div>
                </label>

                <div class="flex flex-col gap-2 items-end shrink-0">
                    <div class="flex items-center gap-1">
                        ${mapsUrl ? `
                            <a href="${mapsUrl}" target="_blank" class="p-1.5 text-gray-400 hover:text-brand-600 hover:bg-brand-50 rounded-lg transition-all" title="Ver no Google Maps">
                                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                                </svg>
                            </a>
                        ` : ''}
                        <button type="button" class="btnDeleteItem p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-all" title="Remover da lista">
                            <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                        </button>
                    </div>
                    <button type="button" class="btnUseOne text-[11px] font-bold px-3 py-1.5 rounded-lg bg-gray-900 text-white hover:bg-black hover:scale-105 transition-all shadow-sm active:scale-95">
                        Usar
                    </button>
                </div>
            </div>
        `;

        const useBtn = card.querySelector('.btnUseOne');
        if (useBtn) {
            useBtn.addEventListener('click', () => {
                useItem(it);
            });
        }

        const deleteBtn = card.querySelector('.btnDeleteItem');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                if (confirm(`Remover "${nome}" desta lista?`)) {
                    const key = it.__key;
                    removeItemByKey(key);
                    renderResults(getLastMapsItems());
                }
            });
        }

        resultsNow.appendChild(card);
    });
};

/**
 * Usa um item (preenche formulário)
 */
