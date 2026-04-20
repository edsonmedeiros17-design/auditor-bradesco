import streamlit as st
import pdfplumber
import pandas as pd
import re

# 1. VALIDAÇÃO DO GOOGLE E CONFIGURAÇÃO
# Isso insere a tag de verificação que o Google pediu de forma invisível para o usuário
st.set_page_config(page_title="Edson Medeiros | Consultoria", layout="wide")
st.markdown(f'<div style="display:none text-indent:-9999px;">google-site-verification: u-8Cv23oI8_QCuHNzQA-Vwqffb58GtwXEWc7jBYJFcQ</div>', unsafe_allow_html=True)

# 2. ESTILO CSS E SELOS DE SEGURANÇA
st.markdown("""
<style>
    .stApp { background-color: #0F172A; color: white; }
    .main-title { color: #BFAF83; font-size: 3rem; font-weight: bold; text-align: center; }
    .selos-container {
        background: rgba(255,255,255,0.05);
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        border: 1px solid #BFAF83;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# 3. ÁREA DE ACESSO (Login com Selos)
if 'auth' not in st.session_state:
    st.session_state['auth'] = False

if not st.session_state['auth']:
    st.markdown("<h2 style='text-align:center; color:#BFAF83;'>CONSULTORIA MEDEIROS - ACESSO RESTRITO</h2>", unsafe_allow_html=True)
    
    # Exibição dos Selos de Segurança na tela de Login
    st.markdown("""
    <div class="selos-container">
        <div style="display: flex; justify-content: center; gap: 30px; align-items: center;">
            <div style="text-align: center;">
                <img src="https://img.icons8.com/shield-check-mark" width="50" style="filter: invert(80%);">
                <p style="font-size: 0.7rem; color: #94A3B8;">SITE PROTEGIDO<br><b>CERTIFICADO SSL</b></p>
            </div>
            <div style="text-align: center;">
                <img src="https://img.icons8.com/color/48/google-logo.png" width="45">
                <p style="font-size: 0.7rem; color: #94A3B8;">SAFE BROWSING<br><b>GOOGLE</b></p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    user = st.text_input("Usuário (E-mail)")
    pw = st.text_input("Senha", type="password")
    
    if st.button("ENTRAR NO SISTEMA"):
        if user == "edson.senabr@gmail.com" and pw == "Roberta123":
            st.session_state['auth'] = True
            st.rerun()
        else:
            st.error("Credenciais Inválidas")
    st.stop()

# 4. CONTEÚDO PÓS-LOGIN (O que já estava funcionando)
st.markdown('<h1 class="main-title">Auditoria de Ativos</h1>', unsafe_allow_html=True)
st.info("O sistema está operando em ambiente seguro e criptografado.")

# ... (restante do código de processamento de PDF que você já tem)
