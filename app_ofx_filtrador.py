import streamlit as st
import pandas as pd
from datetime import datetime

# --- Configuração da Página e Tema ---
st.set_page_config(
    page_title="Filtro de OFX",
    page_icon="💸",
    layout="centered",
    initial_sidebar_state="auto" # Deixa a barra lateral aberta por padrão
)

# Adicionando um pouco de CSS para um visual mais limpo (opcional)
st.markdown("""
<style>
    .reportview-container .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- Barra Lateral (Sidebar) para Organização ---
st.sidebar.title("Sobre o App ℹ️")
st.sidebar.info(
    "Este aplicativo é uma ferramenta para processar arquivos `.ofx` "
    "e remover movimentações indesejadas, como aplicações e resgates automáticos. "
    "O resultado é um extrato limpo e pronto para análise."
)

st.sidebar.markdown("---")
st.sidebar.subheader("Instruções 📝")
st.sidebar.markdown(
    "1. **Faça o upload** do seu arquivo `.ofx`.\n"
    "2. O sistema irá **remover automaticamente** as transações com os seguintes MEMOs:\n"
    "- `RESGATE INVEST FACIL`\n"
    "- `APLIC.INVEST FACIL`\n"
    "- `APLIC.AUTOM.INVESTFACIL`\n"
    "- `RESG.AUTOM.INVEST FACIL`"
)

# --- Funções de Processamento (Sem Alterações) ---
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
            if linha.strip().startswith('<MEMO>'):
                memo = linha.strip().replace('<MEMO>', '').strip()
                for k in keywords_excluir:
                    if memo.startswith(k):
                        return True
        return False

    memos_excluidos = []
    memos_mantidos = []
    blocos_filtrados = []

    for bloco in stmttrn_blocks:
        memo_line = next((l for l in bloco if '<MEMO>' in l), None)
        
        if memo_line:
            memo_text = memo_line.strip().replace('<MEMO>', '').strip()
            if memo_text.startswith('RESG.AUTOM.INVEST FACIL'):
                memo_text = 'RESG.AUTOM.INVEST FACIL'
        else:
            memo_text = '(Sem MEMO)'

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

# --- Layout Principal da Página ---
st.title("💰 Filtro de Movimentações OFX")
st.markdown("Use o formulário abaixo para enviar e filtrar seu extrato OFX.")

uploaded_file = st.file_uploader("📥 **Upload do arquivo .ofx**", type="ofx", help="Apenas arquivos OFX em formato TXT")

if uploaded_file is not None:
    st.success("🎉 Arquivo carregado com sucesso!")
    with st.spinner("Processando o arquivo..."):
        novo_ofx, memos_excluidos, memos_mantidos = process_ofx(uploaded_file.read())

    st.subheader("✅ Processamento Concluído")

    # Usando colunas para um layout mais organizado
    col1, col2 = st.columns(2)

    with col1:
        st.info("🔴 **MEMOs Excluídos**")
        if memos_excluidos:
            st.dataframe(pd.DataFrame(memos_excluidos, columns=["Descrição"]), use_container_width=True)
        else:
            st.write("Nenhum MEMO foi excluído.")

    with col2:
        st.info("🟢 **MEMOs Mantidos**")
        if memos_mantidos:
            st.dataframe(pd.DataFrame(memos_mantidos, columns=["Descrição"]), use_container_width=True)
        else:
            st.write("Todos os MEMOs foram mantidos.")

    st.markdown("---")
    
    # Gerando o nome do arquivo dinâmico
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"OFX_Limpo_{data_hoje}.ofx"
    
    st.download_button(
        label="📥 **Baixar OFX Filtrado**",
        data=novo_ofx,
        file_name=nome_arquivo,
        mime="text/plain"
    )
