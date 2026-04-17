import streamlit as st
import pdfplumber
import pandas as pd
import re

# --- 1. CONFIGURAÇÃO DE ELITE ---
st.set_page_config(
    page_title="Edson Medeiros | Consultoria de Ativos", 
    layout="wide", 
    page_icon="⚖️"
)

# --- 2. CSS CUSTOMIZADO (DESIGN QUIET LUXURY & 3D) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600&family=Playfair+Display:ital,wght@0,700;1,700&family=Inter:wght@300;400;600&family=Great+Vibes&display=swap');

    :root {
        --navy-deep: #0F172A;
        --gold-matte: #BFAF83;
        --off-white: #F8F9FA;
    }

    .stApp { 
        background: radial-gradient(circle at center, #1E293B 0%, #0F172A 100%); 
        color: var(--off-white);
        font-family: 'Inter', sans-serif;
    }

    .consultoria-title {
        font-family: 'Playfair Display', serif !important;
        font-size: 4.5rem !important;
        font-weight: 700 !important;
        background: linear-gradient(180deg, #FFFFFF 0%, #BFAF83 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0px 2px 0px #8A7650, 0px 4px 10px rgba(0,0,0,0.5);
        line-height: 1.1;
    }

    .btn-whatsapp {
        background-color: #25D366 !important;
        color: white !important;
        padding: 14px 28px !important;
        border-radius: 50px !important;
        text-decoration: none !important;
        font-weight: bold !important;
        display: inline-block !important;
        box-shadow: 0 4px 15px rgba(37, 211, 102, 0.4) !important;
        text-align: center;
    }

    .login-box {
        background: rgba(255, 255, 255, 0.05);
        padding: 40px;
        border-radius: 16px;
        border: 1px solid rgba(191, 175, 131, 0.2);
        max-width: 400px;
        margin: auto;
    }

    .footer-signature {
        position: fixed;
        bottom: 30px;
        right: 40px;
        text-align: right;
    }
    .footer-name { font-family: 'Great Vibes', cursive; color: var(--gold-matte); font-size: 2.2rem; margin: 0; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SISTEMA DE LOGIN ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    st.markdown("<br><br>", unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.markdown('<h2 style="color: #BFAF83; font-family: \'Cinzel\'; text-align: center;">ACESSO RESTRITO</h2>', unsafe_allow_html=True)
        
        user_input = st.text_input("E-mail de Acesso")
        pass_input = st.text_input("Senha Técnica", type="password")
        
        if st.button("ENTRAR NO SISTEMA"):
            if user_input == "edson.senabr@gmail.com" and pass_input == "Edsonsena14":
                st.session_state['authenticated'] = True
                st.rerun()
            else:
                st.error("Credenciais inválidas. Entre em contato com o consultor.")
        
        st.markdown("<br><hr style='opacity: 0.1;'><br>", unsafe_allow_html=True)
        st.markdown('<p style="text-align: center; font-size: 0.8rem; color: #64748B;">Ainda não possui acesso?</p>', unsafe_allow_html=True)
        st.markdown(f'<div style="text-align: center;"><a href="https://contate.me/5592995087379" class="btn-whatsapp" target="_blank">Falar com Consultor ⚖️</a></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- 4. MODELO PRINCIPAL (APÓS LOGIN) ---
col_head, col_cta = st.columns([2.5, 1])

with col_head:
    st.markdown('<h1 class="consultoria-title">Consultoria de Ativos</h1>', unsafe_allow_html=True)
    st.markdown("<p style='color: #BFAF83; letter-spacing: 2px; font-weight: 300;'>AUDITORIA TÉCNICA PROPRIETÁRIA DE EXTRATOS</p>", unsafe_allow_html=True)

with col_cta:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(f'<a href="https://contate.me/5592995087379" class="btn-whatsapp" target="_blank">Falar com Consultor ⚖️</a>', unsafe_allow_html=True)

# ... (Manutenção do dicionário de busca e lógica de processamento) ...
st.sidebar.markdown("### PARÂMETROS DE BUSCA")
DICIONARIO_ALVOS = {
    "Tarifas Bancárias": "TARIFA BANCARIA",
    "Seguros / Previdência": "SEGURO",
    "Mora / Encargos": "MORA",
    "Capitalização": "CAPITALIZACAO",
    "Pacote de Serviços": "PACOTE DE SERVICOS",
    "Taxas de Adiantamento": "ADIANT",
    "Baixas e Débitos (BX)": r"\bBX\b"
}
selecionados = [nome for nome in DICIONARIO_ALVOS.keys() if st.sidebar.checkbox(nome, value=True)]

st.markdown("<br>", unsafe_allow_html=True)
upload = st.file_uploader("Submeta o arquivo PDF para certificação automática", type="pdf")

if upload and selecionados:
    with st.spinner('Realizando cruzamento técnico...'):
        dados = []
        termos = [DICIONARIO_ALVOS[f] for f in selecionados]
        with pdfplumber.open(upload) as pdf:
            for p in pdf.pages:
                texto = p.extract_text()
                if texto:
                    for linha in texto.split('\n'):
                        for t in termos:
                            if re.search(t, linha, re.IGNORECASE):
                                data_m = re.search(r'(\d{2}/\d{2}/\d{4})', linha)
                                dados.append({
                                    "DATA": data_m.group(1) if data_m else "---",
                                    "CATEGORIA": [k for k, v in DICIONARIO_ALVOS.items() if v == t][0].upper(),
                                    "DESCRIÇÃO TÉCNICA": linha.strip()
                                })
                                break
        
        df = pd.DataFrame(dados)
        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 BAIXAR RELATÓRIO CERTIFICADO (CSV)", csv, "auditoria_medeiros.csv", "text/csv")

# --- 5. RODAPÉ ---
st.markdown(f"""
    <div class="footer-signature">
        <p class="footer-name">Edson Medeiros</p>
        <p style="font-family: 'Inter', sans-serif; font-size: 0.7rem; color: #64748B; letter-spacing: 3px;">CONSULTORIA & COMPLIANCE</p>
    </div>
    """, unsafe_allow_html=True)
