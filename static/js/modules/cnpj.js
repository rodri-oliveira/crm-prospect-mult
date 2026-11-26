import { formatPhoneBR, legacyMobileSuggestion } from './phone-format.js';
let fillRequest = 0;

/**
 * Módulo de consulta de CNPJ
 * Integração com API backend
 */

/**
 * Consulta CNPJ via API backend
 */
export async function consultarCNPJ() {
    const el = document.getElementById('f_cnpj');
    const status = document.getElementById('cnpjStatus');
    const cnpj = (el?.value || '').trim();

    if (!cnpj) {
        status.textContent = 'Informe o CNPJ';
        status.className = 'text-xs text-red-700';
        return;
    }

    status.textContent = 'Consultando...';
    status.className = 'text-xs text-gray-500';

    try {
        const resp = await fetch(`/api/cnpj/consultar?cnpj=${encodeURIComponent(cnpj)}`);
        const data = await resp.json();

        if (!resp.ok || !data.ok) {
            const msg = data.message || '';
            if (resp.status === 502 || msg.includes('indisponíveis') || msg.includes('Falha')) {
                status.textContent = 'Serviço de consulta temporariamente indisponível. Tente novamente em alguns segundos.';
            } else if (msg.includes('inválido')) {
                status.textContent = 'CNPJ inválido. Verifique o número digitado.';
            } else if (msg.includes('não encontrado')) {
                status.textContent = 'CNPJ não encontrado na base de dados.';
            } else {
                status.textContent = msg || 'Erro ao consultar CNPJ';
            }
            status.className = 'text-xs text-red-700';
            return;
        }

        if (data.ativo === false) {
            const situ = (data.situacao || '').trim();
            status.textContent = situ ? `CNPJ NÃO ATIVO (${situ})` : 'CNPJ NÃO ATIVO';
            status.className = 'text-xs text-red-700';
            el.value = data.cnpj;
            return;
        }

        const razao = data.data?.razao_social || data.data?.nome_fantasia;
        const aberturaRaw = data.data?.data_abertura || data.data?.data_inicio_atividade;
        let msg = razao ? `OK: ${razao}` : 'OK';
        let cls = 'text-xs text-green-700';

        if (aberturaRaw) {
            const d = new Date(String(aberturaRaw).substring(0, 10) + 'T00:00:00');
            if (!isNaN(d.getTime())) {
                const now = new Date();
                const diffDays = Math.floor((now.getTime() - d.getTime()) / (1000 * 60 * 60 * 24));
                const aberturaFmt = String(aberturaRaw).substring(0, 10).split('-').reverse().join('/');
                msg += ` | Abertura: ${aberturaFmt}`;
                if (diffDays >= 0 && diffDays < 365) {
                    const meses = Math.floor(diffDays / 30);
                    msg += ` | ATENÇÃO: CNPJ com ${meses} meses (Multilaser exige 12+ meses para faturado)`;
                    cls = 'text-xs text-red-700 font-bold';
                } else {
                    const anos = Math.floor(diffDays / 365);
                    const meses = Math.floor((diffDays % 365) / 30);
                    if (anos >= 1) {
                        msg += ` | OK: ${anos} ano${anos > 1 ? 's' : ''} e ${meses} meses (aprovado para faturado)`;
                    }
                }
            }
        }

        status.textContent = msg;
        status.className = cls;
        el.value = data.cnpj;
    } catch (e) {
        status.textContent = 'Erro de conexão. Verifique sua internet e tente novamente.';
        status.className = 'text-xs text-red-700';
    }
}

/**
 * Consulta o CNPJ digitado e preenche o formulario com os dados oficiais.
 */
