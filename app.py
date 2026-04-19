import streamlit as st
import pdfplumber
import pandas as pd
import re

# 1. CONFIGURAÇÃO DA PÁGINA E VALIDAÇÃO GOOGLE
st.set_page_config(page_title="Edson Medeiros | Consultoria", layout="wide")

# Tag de verificação oculta para o Google Search Console
st.markdown(f'<div style="display:none;">google-site-verification: u-8Cv23oI8_QCuHNzQA-Vwqffb58GtwXEWc7jBYJFcQ</div>', unsafe_allow_html=True)

# 2. ESTILO CSS (RODAPÉ ADICIONADO)
st.markdown("""
<style>
    .stApp { background-color: #0F172A; color: white; }
    .main-title { color: #BFAF83; font-size: 3rem; font-weight: bold; text-align: center; }
    .btn-whatsapp { 
        background-color: #25D366; color: white; padding: 15px; 
        border-radius: 10px; text-decoration: none; display: block; text-align: center;
    }
    /* Estilo para os selos no rodapé */
    .footer-security {
        position: fixed; left: 20px; bottom: 20px;
        display: flex; align-items: center; gap: 15px;
        padding: 8px 15px; background: rgba(255, 255, 255, 0.05);
        border-radius: 8px; border-left: 2px solid #BFAF83; z-index: 999;
    }
    .footer-text { font-size: 10px; color: #94A3B8; line-height: 1.2; text-transform: uppercase; }
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
    
    # Exibe selos também na tela de login
    st.markdown("""
    <div class="footer-security">
        <img src="https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_92x30dp.png" width="35" style="opacity:0.8;">
        <img src="https://img.icons8.com/shield-check-mark" width="20" style="filter: invert(80%); opacity:0.8;">
        <div class="footer-text"><b>Ambiente Seguro</b><br>Google Safe Browsing & SSL</div>
    </div>
    """, unsafe_allow_html=True)
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

# Selos no rodapé da área interna
st.markdown("""
<div class="footer-security">
    <img src="https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_92x30dp.png" width="35" style="opacity:0.8;">
    <img src="https://img.icons8.com/shield-check-mark" width="20" style="filter: invert(80%); opacity:0.8;">
    <div class="footer-text"><b>Sistema Protegido</b><br>Verificação Google Ativa</div>
</div>
""", unsafe_allow_html=True)
