import streamlit as st
import pdfplumber
import pandas as pd
import re

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Auditoria Premium | Edson Medeiros", layout="wide")

# --- CSS CUSTOMIZADO: QUIET LUXURY REFINADO ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;500;600&family=Great+Vibes&display=swap');

    :root {
        --navy-prime: #001F3F;
        --off-white: #F8F4E6;
        --cinza-chumbo: #2C3E50;
        --cinza-hover: #34495E;
        --bege-fendi: #D2B48C;
        --dourado-matte: #BFAF83;
    }

    .stApp { background-color: var(--off-white); font-family: 'Inter', sans-serif; }

    /* SIDEBAR: ALTO CONTRASTE (7:1+) */
    section[data-testid="stSidebar"] {
        background-color: var(--cinza-chumbo) !important;
        width: 300px !important;
        padding: 24px 10px;
        border-right: 1px solid var(--bege-fendi);
    }

    section[data-testid="stSidebar"] .stMarkdown h3, 
    section[data-testid="stSidebar"] .stMarkdown p, 
    section[data-testid="stSidebar"] label {
        color: #FFFFFF !important;
        font-weight: 500 !important;
    }

    /* Estilização Checkboxes */
    div[data-testid="stCheckbox"] {
        padding: 5px 12px;
        transition: all 0.2s ease;
    }
    div[data-testid="stCheckbox"]:hover {
        background-color: var(--cinza-hover);
        border-radius: 5px;
    }

    h1 {
        font-family: 'Playfair Display', serif !important;
        color: var(--navy-prime) !important;
        font-size: 2.5rem !important;
    }

    /* CARDS DE RESULTADOS */
    div[data-testid="stDataFrame"] {
        background-color: #FFFFFF;
        border: 1px solid var(--bege-fendi);
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.08);
        padding: 10px;
    }

    /* FOOTER BRANDING */
    .footer { position: fixed; bottom: 20px; right: 30px; text-align: right; }
    .footer-line { border-top: 1px solid var(--bege-fendi); width: 120px; margin-left: auto; margin-bottom: 8px; }
    .footer-text { font-family: 'Great Vibes', cursive; color: var(--dourado-matte); font-size: 1.3rem; }
    </style>
    """, unsafe_allow_html=True)

# --- HEADER ---
st.title("Auditoria de Ativos")
st.markdown("<p style='color: #5D6D7E; font-size: 1.1rem; margin-top:-15px;'>Inteligência Especializada em Extratos Bradesco</p>", unsafe_allow_html=True)

# --- DICIONÁRIO AMPLIADO DE FILTROS ---
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
