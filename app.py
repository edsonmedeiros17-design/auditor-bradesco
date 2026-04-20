import streamlit as st
import pdfplumber
import pandas as pd
import re

# 1. CONFIGURAÇÃO DA PÁGINA (Sempre a primeira linha)
st.set_page_config(page_title="Edson Medeiros | Consultoria", layout="wide", page_icon="⚖️")

# Tag Google para o Search Console (Invisível)
st.markdown('<div style="display:none;">google-site-verification: u-8Cv23oI8_QCuHNzQA-Vwqffb58GtwXEWc7jBYJFcQ</div>', unsafe_allow_html=True)

# 2. ESTILO CSS (Simplificado e seguro, mantendo a elegância)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400&display=swap');
    .stApp { background-color: #0F172A; color: white; font-family: 'Inter', sans-serif; }
    .main-title { font-family: 'Playfair Display', serif; color: #BFAF83; font-size: 3.5rem; font-weight: bold; text-align: center; margin-bottom: 0px; }
    .subtitle { color: #8A7650; text-align: center; font-size: 1rem; margin-bottom: 40px; letter-spacing: 1px; }
    .btn-whatsapp { 
        background-color: #25D366; color: white !important; padding: 12px 25px; 
        border-radius: 5px; text-decoration: none; display: block; text-align: center; font-weight: bold;
    }
    .footer-seals { position: fixed; bottom: 15px; left: 15px; display: flex; align-items: center; gap: 10px; opacity: 0.7; }
</style>
""", unsafe_allow_html=True)

# 3. AUTENTICAÇÃO
if 'auth' not in st.session_state:
    st.session_state['auth'] = False

if not st.session_state['auth']:
    st.markdown("<h2 style='text-align:center; color:#BFAF83; font-family: \"Playfair Display\", serif; margin-top: 100px;'>ACESSO RESTRITO</h2>", unsafe_allow_html=True)
    
    col_espaco1, col_login, col_espaco2 = st.columns([1, 1, 1])
    with col_login:
        user = st.text_input("Usuário")
        pw = st.text_input("Senha", type="password")
        if st.button("Entrar", use_container_width=True):
            if user == "edson.senabr@gmail.com" and pw == "Roberta123":
                st.session_state['auth'] = True
                st.rerun()
            else:
                st.error("Credenciais Inválidas")
    st.stop()

# 4. CONTEÚDO PRINCIPAL
st.markdown('<h1 class="main-title">Consultoria de Ativos</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">AUDITORIA TÉCNICA DE EXTRATOS</p>', unsafe_allow_html=True)

col1, col2 = st.columns([4, 1])
with col2:
    st.markdown('<a href="https://contate.me/5592995087379" class="btn-whatsapp" target="_blank">Falar com Consultor ⚖️</a>', unsafe_allow_html=True)

# 5. PARÂMETROS DE BUSCA (A Barra Lateral que você precisava)
st.sidebar.markdown("<h3 style='color: #BFAF83;'>FILTROS</h3>", unsafe_allow_html=True)
DICIONARIO = {
    "Cesta / Pacote": "CESTA|PACOTE",
    "Tarifas Bancárias": "TARIFA BANCARIA",
    "Mora / Juros": "MORA|JUROS",
    "Seguro": "SEGURO",
    "Baixas (BX)": r"\bBX\b",
    "Anuidade": "ANUIDADE"
}

# Cria as caixas de seleção na barra esquerda
selecionados = {}
for nome, termo in DICIONARIO.items():
    if st.sidebar.checkbox(nome, value=True):
        selecionados[nome] = termo

# 6. PROCESSAMENTO DO PDF (O seu bloco original intacto)
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
                            for nome, termo in selecionados.items():
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

# 7. SELOS (Simplificados para não travar o carregamento)
st.markdown("""
<div class="footer-seals">
    <img src="https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_92x30dp.png" width="40">
    <span style="font-size: 10px; color: #94A3B8; font-weight: bold;">SITE PROTEGIDO</span>
</div>
""", unsafe_allow_html=True)
