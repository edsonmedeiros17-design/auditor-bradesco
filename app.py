import streamlit as st
import pdfplumber
import pandas as pd
import re

# 1. SETUP INICIAL
st.set_page_config(page_title="Edson Medeiros | Consultoria", layout="wide")
st.markdown('<div style="display:none;">google-site-verification: u-8Cv23oI8_QCuHNzQA-Vwqffb58GtwXEWc7jBYJFcQ</div>', unsafe_allow_html=True)

# 2. LOGIN SEGURO
if 'auth' not in st.session_state:
    st.session_state['auth'] = False

if not st.session_state['auth']:
    st.markdown("<h2 style='text-align:center; color:#BFAF83;'>ACESSO RESTRITO</h2>", unsafe_allow_html=True)
    u = st.text_input("Usuário")
    p = st.text_input("Senha", type="password")
    if st.button("Acessar Sistema"):
        if u == "edson.senabr@gmail.com" and p == "Roberta123":
            st.session_state['auth'] = True
            st.rerun()
        else:
            st.error("Credenciais Inválidas")
    st.stop()

# 3. CONTEÚDO (APÓS LOGIN)
st.markdown("<h1 style='text-align:center; color:#BFAF83;'>Consultoria de Ativos</h1>", unsafe_allow_html=True)

# Barra Lateral
st.sidebar.title("Filtros de Auditoria")
DIC = {"Cesta": "CESTA|PACOTE", "Tarifas": "TARIFA BANCARIA", "Mora": "MORA|JUROS", "Seguro": "SEGURO"}
filtros = [n for n in DIC.keys() if st.sidebar.checkbox(n, value=True)]

up = st.file_uploader("Envie o PDF aqui", type="pdf")

if up:
    try:
        res = []
        with pdfplumber.open(up) as pdf:
            for pg in pdf.pages:
                txt = pg.extract_text()
                if txt:
                    for lin in txt.split('\n'):
                        for f in filtros:
                            if re.search(DIC[f], lin, re.IGNORECASE):
                                val = re.findall(r'(\d[\d\.]*,\d{2})', lin)
                                res.append({"CATEGORIA": f, "DESCRIÇÃO": lin[:80], "VALOR": val[-1] if val else "0,00"})
        if res:
            df = pd.DataFrame(res)
            st.dataframe(df, use_container_width=True)
            st.download_button("BAIXAR LAUDO", df.to_csv(index=False).encode('utf-8-sig'), "laudo.csv")
        else:
            st.info("Nada encontrado.")
    except Exception as e:
        st.error(f"Erro: {e}")