export async function preencherDadosCNPJ() {
    const el = document.getElementById('f_cnpj');
    const status = document.getElementById('cnpjStatus');
    const cnpj = (el?.value || '').trim();
    const requestId = ++fillRequest;
    const review = document.getElementById('cnpjPhoneReview');
    const reviewText = document.getElementById('cnpjPhoneReviewText');
    const applyPhone = document.getElementById('cnpjPhoneApply');
    if (review) review.hidden = true;
    if (applyPhone) applyPhone.onclick = null;
    const requestedCnpj = cnpj.replace(/\D/g, '');
    const isCurrent = () => {
        if (requestId !== fillRequest) return false;
        if ((el?.value || '').replace(/\D/g, '') !== requestedCnpj) {
            status.textContent = 'CNPJ alterado. Clique em Preencher dados para consultar novamente.';
            status.className = 'text-xs text-gray-500';
            return false;
        }
        return true;
    };
    // Preserve fields already completed by the user or by a Maps selection.
    const fields = ['f_nome', 'f_endereco', 'f_cidade', 'f_estado', 'f_telefone', 'f_email'];
    const original = new Map(fields.map(id => [id, document.getElementById(id)?.value || '']));
    let filled = 0;
    const fill = (id, value) => {
        const field = document.getElementById(id);
        if (!field || original.get(id).trim() || field.value.trim() || !String(value || '').trim()) return;
        setValue(id, value);
        filled += 1;
    };

    if (!cnpj) {
        status.textContent = 'Informe o CNPJ';
        status.className = 'text-xs text-red-700';
        return;
    }

    status.textContent = 'Buscando dados...';
    status.className = 'text-xs text-gray-500';

    try {
        const resp = await fetch(`/api/cnpj/consultar?cnpj=${encodeURIComponent(cnpj)}`);
        const data = await resp.json();
        if (!isCurrent()) return;

        if (!resp.ok || !data.ok) {
            status.textContent = data.message || 'Erro ao buscar dados do CNPJ';
            status.className = 'text-xs text-red-700';
            return;
        }

        const d = data.data || {};
        setValue('f_cnpj', data.cnpj);
        fill('f_nome', d.nome_fantasia?.trim() || d.razao_social || '');
        fill('f_endereco', buildEnderecoComCep(d.endereco, d.cep));
        fill('f_cidade', d.cidade || '');
        fill('f_estado', d.estado || '');
        fill('f_telefone', formatPhoneBR(d.telefone || ''));
        fill('f_email', d.email || '');
        const phone = document.getElementById('f_telefone');
        const loadedPhone = formatPhoneBR(d.telefone || '');
        const suggestion = legacyMobileSuggestion(d.telefone);
        if (suggestion && phone?.value === loadedPhone && review && reviewText && applyPhone) {
            reviewText.textContent = `A fonte retornou ${loadedPhone}, com 8 dígitos após o DDD. Pode ser um celular antigo. Sugestão: ${suggestion}. Confira antes de usar; isso não confirma WhatsApp.`;
            review.hidden = false;
            applyPhone.onclick = () => {
                if (!isCurrent() || phone.value !== loadedPhone) {
                    reviewText.textContent = 'O CNPJ ou telefone mudou. Consulte novamente para revisar a sugestão.';
                    applyPhone.hidden = true;
                    return;
                }
                setValue('f_telefone', suggestion);
                review.hidden = true;
            };
            applyPhone.hidden = false;
        }

        const razao = d.razao_social || d.nome_fantasia || 'CNPJ encontrado';
        const notice = ' Campos existentes preservados. WhatsApp, site e responsável precisam de confirmação.';
        status.textContent = (data.ativo === false
            ? `Dados preenchidos | CNPJ NAO ATIVO (${data.situacao || 'situacao desconhecida'})`
            : `${filled} campo(s) preenchido(s): ${razao}`) + notice;
        status.className = data.ativo === false
            ? 'text-xs text-red-700 font-bold'
            : 'text-xs text-green-700';
    } catch (e) {
        if (!isCurrent()) return;
        status.textContent = 'Erro de conexao. Verifique sua internet e tente novamente.';
        status.className = 'text-xs text-red-700';
    }
}

function setValue(id, value) {
    const el = document.getElementById(id);
    if (!el || value == null || String(value).trim() === '') return;
    el.value = String(value).trim();
    el.dispatchEvent(new Event('input', { bubbles: true }));
}


function buildEnderecoComCep(endereco, cep) {
    const end = String(endereco || '').trim();
    const cepClean = String(cep || '').trim();
    if (!end) return '';
    if (!cepClean || end.includes(cepClean)) return end;
    return `${end}, ${cepClean}`;
}

// Expõe globalmente para compatibilidade
window.consultarCNPJ = consultarCNPJ;
window.preencherDadosCNPJ = preencherDadosCNPJ;
