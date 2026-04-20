import streamlit as st
import pdfplumber
import pandas as pd
import re

# --- 1. CONFIGURAÇÃO MÁXIMA ---
st.set_page_config(page_title="Edson Medeiros | Auditoria", layout="wide")

# Tag Google (Essencial para sua verificação)
st.markdown('<div style="display:none;">google-site-verification: u-8Cv23oI8_QCuHNzQA-Vwqffb58GtwXEWc7jBYJFcQ</div>', unsafe_allow_html=True)

# --- 2. ESTILO VISUAL ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400&family=Great+Vibes&display=swap');
    .stApp { background-color: #0F172A; color: white; font-family: 'Inter', sans-serif; }
    .title { font-family: 'Playfair Display', serif; color: #BFAF83; font-size: 3rem; text-align: center; }
    .footer { position: fixed; bottom: 10px; width: 100%; text-align: center; }
    .signature { font-family: 'Great Vibes', cursive; color: #BFAF83; font-size: 1.8rem; }
</style>
""", unsafe_allow_html=True)

# --- 3. LOGIN ---
if 'logado' not in st.session_state:
    st.session_state['logado'] = False

if not st.session_state['logado']:
    st.markdown('<h1 class="title">CONSULTORIA MEDEIROS</h1>', unsafe_allow_html=True)
    with st.container():
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            u = st.text_input("E-mail")
            p = st.text_input("Senha", type="password")
            if st.button("ACESSAR", use_container_width=True):
                if u == "edson.senabr@gmail.com" and p == "Roberta123":
                    st.session_state['logado'] = True
                    st.rerun()
                else:
                    st.error("Dados incorretos")
    st.stop()

# --- 4. ÁREA DE AUDITORIA ---
st.markdown('<h1 class="title">Relatório de Auditoria</h1>', unsafe_allow_html=True)

# Dicionário de débitos solicitado
st.sidebar.header("FILTROS BANCÁRIOS")
TERMOS = {
    "Cesta/Pacote": "CESTA|PACOTE",
    "Tarifas": "TARIFA BANCARIA",
    "Seguros": "SEGURO",
    "Débitos BX": r"\bBX\b",
    "Mora": "MORA|JUROS"
}
escolhas = [n for n in TERMOS.keys() if st.sidebar.checkbox(n, value=True)]

arquivo = st.file_uploader("Envie o extrato em PDF", type="pdf")

if arquivo:
    with st.spinner("Analisando..."):
        lista_dados = []
        with pdfplumber.open(arquivo) as pdf:
            for p in pdf.pages:
                texto = p.extract_text()
                if texto:
                    for linha in texto.split('\n'):
                        for item in escolhas:
                            if re.search(TERMOS[item], linha, re.IGNORECASE):
                                v = re.findall(r'(\d[\d\.]*,\d{2})', linha)
                                lista_dados.append({
                                    "CATEGORIA": item,
                                    "DETALHE": linha[:70],
                                    "VALOR": v[-1] if v else "0,00"
                                })
        if lista_dados:
            df = pd.DataFrame(lista_dados)
            st.table(df) # Table é mais leve que Dataframe para evitar erros
            st.download_button("BAIXAR RESULTADO", df.to_csv(index=False).encode('utf-8'), "auditoria.csv")
        else:
            st.info("Nenhum item encontrado.")

# --- 5. RODAPÉ ---
st.markdown(f"""
<div class="footer">
    <span class="signature">Edson Medeiros</span>
    <p style="font-size: 0.6rem; opacity: 0.5;">SITE PROTEGIDO | GOOGLE VERIFIED</p>
</div>
""", unsafe_allow_html=True)
