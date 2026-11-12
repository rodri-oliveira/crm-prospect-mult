export const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[char]));
export const safeHttpUrl = value => {
    const text = String(value || '').trim();
    if (!text || /^[a-z][a-z0-9+.-]*:/i.test(text) && !/^https?:\/\//i.test(text)) return '';
    try {
        const url = new URL(text.includes('://') ? text : `https://${text}`);
        return ['http:', 'https:'].includes(url.protocol) && !url.username && !url.password ? url.href : '';
    } catch { return ''; }
};
