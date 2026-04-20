import streamlit as st
import pdfplumber
import pandas as pd
import re
import traceback

# --- 1. CONFIGURAÇÃO DE PÁGINA (Sempre a primeira linha) ---
st.set_page_config(page_title="Edson Medeiros | Consultoria de Ativos", layout="wide", page_icon="⚖️")

# --- 2. TAG DE VERIFICAÇÃO GOOGLE (Obrigatória para o Search Console) ---
st.markdown('<div style="display:none;">google-site-verification: u-8Cv23oI8_QCuHNzQA-Vwqffb58GtwXEWc7jBYJFcQ</div>', unsafe_allow_html=True)

# --- 3. BLINDAGEM DE ESTILO CSS ---
# Este bloco recria o visual de luxo das suas imagens anteriores
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600&family=Playfair+Display:ital,wght@0,700;1,700&family=Inter:wght@300;400;600&family=Great+Vibes&display=swap');
    :root { --navy-deep: #0F172A; --gold-matte: #BFAF83; --off-white: #F8F9FA; }
    .stApp { background: radial-gradient(circle at center, #1E293B 0%, #0F172A 100%); color: var(--off-white); font-family: 'Inter', sans-serif; }
    .consultoria-title { font-family: 'Playfair Display', serif !important; font-size: 3.5rem !important; font-weight: 700 !important; background: linear-gradient(180deg, #FFFFFF 0%, #BFAF83 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 0px; }
    .subtitle { color: #BFAF83; text-align: center; letter-spacing: 2px; font-family: 'Cinzel', serif; font-size: 0.8rem; margin-bottom: 30px; }
    .btn-whatsapp { background-color: #25D366 !important; color: white !important; padding: 10px 20px !important; border-radius: 50px !important; text-decoration: none !important; font-weight: bold !important; display: inline-block !important; }
    .footer-signature { position: fixed; bottom: 20px; right: 30px; text-align: right; }
    .footer-name { font-family: 'Great Vibes', cursive; color: var(--gold-matte); font-size: 2rem; margin: 0; }
    .footer-security { position: fixed; left: 20px; bottom: 20px; display: flex; align-items: center; gap: 10px; padding: 5px 10px; background: rgba(255,255,255,0.05); border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

# --- 4. LÓGICA DE LOGIN ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    st.markdown('<h1 class="consultoria-title">Consultoria Medeiros</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">ACESSO RESTRITO - AUDITORIA DE ATIVOS</p>', unsafe_allow_html=True)
    
    _, col_login, _ = st.columns([1, 1, 1])
    with col_login:
        email = st.text_input("E-mail de Acesso")
        senha = st.text_input("Senha", type="password")
        if st.button("ENTRAR NO SISTEMA", use_container_width=True):
            if email == "edson.senabr@gmail.com" and senha == "Roberta123":
                st.session_state['authenticated'] = True
                st.rerun()
            else:
                st.error("Credenciais incorretas.")
    st.stop()

# --- 5. INTERFACE PRINCIPAL (AUDITORIA) ---
st.markdown('<div style="text-align: right;"><a href="https://contate.me/5592995087379" class="btn-whatsapp" target="_blank">Falar com Consultor ⚖️</a></div>', unsafe_allow_html=True)
st.markdown('<h1 class="consultoria-title">Relatório de Auditoria</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">ANÁLISE TÉCNICA DE IRREGULARIDADES BANCÁRIAS</p>', unsafe_allow_html=True)

# Sidebar com Dicionário de Busca
st.sidebar.markdown("### PARÂMETROS DE BUSCA")
DICIONARIO = {
    "Cesta / Pacote": "CESTA|PACOTE",
    "Tarifas Bancárias": "TARIFA BANCARIA",
