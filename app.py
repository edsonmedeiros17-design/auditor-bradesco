import streamlit as st
import pdfplumber
import pandas as pd
import re

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Edson Medeiros | Consultoria", layout="wide")

# 2. ESTILO CSS (SIMPLIFICADO PARA EVITAR ERROS)
st.markdown("""
<style>
    .stApp { background-color: #0F172A; color: white; }
    .main-title { color: #BFAF83; font-size: 3rem; font-weight: bold; text-align: center; }
    .btn-whatsapp { 
        background-color: #25D366; color: white; padding: 15px; 
        border-radius: 10px; text-decoration: none; display: block; text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# 3. AUTENTICAÇÃO
if 'auth' not in st.session_state:
    st.session_state['auth'] = False

if not st.session_state['auth']:
    st.markdown("<h2 style='text-align:center; color:#BFAF83;'>ACESSO RESTRITO</h2>", unsafe_allow_html=True)
    user = st.text_input("Usuário")
    pw = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if user == "edson.senabr@gmail.com" and pw == "Roberta123":
            st.session_state['auth'] = True
            st.rerun()
        else:
            st.error("Credenciais Inválidas")
    st.stop()

# 4. CONTEÚDO PRINCIPAL
st.markdown('<h1 class="main-title">Consultoria de Ativos</h1>', unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])
with col2:
    st.markdown('<a href="https://contate.me/5592995087379" class="btn-whatsapp">Falar com Consultor ⚖️</a>', unsafe_allow_html=True)

# Parâmetros de Busca
DICIONARIO = {
    "Cesta / Pacote": "CESTA|PACOTE",
    "Tarifas Bancárias": "TARIFA BANCARIA",
    "Mora": "MORA",
    "Seguro": "SEGURO"
}

upload = st.file_uploader("Submeta o arquivo PDF", type="pdf")

if upload:
    with st.spinner('Processando...'):
        dados = []
        try:
            with pdfplumber.open(upload) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        for linha in text.split('\n'):
                            for nome, termo in DICIONARIO.items():
                                if re.search(termo, linha, re.IGNORECASE):
                                    valor = re.findall(r'(\d[\d\.]*,\d{2})', linha)
                                    valor_f = valor[-1] if valor else "0,00"
                                    dados.append({
                                        "DATA": "Ver extrato",
                                        "CATEGORIA": nome,
                                        "DESCRIÇÃO": linha[:80],
                                        "VALOR": valor_f
                                    })
            
            if dados:
                df = pd.DataFrame(dados)
                st.write("### Ocorrências Identificadas")
                st.dataframe(df, use_container_width=True)
                
                csv = df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 BAIXAR LAUDO", csv, "laudo.csv", "text/csv")
            else:
                st.info("Nenhuma irregularidade encontrada.")
        except Exception as e:
            st.error(f"Erro ao ler PDF: {e}")
