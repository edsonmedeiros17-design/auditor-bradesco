import streamlit as st
import pdfplumber
import pandas as pd
import re
from datetime import datetime
from PIL import Image
import io

# --- 1. CONFIGURAÇÃO E ESTÉTICA PREMIUM (MANUTENÇÃO TOTAL) ---
st.set_page_config(page_title="Edson Medeiros | Consultoria de Ativos", layout="wide", page_icon="⚖️")

ESTILO_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600&family=Playfair+Display:ital,wght@0,700;1,700&family=Inter:wght@300;400;600&family=Great+Vibes&display=swap');
:root { --navy-deep: #0F172A; --gold-matte: #BFAF83; --emerald-success: #10B981; --off-white: #F8F9FA; }
.stApp { background: radial-gradient(circle at center, #1E293B 0%, #0F172A 100%); color: var(--off-white); font-family: 'Inter', sans-serif; }
.consultoria-title { font-family: 'Playfair Display', serif !important; font-size: 4.5rem !important; font-weight: 700 !important; background: linear-gradient(180deg, #FFFFFF 0%, #BFAF83 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 0px 2px 0px #8A7650, 0px 4px 10px rgba(0,0,0,0.5); line-height: 1.1; margin-bottom: 5px; }
.btn-whatsapp { background-color: #25D366 !important; color: white !important; padding: 14px 28px !important; border-radius: 50px !important; text-decoration: none !important; font-weight: bold !important; display: inline-block !important; transition: 0.3s !important; box-shadow: 0 4px 15px rgba(37, 211, 102, 0.4) !important; text-align: center; border: none !important; margin-top: 10px; }
.impact-card { background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(191, 175, 131, 0.2); border-radius: 12px; padding: 20px; text-align: center; margin-bottom: 20px; }
.resumo-direto { background: rgba(191, 175, 131, 0.05); border: 1px solid rgba(191, 175, 131, 0.2); padding: 20px; border-radius: 12px; margin-bottom: 30px; }
.categoria-badge { background: rgba(191, 175, 131, 0.15); color: #BFAF83; border: 1px solid #BFAF83; padding: 6px 15px; border-radius: 20px; font-size: 0.75rem; margin: 5px; display: inline-block; font-weight: 600; letter-spacing: 1px; }
.how-it-works { background: rgba(15, 23, 42, 0.6); border-radius: 16px; padding: 40px; margin-top: 60px; border: 1px solid rgba(191, 175, 131, 0.1); margin-bottom: 100px; }
.step-number { color: var(--gold-matte); font-family: 'Cinzel', serif; font-size: 1.8rem; margin-bottom: 10px; }
.footer-signature { position: fixed; bottom: 30px; right: 40px; text-align: right; z-index: 100; }
.footer-name { font-family: 'Great Vibes', cursive; color: var(--gold-matte); font-size: 2.2rem; margin: 0; }
[data-testid="stSidebar"] { background-color: #080C14 !important; border-right: 1px solid #1E293B; }
</style>
"""
st.markdown(ESTILO_CSS, unsafe_allow_html=True)

# --- 2. TELA DE ACESSO RESTRITO (LOGIN INTEGRADO) ---
def tela_login():
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False

    if not st.session_state["autenticado"]:
        _, col_login, _ = st.columns([1, 1.2, 1])
        with col_login:
            st.markdown("<br><br><br>", unsafe_allow_html=True)
            st.markdown("<h2 style='font-family: Cinzel; color: #BFAF83; letter-spacing: 3px; text-align: center;'>ACESSO RESTRITO</h2>", unsafe_allow_html=True)
            email = st.text_input("E-mail de Acesso")
            senha = st.text_input("Senha", type="password")
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("AUTENTICAR SISTEMA", use_container_width=True):
                if email == "edson.senabr@gmail.com" and senha == "medeirosefernandes2026":
                    st.session_state["autenticado"] = True
                    st.rerun()
                else:
                    st.error("Credenciais incorretas.")
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div style="text-align: center;"><a href="https://contate.me/5592995087379" class="btn-whatsapp" target="_blank">Suporte Técnico ⚖️</a></div>', unsafe_allow_html=True)
        return False
    return True

if tela_login():
    # --- 3. DASHBOARD PRINCIPAL (SOFISTICAÇÃO MANTIDA) ---
    col_head, col_cta = st.columns([2.5, 1])
    with col_head:
        st.markdown('<h1 class="consultoria-title">Consultoria de Ativos</h1>', unsafe_allow_html=True)
        st.markdown("<p style='color: #BFAF83; letter-spacing: 2px; font-size: 0.9rem;'>AUDITORIA TÉCNICA PROPRIETÁRIA DE EXTRATOS</p>", unsafe_allow_html=True)
    with col_cta:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown('<a href="https://contate.me/5592995087379" class="btn-whatsapp" target="_blank">Falar com Consultor ⚖️</a>', unsafe_allow_html=True)

    # --- 4. SIDEBAR E PARÂMETROS (RÚBRICAS ATUALIZADAS) ---
    st.sidebar.markdown("### PARÂMETROS DE BUSCA")
    DICIONARIO_ALVOS = {
        "CESTA/PACOTE": "CESTA|PACOTE",
        "MORA": "MORA",
        "BX": r"\bBX\b",
        "PARCELA CREDITO PESSOAL": "PARCELA CREDITO PESSOAL",
        "GASTOS CARTAO DE CREDITO": "GASTOS CARTAO DE CREDITO",
        "SEGURO": "SEGURO",
        "ADIANT": "ADIANT",
        "APLIC": "APLIC",
        "ENCARGOS": "ENCARGOS",
        "ANUIDADE": "ANUIDADE",
        "OPERACOES VENCIDAS": "OPERACOES VENCIDAS",
        "DIV. EM ATRASO": "DIV. EM ATRASO"
    }
    selecionados = [n for n in DICIONARIO_ALVOS.keys() if st.sidebar.checkbox(n, value=True)]
    
    st.sidebar.markdown("<br>### PERÍODO DE AUDITORIA", unsafe_allow_html=True)
    usar_data = st.sidebar.checkbox("Ativar Limite (Prescrição)")
    if usar_data:
        d_inf = st.sidebar.date_input("Início", format="DD/MM/YYYY")
        d_sup = st.sidebar.date_input("Fim", format="DD/MM/YYYY")

    # --- 5. LÓGICA DE PROCESSAMENTO HÍBRIDO (DIGITAL + IMAGEM) ---
    st.markdown("<br>", unsafe_allow_html=True)
    upload = st.file_uploader("Upload de Extratos (PDF Digital ou Scans/Fotos/Imagens)", type=["pdf", "png", "jpg", "jpeg"])

    if upload:
        with st.spinner('Executando Auditoria Crítica e Reconhecimento de Imagem...'):
            dados = []
            termos = [DICIONARIO_ALVOS[f] for f in selecionados]
            linhas_extraidas = []

            # Passo 1: Extração Inteligente
            if upload.type == "application/pdf":
                with pdfplumber.open(upload) as
