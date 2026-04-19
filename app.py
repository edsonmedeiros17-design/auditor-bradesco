import streamlit as st
import pdfplumber
import pandas as pd
import re

# 1. CONFIGURAÇÃO DA PÁGINA E VALIDAÇÃO GOOGLE (OCULTA)
st.set_page_config(page_title="Edson Medeiros | Consultoria", layout="wide")
st.markdown(f'<div style="display:none;">google-site-verification: u-8Cv23oI8_QCuHNzQA-Vwqffb58GtwXEWc7jBYJFcQ</div>', unsafe_allow_html=True)

# 2. ESTILO CSS PARA RECUPERAR A APARÊNCIA ORIGINAL
st.markdown("""
<style>
    .stApp { background-color: #0F172A; color: white; }
    .main-title { color: #BFAF83; font-size: 3rem; font-weight: bold; text-align: center; margin-bottom: 5px; }
    .subtitle { color: #94A3B8; text-align: center; font-size: 1.1rem; margin-bottom: 40px; }
    
    /* Botão WhatsApp */
    .btn-whatsapp { 
        background-color: #25D366; color: white !important; padding: 12px 25px; 
        border-radius: 30px; text-decoration: none; font-weight: bold;
        float: right; transition: 0.3s;
    }
    
    /* Selos de Segurança no Canto Inferior Esquerdo */
    .footer-security {
        position: fixed; left: 20px; bottom: 20px;
        display: flex; align-items: center; gap: 12px;
        padding: 8px 15px; background: rgba(255, 255, 255, 0.05);
        border-radius: 8px; border: 1px solid rgba(191,175,131,0.2); z-index: 999;
    }
    .footer-text { font-size: 9px; color: #94A3B8; line-height: 1.1; text-transform: uppercase; }
</style>
""", unsafe_allow_html=True)

# 3. AUTENTICAÇÃO
if 'auth' not in st.session_state:
    st.session_state['auth'] = False

if not st.session_state['auth']:
    st.markdown('<h1 class="main-title">CONSULTORIA MEDEIROS</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">SISTEMA PRIVADO DE AUDITORIA</p>', unsafe_allow_html=True)
    _, col_login, _ = st.columns([1, 1, 1])
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

# 4. CONTEÚDO PRINCIPAL (RESTAURADO)
st.markdown('<a href="https://contate.me/5592995087379" class="btn-whatsapp">Falar com Consultor ⚖️</a>', unsafe_allow_html=True)
st.markdown('<h1 class="main-title">Relatório de Auditoria</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Análise Técnica de Irregularidades Bancárias</p>', unsafe_allow_html=True)

# BARRA DE SELEÇÃO DE DÉBITOS (A QUE ESTAVA FALTANDO)
st.markdown("### Selecione os Débitos para Análise")
DICIONARIO = {
    "Cesta / Pacote": "CESTA|PACOTE|MENSALIDADE",
    "Tarifas Bancárias": "TARIFA BANCARIA|TAR BANC",
    "Mora / Juros": "MORA|JUROS|MULTA",
    "Seguro": "SEGURO|PROT"
}
selecionados = st.multiselect("Selecione os termos de busca:", list(DICIONARIO.keys()), default=list(DICIONARIO.keys()))

upload = st.file_uploader("Submeta o arquivo PDF aqui", type="pdf")

if upload:
    with st.spinner('Analisando documento...'):
        dados = []
        try:
            with pdfplumber.open(upload) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        for linha in text.split('\n'):
                            for nome in selecionados:
                                termo = DICIONARIO[nome]
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
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                csv = df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 BAIXAR LAUDO TÉCNICO", csv, "laudo_auditoria.csv", "text/csv")
            else:
                st.info("Nenhuma irregularidade encontrada para os débitos selecionados.")
        except Exception as e:
            st.error(f"Erro ao ler PDF: {e}")

# 5. RODAPÉ DE SEGURANÇA (SELOS DISCRETOS NO CANTO ESQUERDO)
st.markdown("""
<div class="footer-security">
    <img src="https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_92x30dp.png" width="35" style="opacity:0.8;">
    <img src="https://img.icons8.com/shield-check-mark" width="20" style="filter: invert(80%); opacity:0.7;">
    <div class="footer-text"><b>Ambiente Seguro</b><br>Google Safe & SSL Ativo</div>
</div>
""", unsafe_allow_html=True)
