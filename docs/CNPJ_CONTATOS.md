# Preenchimento de contatos pelo CNPJ

A consulta padrão `/api/cnpj/consultar?cnpj=...` tenta BrasilAPI e complementa telefone/e-mail pela ReceitaWS quando faltarem. Não depende de parâmetros adicionais. Um resultado parcial com nome e endereço não encerra mais a busca de contatos. A identidade, o endereço e a situação da primeira fonte são preservados ao complementar contatos da mesma inscrição.

- Um segundo telefone da BrasilAPI é aproveitado se o primeiro estiver vazio.
- A fonte do telefone aparece em `data.fonte_telefone`.
- O número original fica em `data.telefone_original`.
- Números com DDD válido e oito dígitos locais começando em 8/9 recebem o nono dígito. O ajuste fica sinalizado em `data.telefones` e na mensagem do formulário. Prefixos 6/7 são ambíguos e não são alterados.
- Um celular pode preencher o campo WhatsApp como **sugestão não confirmada**. A consulta não verifica cadastro no WhatsApp. Fixos não viram WhatsApp automaticamente. Telefone fixo e celular separados por barra são tratados individualmente.
- Cada clique em Preencher dados limpa os dados da empresa anterior e preenche a nova consulta, inclusive limpando campos ausentes na resposta (site, responsável, e-mail, vínculos Maps e anotações antigas). CNPJ e segmentos selecionados permanecem. Edições feitas enquanto a resposta está chegando são preservadas. O botão fica desabilitado durante a consulta e respostas de CNPJs anteriores são ignoradas.
- Consultas com telefone retornado ficam em cache em memória por cinco minutos (até 128 inscrições) para reduzir chamadas repetidas. Ausência de contato não é armazenada em cache. Não há migração de banco ou cadastro automático.
- Uma segunda fonte indisponível gera aviso de consulta incompleta. Ausência de telefone não é apresentada como sucesso de obtenção do contato.
- `consulta_versao=20261126-contatos-1` permite identificar um backend antigo ainda rodando; o formulário informa que é necessário reiniciar se a versão não estiver presente.

Validação: consulta real do CNPJ 35303902000181 pelo cliente Flask sem parâmetro adicional, seguida de execução do JavaScript real do formulário com essa resposta. A resposta retornou telefone e e-mail pela ReceitaWS; o celular antigo foi ajustado e preencheu a sugestão de WhatsApp, marcada como não confirmada. Testes automatizados cobrem fontes parciais, cache, preservação, números, múltiplos contatos e compatibilidade. A conferência visual por Chromium não pôde ser executada neste ambiente.
