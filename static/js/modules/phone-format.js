/* Formatting never invents digits. Legacy mobile corrections require review. */
const ddds = new Set('11 12 13 14 15 16 17 18 19 21 22 24 27 28 31 32 33 34 35 37 38 41 42 43 44 45 46 47 48 49 51 53 54 55 61 62 63 64 65 66 67 68 69 71 73 74 75 77 79 81 82 83 84 85 86 87 88 89 91 92 93 94 95 96 97 98 99'.split(' '));

function nationalDigits(value) {
    let digits = String(value || '').replace(/\D/g, '');
    if (digits.startsWith('55') && [12, 13].includes(digits.length)) digits = digits.slice(2);
    return digits;
}

export function formatPhoneBR(value) {
    const raw = String(value || '').trim();
    if (!raw) return '';
    // Keep separate numbers separate instead of treating them as a single long phone.
    if (/[\/;,]/.test(raw)) return raw.split(/[\/;,]/).map(formatPhoneBR).filter(Boolean).join(' / ');
    const digits = nationalDigits(raw);
    if (digits.length === 8) return `${digits.slice(0, 4)}-${digits.slice(4)}`;
    if (digits.length === 9) return `${digits.slice(0, 5)}-${digits.slice(5)}`;
    if (digits.length === 10 && ddds.has(digits.slice(0, 2))) return `(${digits.slice(0, 2)}) ${digits.slice(2, 6)}-${digits.slice(6)}`;
    if (digits.length === 11 && ddds.has(digits.slice(0, 2)) && digits[2] === '9') return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7)}`;
    return raw;
}

export function legacyMobileSuggestion(value) {
    const raw = String(value || '').trim();
    if (/[\/;,]/.test(raw) || /[^\d\s()+.\-]/.test(raw)) return '';
    const digits = nationalDigits(raw);
    // 6/7 can refer to other historical services. Never guess for these prefixes,
    // landlines, incomplete local numbers, service numbers or already complete mobiles.
    if (digits.length !== 10 || !ddds.has(digits.slice(0, 2)) || !['8', '9'].includes(digits[2])) return '';
    return formatPhoneBR(digits.slice(0, 2) + '9' + digits.slice(2));
}
