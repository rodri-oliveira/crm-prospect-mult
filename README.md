# Prospect CRM

CRM local para prospecção B2B, qualificação, retornos, negociação, vendas e pós-venda. O foco atual é **acessórios de informática no Sudeste: SP, RJ, MG e ES**.

## Prospecção sem API paga

- Busca por cidade e UF explícitas, com descoberta ampla de lojas de informática, suprimentos e periféricos, seguida de qualificação da atividade.
- Importação CSV com prévia, seleção dos contatos e validação de campos antes da gravação.
- Duplicados por CNPJ, identificador do Maps ou nome + cidade + UF não sobrescrevem o histórico. CSV considera CNPJ e nome + cidade + UF, incluindo arquivados e leads.
- Prioridade de revisão baseada em indícios de atividade e disponibilidade de canais. **Não comprova porte, intenção de compra, telefone válido ou WhatsApp ativo.**
- Seleção de um resultado do Maps não presume que o telefone seja WhatsApp.

A coleta automatizada existente usa **Playwright no site do Google Maps**, sem chave de API. Pode falhar por mudança de página ou bloqueio e depende das condições do serviço. A alternativa independente do scraper é importar listas próprias ou montar contatos a partir de fontes comerciais públicas, revisando cada contato antes de abordar. Não há garantia de cobertura completa ou obtenção automática de contatos verificados.

Os demais segmentos foram preservados para compatibilidade; a revisão de regras comerciais desta versão se concentra em acessórios de informática.

## Executar no Windows

Python 3.11 ou superior:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m playwright install chromium
python app.py
```

Acesse `http://127.0.0.1:5000`. O Chromium é necessário para coleta no Maps, não para cadastro manual, CSV, relatórios ou vendas.

O servidor inicia em acesso local e com depuração desligada. As configurações são lidas de **variáveis de ambiente**; o projeto não carrega `.env` automaticamente.

| Variável | Uso |
|---|---|
| `CRM_DATABASE_PATH` | Caminho do SQLite; padrão `database.db` na raiz |
| `CRM_HOST` | Endereço de escuta; padrão `127.0.0.1` |
| `PORT` | Porta; padrão `5000` |
| `FLASK_DEBUG` | `true` somente em desenvolvimento |
| `CRM_USERNAME` / `CRM_PASSWORD` | Configure ambos para acesso pela rede; autenticação HTTP Basic de usuário único |
| `CRM_SECRET_KEY` | Chave aleatória estável, necessária para compartilhar sessões entre processos |
| `CRM_COOKIE_SECURE` | `true` quando servido exclusivamente por HTTPS |

Para acesso por rede, configure autenticação e HTTPS com servidor adequado. `python app.py` é o servidor de desenvolvimento. A autenticação atual não implementa equipes, permissões por vendedor ou recuperação de senha. Requisições que gravam dados exigem o token CSRF da sessão; formulários e chamadas do frontend já o enviam.

## Atualizar uma instalação existente

1. Pare a aplicação e, com o ambiente virtual ativo, faça uma cópia consistente do banco:

```powershell
python -m scripts.backup_database
```

2. Guarde a cópia fora do repositório. Atualize o código preservando seu `database.db` e a mesma configuração de caminho.
3. Inicie a aplicação. A inicialização adiciona as estruturas ausentes, incluindo vendas e o controle de encerramento dos retornos, sem excluir registros.
4. Confira um prospect, um lead, agendamentos e vendas antes de retomar o uso diário.

A atualização não altera retroativamente classificações comerciais. Registros antigos podem exigir revisão; a correção impede novas conversões indevidas de descartados, mas não apaga leads previamente criados por essa falha.

## Fluxo e organização

Veja [o comportamento de cada status](docs/FLUXO_COMERCIAL.md) e [a organização do código](docs/MANUTENCAO.md).

- `domain/`: contratos dos repositórios e modelos.
- `application/`: casos de uso, validação de fluxo e critérios de qualificação.
- `infrastructure/`: SQLite, integrações e geração de relatórios.
- `interfaces/`: rotas web/API, importação e proteção das requisições.
- `templates/prospeccao/`, `templates/agendamentos/`: componentes das páginas.
- `static/js/modules/`: estado, busca, apresentação e interação dos formulários.

## Testar

```powershell
python -m pytest -q
```

Os testes usam dados sintéticos e bancos temporários: status de prospects e leads, resultados dos retornos, conversão e reversão em caso de falha, venda/pós-venda, CSV, duplicados, autenticação e CSRF.

O teste de navegador é opcional, requer Chromium e um ambiente que permita iniciar navegador e servidor local:

```powershell
$env:CRM_BROWSER_TESTS = "1"
python -m pytest tests/integration/test_browser.py -q
```

A busca real em serviços externos não é executada pela suíte automatizada. Relatórios e contadores não são evidência de validação dos contatos ou faturamento confirmado fora do CRM.
