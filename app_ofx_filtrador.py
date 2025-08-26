
import streamlit as st
import pandas as pd
import unicodedata

st.set_page_config(
    page_title="Filtro de OFX",
    page_icon="💸",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.title("💸 Filtro de Movimentações OFX (.TXT)")
st.markdown("Envie um arquivo `.ofx` no formato **TXT**. O sistema irá remover automaticamente movimentações com os MEMOs:")
st.markdown("- `RESGATE INVEST FACIL`\n- `APLIC.INVEST FACIL`\n- `APLIC.AUTOM.INVESTFACIL`\n- `RESG.AUTOM.INVEST FACIL`")

uploaded_file = st.file_uploader("📤 Faça upload do arquivo .ofx", type="ofx", help="Apenas arquivos OFX em formato TXT")

def limpar_texto(texto):
    texto = texto.upper()
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    texto = texto.replace('*', '').strip()
    return texto

def process_ofx(file_content):
    keywords_excluir = [
        'RESGATE INVEST FACIL',
        'APLIC.INVEST FACIL',
        'APLIC.AUTOM.INVESTFACIL',
        'RESG.AUTOM.INVEST FACIL'
    ]
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
            if '<MEMO>' in linha:
                memo = limpar_texto(linha.strip().replace('<MEMO>', ''))
                return any(k in memo for k in keywords_excluir)
        return False

    memos_excluidos = []
    memos_mantidos = []
    blocos_filtrados = []

    for bloco in stmttrn_blocks:
        memo_line = next((l for l in bloco if '<MEMO>' in l), '').strip()
        memo_text = memo_line.replace('<MEMO>', '') if memo_line else '(Sem MEMO)'
        if bloco_deve_ser_excluido(bloco):
            memos_excluidos.append(memo_text)
        else:
            memos_mantidos.append(memo_text)
            blocos_filtrados.append(bloco)

    inicio = []
    fim = []

    for line in lines:
        if '<STMTTRN>' in line or '</STMTTRN>' in line:
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

    return ''.join(novo_conteudo), memos_excluidos, memos_mantidos

if uploaded_file is not None:
    st.info("📄 Arquivo carregado com sucesso. Iniciando processamento...")
    with st.spinner("Processando..."):
        novo_ofx, memos_excluidos, memos_mantidos = process_ofx(uploaded_file.read())
    st.success("✅ Processamento concluído!")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🔴 MEMOs Excluídos")
        if memos_excluidos:
            st.table(pd.DataFrame(memos_excluidos, columns=["MEMO"]))
        else:
            st.write("Nenhum MEMO excluído.")
    with col2:
        st.subheader("🟢 MEMOs Mantidos")
        if memos_mantidos:
            st.table(pd.DataFrame(memos_mantidos, columns=["MEMO"]))
        else:
            st.write("Nenhum MEMO mantido.")

    st.download_button("📥 Baixar OFX filtrado", novo_ofx, file_name="extrato_filtrado.ofx", mime="text/plain")
