export const deriveMapsKey = (mapsUrl, mapsPlaceId, id) => {
    const url = String(mapsUrl || '').trim();
    if (url) {
        try {
            const u = new URL(url);
            const cid = u.searchParams.get('cid');
            if (cid && /^\d+$/.test(cid)) {
                return `cid:${cid}`;
            }
        } catch (e) {}
        const m = url.match(/(0x[0-9a-fA-F]+:0x[0-9a-fA-F]+)/);
        if (m && m[1]) {
            return `ftid:${m[1].toLowerCase()}`;
        }
    }
    const k = String(mapsPlaceId || id || '').trim();
    return k;
};

/**
 * Log de debug
 */
export const mapsLog = (event, data) => {
    try {
        if (!window.MAPS_DEBUG) return;
        console.log(`[MAPS_DEBUG] ${event}`, data || {});
    } catch (e) {}
};

/**
 * Renderiza resultados no drawer
 */
