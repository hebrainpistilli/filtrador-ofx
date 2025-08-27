import streamlit as st
import pandas as pd
from datetime import datetime

# --- Configuração da Página ---
st.set_page_config(
    page_title="Filtro de OFX",
    page_icon="💸",
    layout="wide", # Usando layout "wide" para mais espaço
    initial_sidebar_state="auto"
)

# --- CSS Personalizado para um Design Avançado ---
st.markdown("""
<style>
    /* Esconde o menu e o rodapé padrão do Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Altera o estilo dos containers principais */
    .st-emotion-cache-1g0b5a3 {
        background-color: #f0f2f6;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        padding: 20px;
        margin-bottom: 20px;
    }
    
    /* Estilo para os títulos e subtítulos */
    h1 {
        color: #2e415a;
        font-family: 'Segoe UI', sans-serif;
    }
    h3 {
        color: #5d6d7e;
        font-family: 'Segoe UI', sans-serif;
    }
    
    /* Estilo para o botão de download */
    .st-emotion-cache-12fmw13 button {
        background-color: #2c944d;
        color: white;
        border-radius: 8px;
        padding: 10px 20px;
        font-size: 16px;
        font-weight: bold;
        transition: background-color 0.3s, transform 0.3s;
    }
    .st-emotion-cache-12fmw13 button:hover {
        background-color: #3cb863;
        transform: scale(1.05);
    }

    /* Estilo para as abas */
    .st-emotion-cache-1g1q3w {
        font-size: 16px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- Barra Lateral (Sidebar) com um Visual Mais Limpo ---
st.sidebar.title("Sobre o App ℹ️")
st.sidebar.info(
    "Este aplicativo é uma ferramenta para **limpar arquivos OFX**, "
    "removendo transações automáticas de investimento. O resultado é um extrato "
    "mais claro para sua análise financeira."
)
st.sidebar.markdown("---")
st.sidebar.subheader("Instruções 📝")
st.sidebar.markdown(
    "1. **Carregue** seu arquivo `.ofx`.\n"
    "2. O sistema irá **filtrar automaticamente** as transações com os seguintes MEMOs:\n"
    "   - `RESGATE INVEST FACIL`\n"
    "   - `APLIC.INVEST FACIL`\n"
    "   - `APLIC.AUTOM.INVESTFACIL`\n"
    "   - `RESG.AUTOM.INVEST FACIL`"
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
    st.success("🎉 **Arquivo carregado com sucesso!**")
    
    with st.spinner("Processando o arquivo..."):
        novo_ofx, memos_excluidos, memos_mantidos = process_ofx(uploaded_file.read())

    st.subheader("✅ Processamento Concluído")
    
    # Criando abas para separar os resultados
    tab_mantidos, tab_excluidos = st.tabs(["✅ **Transações Mantidas**", "❌ **Transações Excluídas**"])

    with tab_mantidos:
        st.write("Aqui estão as transações que **foram mantidas** no seu extrato.")
        if memos_mantidos:
            st.dataframe(pd.DataFrame(memos_mantidos, columns=["Descrição"]), use_container_width=True)
        else:
            st.info("Nenhuma transação foi mantida.")

    with tab_excluidos:
        st.write("Estas são as transações que **foram removidas** do seu extrato.")
        if memos_excluidos:
            st.dataframe(pd.DataFrame(memos_excluidos, columns=["Descrição"]), use_container_width=True)
        else:
            st.info("Nenhuma transação foi excluída.")

    st.markdown("---")
    
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"OFX_Limpo_{data_hoje}.ofx"
    
    st.download_button(
        label="📥 **Baixar OFX Tratado**",
        data=novo_ofx,
        file_name=nome_arquivo,
        mime="text/plain"
    )
