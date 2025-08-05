
import streamlit as st

def process_ofx(file_content):
    keywords_excluir = ['RESGATE INVEST FACIL', 'APLIC.INVEST FACIL']
    lines = file_content.decode('latin1').splitlines(keepends=True)

    stmttrn_blocks = []
    current_block = []
    in_block = False

    for line in lines:
        if '<STMTTRN>' in line:
            if current_block:
                stmttrn_blocks.append(current_block)
            current_block = [line]
            in_block = True
        elif in_block:
            current_block.append(line)
            if '</STMTTRN>' in line:
                stmttrn_blocks.append(current_block)
                current_block = []
                in_block = False

    if current_block:
        stmttrn_blocks.append(current_block)

    def bloco_deve_ser_excluido(bloco):
        for linha in bloco:
            if linha.strip().startswith('<MEMO>'):
                memo = linha.strip().replace('<MEMO>', '')
                return any(memo == k or memo.endswith(k) for k in keywords_excluir)
        return False

    blocos_filtrados = [bloco for bloco in stmttrn_blocks if not bloco_deve_ser_excluido(bloco)]
    memos_detectados = [next((line for line in b if '<MEMO>' in line), '(Sem MEMO)').strip() for b in stmttrn_blocks]

    inicio = []
    fim = []
    in_stmttrs = False

    for line in lines:
        if '<STMTTRN>' in line or '</STMTTRN>' in line:
            in_stmttrs = True
            break
        inicio.append(line)

    for i in range(len(lines) - 1, -1, -1):
        if '</STMTTRN>' in lines[i] or '<STMTTRN>' in lines[i]:
            fim = lines[i+1:]
            break

    novo_conteudo = inicio
    for bloco in blocos_filtrados:
        novo_conteudo.extend(bloco)
    novo_conteudo.extend(fim)

    return ''.join(novo_conteudo), memos_detectados

st.title("Filtro de Movimentações OFX (.SGML)")

uploaded_file = st.file_uploader("Faça upload do arquivo .ofx (formato SGML)", type="ofx")

if uploaded_file is not None:
    st.info("Arquivo carregado com sucesso. Processando...")
    novo_ofx, memos = process_ofx(uploaded_file.read())

    st.subheader("Prévia dos MEMOs detectados:")
    st.write(memos)

    st.download_button("📥 Baixar OFX filtrado", novo_ofx, file_name="extrato_filtrado.ofx", mime="text/plain")
