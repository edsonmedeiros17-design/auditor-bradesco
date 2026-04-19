import streamlit as st
import pdfplumber
import pandas as pd
import re

# 1. CONFIGURAÇÃO E VALIDAÇÃO OCULTA (GOOGLE)
st.set_page_config(page_title="Edson Medeiros | Consultoria", layout="wide")
st.markdown(f'<div style="display:none;">google-site-verification: u-8Cv23oI8_QCuHNzQA-Vwqffb58GtwXEWc7jBYJFcQ</div>', unsafe_allow_html=True)

# 2. RESTAURAÇÃO DA ESTÉTICA E DESIGN
st.markdown("""
<style>
    .stApp { background-color: #0F172A; color: white; }
    .main-title { color: #BFAF83; font-size: 3rem; font-weight: bold; text-align: center; margin-bottom: 0px; }
    .subtitle { color: #94A3B8; text-align: center; font-size: 1.2rem; margin-bottom: 40px; }
    
    /* Botão WhatsApp Estilizado */
    .btn-whatsapp {
        background-color: #25D366; color: white !important;
        padding: 12px 25px; border-radius: 30px;
        text-decoration: none; font-weight: bold;
        display: inline-block; transition: 0.3s;
    }
    .btn-whatsapp:hover { background-color: #128C7E; transform: scale(1.05); }

    /* Selos de Segurança Sofisticados (Rodapé) */
    .footer-security {
        position: fixed; left: 20px; bottom: 20px;
        display: flex; align-items: center; gap: 15px;
        padding: 10px 15px; background: rgba(255, 255, 255, 0.03);
        border-radius: 8px; border-left: 2px solid #BFAF83; z-index: 999;
    }
    .footer-text { font-size: 10px; color: #94A3B8; line-height: 1.2; text-transform: uppercase; }
    .footer-icon { filter: grayscale(100%); opacity: 0.6; }
</style>
""", unsafe_allow_html=True)

# 3. CONTROLE DE ACESSO
if 'auth' not in st.session_state:
    st.session_state['auth'] = False

if not st.session_state['auth']:
    st.markdown('<h1 class="main-title">CONSULTORIA MEDEIROS</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">SISTEMA PRIVADO DE AUDITORIA DE ATIVOS</p>', unsafe_allow_html=True)
    
    _, col_login, _ = st.columns([1, 1, 1])
    with col_login:
        user = st.text_input("Usuário")
        pw = st.text_input("Senha", type="password")
        if st.button("ACESSAR SISTEMA", use_container_width=True):
            if user == "edson.senabr@gmail.com" and pw == "Roberta123":
                st.session_state['auth'] = True
                st.rerun()
            else:
                st.error("Credenciais Inválidas")
    
    # Selos na tela de login
    st.markdown("""
    <div class="footer-security">
        <img src="https://img.icons8.com/color/48/google-logo.png" width="20" class="footer-icon">
        <img src="https://img.icons8.com/shield-check-mark" width="22" style="filter: invert(80%);" class="footer-icon">
        <div class="footer-text"><b>Ambiente Seguro</b><br>Criptografia SSL & Google Safe</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# 4. INTERFACE PRINCIPAL (RESTAURADA)
st.markdown('<h1 class="main-title">Relatório de Auditoria</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Análise Técnica de Irregularidades Bancárias</p>', unsafe_allow_html=True)

col_info, col_btn = st.columns([3, 1])
with col_btn:
    st.markdown('<a href="https://contate.me/5592995087379" class="btn-whatsapp">Falar com Consultor ⚖️</a>', unsafe_allow_html=True)

# DICIONÁRIO DE BUSCA (SUA INTELIGÊNCIA DE NEGÓCIO)
DICIONARIO = {
    "Cesta / Pacote": "CESTA|PACOTE|MENSALIDADE",
    "Tarifas": "TARIFA BANCARIA|TAR BANC",
    "Seguros": "SEGURO|PROT",
    "Juros/Mora": "MORA|JUROS|MULTA"
}

upload = st.file_uploader("Arraste o extrato PDF aqui", type="pdf")

if upload:
    with st.spinner('Analisando extrato...'):
        dados = []
        try:
            with pdfplumber.open(upload) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        for linha in text.split('\n'):
                            for nome, termo in DICIONARIO.items():
                                if re.search(termo, linha, re.IGNORECASE):
                                    # Captura o valor financeiro (ex: 1.250,00)
                                    valor = re.findall(r'(\d[\d\.]*,\d{2})', linha)
                                    valor_f = valor[-1] if valor else "0,00"
                                    dados.append({
                                        "DATA": "Ver extrato",
                                        "CATEGORIA": nome,
                                        "DESCRIÇÃO": linha[:80],
                                        "VALOR (R$)": valor_f
                                    })
            
            if dados:
                df = pd.DataFrame(dados)
                st.success(f"Foram encontradas {len(df)} possíveis irregularidades.")
                st.dataframe(df, use_container_width=True)
                
                csv = df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 BAIXAR LAUDO TÉCNICO (CSV)", csv, "laudo_auditoria.csv", "text/csv")
            else:
                st.warning("Nenhum termo de irregularidade foi encontrado neste documento.")
        except Exception as e:
            st.error(f"Erro no processamento: {e}")

# Selos também na área logada para manter a confiança
st.markdown("""
<div class="footer-security">
    <img src="https://img.icons8.com/color/48/google-logo.png" width="20" class="footer-icon">
    <img src="https://img.icons8.com/shield-check-mark" width="22" style="filter: invert(80%);" class="footer-icon">
    <div class="footer-text"><b>Sistema Protegido</b><br>Monitoramento Ativo</div>
</div>
""", unsafe_allow_html=True)
