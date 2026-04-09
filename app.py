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

    /* Cores de Alto Contraste */
    :root {
        --navy-prime: #001F3F;
        --off-white: #F8F4E6;
        --cinza-chumbo: #1C2833; /* Escurecido para contraste máximo */
        --bege-fendi: #D2B48C;
        --dourado-matte: #BFAF83;
    }

    .stApp { background-color: var(--off-white); font-family: 'Inter', sans-serif; }

    /* SIDEBAR FORÇADA (Contraste Texto Branco sobre Fundo Escuro) */
    [data-testid="stSidebar"] {
        background-color: var(--cinza-chumbo) !important;
        border-right: 2px solid var(--bege-fendi);
    }
    
    [data-testid="stSidebar"] .stMarkdown h3, 
    [data-testid="stSidebar"] label p {
        color: #FFFFFF !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
    }

    /* Títulos Serifados */
    h1 {
        font-family: 'Playfair Display', serif !important;
        color: var(--navy-prime) !important;
        font-size: 3rem !important;
    }

    /* Estilização do Botão de Upload */
    .stFileUploader section {
        background-color: #FFFFFF !important;
        border: 1px solid var(--bege-fendi) !important;
        border-radius: 12px !important;
        padding: 20px !important;
    }

    /* Assinatura Edson Medeiros */
    .footer { position: fixed; bottom: 20px; right: 30px; text-align: right; }
    .footer-line { border-top: 1px solid var(--bege-fendi); width: 120px; margin-left: auto; margin-bottom: 5px; }
    .footer-text { font-family: 'Great Vibes', cursive; color: var(--dourado-matte); font-size: 1.4rem; }
    </style>
    """, unsafe_allow_html=True)

# --- CONTEÚDO ---
st.title("Auditoria de Ativos")
st.markdown("<p style='color: #5D6D7E; font-size: 1.1rem; margin-top:-20px;'>Inteligência em Leitura de Extratos</p>", unsafe_allow_html=True)

# --- DICIONÁRIO AMPLIADO (TODOS OS FILTROS) ---
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

# --- SIDEBAR ---
st.sidebar.markdown("### Tipos de Descontos")
selecionados = []
for nome in DICIONARIO_ALVOS.keys():
    if st.sidebar.checkbox(nome, value=True):
        selecionados.append(nome)

# --- ÁREA CENTRAL ---
st.markdown("<br>", unsafe_allow_html=True)
upload = st.file_uploader("Deposite o extrato PDF para análise técnica", type="pdf")

if upload and selecionados:
    with st.spinner('Analisando registros...'):
        # (Lógica de processamento simplificada aqui para o exemplo)
        st.success("Extrato carregado. Pronto para auditoria.")
        # Se você já tem a função analisar_extrato, ela entra aqui.

# --- FOOTER ---
st.markdown(f"""
    <div class="footer">
        <div class="footer-line"></div>
        <div class="footer-text">Fundado por Edson Medeiros</div>
    </div>
    """, unsafe_allow_html=True)
