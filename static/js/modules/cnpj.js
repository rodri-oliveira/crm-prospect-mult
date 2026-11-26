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
    const fields = ['f_nome', 'f_endereco', 'f_cidade', 'f_estado', 'f_telefone', 'f_whatsapp', 'f_email'];
    const original = new Map(fields.map(id => [id, document.getElementById(id)?.value || '']));
    let filled = 0;
    const fill = (id, value) => {
        const field = document.getElementById(id);
        if (!field || original.get(id).trim() || field.value.trim() || !String(value || '').trim()) return false;
        setValue(id, value);
        filled += 1;
        return true;
    };

    if (!cnpj) {
        status.textContent = 'Informe o CNPJ';
        status.className = 'text-xs text-red-700';
        return;
    }

    const button = document.getElementById('btnPreencherCnpj');
    if (button) button.disabled = true;
    status.textContent = 'Buscando cadastro e contatos...';
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
        const whatsappFilled = fill('f_whatsapp', formatPhoneBR(d.whatsapp || ''));
        const whatsappNote = document.getElementById('f_whatsapp_status');
        if (whatsappFilled && whatsappNote) {
            whatsappNote.textContent = 'Celular sugerido; WhatsApp ainda não confirmado.';
            whatsappNote.hidden = false;
        }

        const razao = d.razao_social || d.nome_fantasia || 'CNPJ encontrado';
        const missing = [];
        if (!document.getElementById('f_telefone')?.value.trim()) missing.push('telefone');
        if (!document.getElementById('f_email')?.value.trim()) missing.push('e-mail');
        const versionMissing = data.consulta_versao !== '20261126-contatos-1';
        const source = d.fonte_telefone ? ` Telefone: ${d.fonte_telefone}.` : '';
        const adjusted = d.telefones?.some(p => p.nono_digito_ajustado)
            ? ' Celular no formato antigo: nono dígito acrescentado; confira o número.' : '';
        const unavailable = missing.length ? ` Sem dados disponíveis para: ${missing.join(', ')}.` : '';
        const outcome = filled ? `${filled} campo(s) preenchido(s).` : 'Os campos já preenchidos foram preservados.';
        const inactive = data.ativo === false ? ` CNPJ NÃO ATIVO (${data.situacao || 'situação desconhecida'}).` : '';
        const notices = Array.isArray(data.avisos) ? data.avisos.join(' ') : '';
        const restart = versionMissing ? ' Reinicie o aplicativo: o servidor ainda não carregou a consulta atualizada.' : '';
        status.textContent = `Consulta concluída: ${razao}. ${outcome}${source}${adjusted}${unavailable}${inactive} ${notices} WhatsApp sugerido precisa de confirmação.${restart}`;
        status.className = data.ativo === false ? 'text-xs text-red-700 font-bold'
            : (missing.length || versionMissing || notices) ? 'text-xs text-amber-800' : 'text-xs text-green-700';
    } catch (e) {
        if (!isCurrent()) return;
        status.textContent = 'Erro de conexao. Verifique sua internet e tente novamente.';
        status.className = 'text-xs text-red-700';
    } finally {
        if (button && requestId === fillRequest) button.disabled = false;
    }
}

function setValue(id, value) {
    const el = document.getElementById(id);
    if (!el || value == null || String(value).trim() === '') return;
    el.value = String(value).trim();
    el.dispatchEvent(new Event('input', { bubbles: true }));
}

function formatPhoneBR(value) {
    const raw = String(value || '').trim();
    if (!raw) return '';

    let digits = raw.replace(/\D/g, '');
    if (!digits) return raw;

    if (digits.startsWith('55') && (digits.length === 12 || digits.length === 13)) {
        digits = digits.substring(2);
    }

    if (digits.length === 8) return `${digits.substring(0, 4)}-${digits.substring(4)}`;
    if (digits.length === 9) return `${digits.substring(0, 5)}-${digits.substring(5)}`;
    if (digits.length === 10) return `(${digits.substring(0, 2)}) ${digits.substring(2, 6)}-${digits.substring(6)}`;
    if (digits.length === 11) return `(${digits.substring(0, 2)}) ${digits.substring(2, 7)}-${digits.substring(7)}`;

    return raw;
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
