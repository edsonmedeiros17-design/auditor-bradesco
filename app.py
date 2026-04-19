import streamlit as st
import pdfplumber
import pandas as pd
import re
import traceback

# --- BLINDAGEM GLOBAL ANTI-QUEDA ---
try:
    # --- 1. CONFIGURAÇÃO ---
    st.set_page_config(page_title="Edson Medeiros | Consultoria de Ativos", layout="wide", page_icon="⚖️")
    
    # TAG DE VERIFICAÇÃO GOOGLE (INVISÍVEL)
    st.markdown(f'<div style="display:none;">google-site-verification: u-8Cv23oI8_QCuHNzQA-Vwqffb58GtwXEWc7jBYJFcQ</div>', unsafe_allow_html=True)

    # --- 2. CSS CUSTOMIZADO ---
    ESTILO_CSS = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600&family=Playfair+Display:ital,wght@0,700;1,700&family=Inter:wght@300;400;600&family=Great+Vibes&display=swap');
    :root { --navy-deep: #0F172A; --gold-matte: #BFAF83; --emerald-success: #10B981; --off-white: #F8F9FA; }
    .stApp { background: radial-gradient(circle at center, #1E293B 0%, #0F172A 100%); color: var(--off-white); font-family: 'Inter', sans-serif; }
    .consultoria-title { font-family: 'Playfair Display', serif !important; font-size: 4.5rem !important; font-weight: 700 !important; background: linear-gradient(180deg, #FFFFFF 0%, #BFAF83 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 0px 2px 0px #8A7650, 0px 4px 10px rgba(0,0,0,0.5); line-height: 1.1; margin-bottom: 5px; }
    .btn-whatsapp { background-color: #25D366 !important; color: white !important; padding: 14px 28px !important; border-radius: 50px !important; text-decoration: none !important; font-weight: bold !important; display: inline-block !important; transition: 0.3s !important; box-shadow: 0 4px 15px rgba(37, 211, 102, 0.4) !important; text-align: center; border: none !important; }
    .btn-whatsapp:hover { transform: scale(1.05); background-color: #128C7E !important; }
    .impact-card { background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(191, 175, 131, 0.2); border-radius: 12px; padding: 20px; text-align: center; margin-bottom: 20px; }
    .how-it-works { background: rgba(15, 23, 42, 0.6); border-radius: 16px; padding: 40px; margin-top: 60px; border: 1px solid rgba(191, 175, 131, 0.1); }
    .step-number { color: var(--gold-matte); font-family: 'Cinzel', serif; font-size: 1.8rem; margin-bottom: 10px; }
    .login-box { background: rgba(255, 255, 255, 0.05); padding: 40px; border-radius: 16px; border: 1px solid rgba(191, 175, 131, 0.2); max-width: 450px; margin: auto; text-align: center; }
    .footer-signature { position: fixed; bottom: 30px; right: 40px; text-align: right; z-index: 100; }
    .footer-name { font-family: 'Great Vibes', cursive; color: var(--gold-matte); font-size: 2.2rem; margin: 0; }
    .footer-tech { font-family: 'Inter', sans-serif; font-size: 0.7rem; color: #64748B; letter-spacing: 3px; text-transform: uppercase; }
    
    /* Selos de Segurança Discretos */
    .footer-security {
        position: fixed; left
