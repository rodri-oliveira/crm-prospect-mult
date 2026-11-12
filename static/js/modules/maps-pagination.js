export const pagination = { currentPage: 1, pageSize: 50 };
export const _getPagedItems = (items) => {
    const total = Array.isArray(items) ? items.length : 0;
    const totalPages = Math.max(1, Math.ceil(total / pagination.pageSize));
    if (pagination.currentPage > totalPages) pagination.currentPage = totalPages;
    if (pagination.currentPage < 1) pagination.currentPage = 1;
    const start = total === 0 ? 0 : (pagination.currentPage - 1) * pagination.pageSize;
    const end = total === 0 ? 0 : Math.min(start + pagination.pageSize, total);
    const slice = Array.isArray(items) ? items.slice(start, end) : [];
    return { total, totalPages, page: pagination.currentPage, start, end, items: slice };
};

export const _updatePaginationUI = (paging) => {
    const infoEl = document.getElementById('mapsPageInfo');
    const rangeEl = document.getElementById('mapsPageRange');
    const prevBtn = document.getElementById('mapsPagePrev');
    const nextBtn = document.getElementById('mapsPageNext');
    const sizeSel = document.getElementById('mapsPageSize');

    if (infoEl) infoEl.textContent = `Página ${paging.page} de ${paging.totalPages}`;
    if (rangeEl) {
        const from = paging.total === 0 ? 0 : (paging.start + 1);
        const to = paging.end;
        rangeEl.textContent = `Mostrando ${from}-${to} de ${paging.total}`;
    }
    if (prevBtn) prevBtn.disabled = paging.page <= 1;
    if (nextBtn) nextBtn.disabled = paging.page >= paging.totalPages;
    if (sizeSel) sizeSel.value = String(pagination.pageSize);
};

/**
 * Obtém itens selecionados
 */
