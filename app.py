import streamlit as st
import pdfplumber
import pandas as pd
import re

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Auditoria Premium | Edson Medeiros", layout="wide")

# --- CSS QUIET LUXURY COM ALTO CONTRASTE ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;500;600&family=Great+Vibes&display=swap');

    :root {
        --navy-prime: #001F3F;
        --off-white: #F8F4E6;
        --cinza-chumbo: #1C2833;
        --bege-fendi: #D2B48C;
        --dourado-matte: #BFAF83;
    }

    .stApp { background-color: var(--off-white); font-family: 'Inter', sans-serif; }

    [data-testid="stSidebar"] {
        background-color: var(--cinza-chumbo) !important;
        border-right: 2px solid var(--bege-fendi);
    }
    
    [data-testid="stSidebar"] .stMarkdown h3, 
    [data-testid="stSidebar"] label p {
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }

    h1 {
        font-family: 'Playfair Display', serif !important;
        color: var(--navy-prime) !important;
        font-size: 2.5rem !important;
    }

    div[data-testid="stDataFrame"] {
        background-color: #FFFFFF;
        border-radius: 12px;
        padding: 10px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.05);
    }

    .footer { position: fixed; bottom: 20px; right: 30px; text-align: right; }
    .footer-line { border-top: 1px solid var(--bege-fendi); width: 120px; margin-left: auto; margin-bottom: 5px; }
    .footer-text { font-family: 'Great Vibes', cursive; color: var(--dourado-matte); font-size: 1.4rem; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÃO DE BUSCA ---
def analisar_extrato(file, filtros_selecionados, dicionario):
    dados = []
    termos_busca = [dicionario[f] for f in filtros_selecionados]
    
    with pdfplumber.open(file) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if texto:
                linhas = texto.split('\n')
                for linha in linhas:
                    for termo in termos_busca:
                        if re.search(termo, linha, re.IGNORECASE):
                            data_match = re.search(r'(\d{2}/\d{2}/\d{4})', linha)
                            data = data_match.group(1) if data_match else "---"
                            cat = [k for k, v in dicionario.items() if v == termo][0]
                            
                            dados.append({
                                "Data": data,
                                "Categoria": cat,
                                "Descrição Completa": linha.strip()
                            })
                            break
    return pd.DataFrame(dados)

# --- CONTEÚDO ---
st.title("Auditoria de Ativos")
st.markdown("<p style='color: #5D6D7E; font-size: 1.1rem; margin-top:-20px;'>Inteligência em Leitura de Extratos</p>", unsafe_allow_html=True)

DICIONARIO_ALVOS = {
    "Mora Crédito Pessoal": "MORA CREDITO PESSOAL",
    "Encargos": "ENCARGOS",
    "Parcela Crédito Pessoal": "PARCELA CREDITO PESSOAL",
    "Gastos Cartão de Crédito": "GASTOS CARTAO DE CREDITO",
    "BX (Baixas)": r"\bBX\b",
    "APLIC (Aplicações)": r"\bAPLIC\b",
    "Tarifa Bancária": "TARIFA BANCARIA",
    "Anuidade Cartão": "CARTAO CREDITO ANUIDADE",
    "Título de Capitalização": "TITULO DE CAPITALIZACAO",
    "Pacote de Serviços": "PACOTE DE SERVIÇOS",
    "Vida e Previdência": "VIDA E PREV",
    "Seguros": "SEGURO",
    "Serviço de Cartão": "SERVICO CARTAO",
    "Adiantamento (ADIANT)": "ADIANT",
    "Parcelas Vencidas": "VENCIDAS",
    "Tarifa 2ª Via": "TAR 2 VIA"
}

st.sidebar.markdown("### Tipos de Descontos")
selecionados = []
for nome in DICIONARIO_ALVOS.keys():
    if st.sidebar.checkbox(nome, value=True):
        selecionados.append(nome)

st.markdown("<br>", unsafe_allow_html=True)
upload = st.file_uploader("Deposite o extrato PDF para análise técnica", type="pdf")

if upload:
    if not selecionados:
        st.warning("⚠️ Selecione filtros no menu lateral.")
    else:
        with st.spinner('Auditando documento...'):
            df_resultado = analisar_extrato(upload, selecionados, DICIONARIO_ALVOS)
            if not df_resultado.empty:
                st.success(f"Encontrados {len(df_resultado)} registros.")
                st.dataframe(df_resultado, use_container_width=True)
                csv = df_resultado.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 Baixar Relatório", csv, "auditoria.csv", "text/csv")
            else:
                st.info("Nenhuma ocorrência encontrada.")

st.markdown(f"""<div class="footer"><div class="footer-line"></div><div class="footer-text">Fundado por Edson Medeiros</div></div>""", unsafe_allow_html=True)
