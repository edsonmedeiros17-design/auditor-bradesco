import streamlit as st
import pdfplumber
import pandas as pd
import re

# --- CONFIGURAÇÃO DE ESTADO E PÁGINA ---
st.set_page_config(page_title="Edson Medeiros | Auditoria de Ativos", layout="wide", page_icon="🏦")

# --- CSS QUIET LUXURY (REFINAMENTO FINAL) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;800&family=Playfair+Display:ital,wght@0,700;1,700&family=Inter:wght@300;400;600&family=Great+Vibes&display=swap');

    :root {
        --navy-dark: #0F172A;
        --emerald-matte: #1A5F3A;
        --gold-label: #BFAF83;
        --off-white: #F8F9FA;
    }

    .stApp { background-color: var(--navy-dark); color: var(--off-white); font-family: 'Inter', sans-serif; }

    /* NÚMERO 1: FONTE SOFISTICADA (ESTILO TIMES ROMAN DE LUXO) */
    .hero-title {
        font-family: 'Playfair Display', serif !important;
        font-size: 4.5rem !important;
        font-weight: 700 !important;
        background: linear-gradient(135deg, #FFF 30%, #BFAF83 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 2px 4px 8px rgba(0,0,0,0.5); /* Efeito 3D sutil */
        line-height: 1.1;
        margin-bottom: 10px;
    }

    /* NÚMERO 2: FRASE DE CONFIANÇA */
    .trust-subtitle {
        font-family: 'Inter', sans-serif;
        color: #94A3B8;
        font-size: 1.2rem;
        letter-spacing: 0.5px;
        max-width: 700px;
        border-left: 3px solid var(--emerald-matte);
        padding-left: 20px;
        margin: 20px 0 40px 0;
    }

    /* BARRA LATERAL (FILTROS) - RECUPERADA E VISÍVEL */
    [data-testid="stSidebar"] {
        background-color: #080C14 !important;
        border-right: 1px solid rgba(191, 175, 131, 0.2);
    }
    [data-testid="stSidebar"] h3 { color: var(--gold-label) !important; font-family: 'Cinzel', serif; font-size: 0.9rem !important; }

    /* ÁREA DE UPLOAD (EM DESTAQUE) */
    .upload-box {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(191, 175, 131, 0.3);
        border-radius: 16px;
        padding: 40px;
        transition: 0.3s ease;
    }
    .upload-box:hover { border-color: var(--emerald-matte); background: rgba(26, 95, 58, 0.05); }

    /* NÚMERO 3: ASSINATURA EDSON MEDEIROS (PADRÃO SOLICITADO) */
    .footer-signature {
        position: fixed;
        bottom: 30px;
        right: 40px;
        text-align: right;
    }
    .footer-name { font-family: 'Great Vibes', cursive; color: var(--gold-label); font-size: 1.8rem; margin: 0; }
    .footer-tech { font-family: 'Inter', sans-serif; font-size: 0.65rem; color: #64748B; letter-spacing: 3px; text-transform: uppercase; }

    /* ESTILO DA TABELA */
    div[data-testid="stDataFrame"] { background: #1E293B; border-radius: 8px; padding: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR: CONTROLE DE DESCONTOS (RECUPERADO) ---
st.sidebar.markdown("### FILTROS DE AUDITORIA")
DICIONARIO_ALVOS = {
    "Tarifa Bancária": "TARIFA BANCARIA",
    "Mora Crédito Pessoal": "MORA CREDITO PESSOAL",
    "Encargos": "ENCARGOS",
    "Seguros": "SEGURO",
    "Título de Capitalização": "TITULO DE CAPITALIZACAO",
    "Pacote de Serviços": "PACOTE DE SERVIÇOS",
    "BX (Baixas)": r"\bBX\b",
    "Adiantamento (ADIANT)": "ADIANT",
    "Parcelas Vencidas": "VENCIDAS"
}
selecionados = []
for nome in DICIONARIO_ALVOS.keys():
    if st.sidebar.checkbox(nome.upper(), value=True):
        selecionados.append(nome)

# --- HERO SECTION ---
st.markdown('<h1 class="hero-title">Robô Leitor <br> de Extratos</h1>', unsafe_allow_html=True)
st.markdown('<p class="trust-subtitle">Tecnologia de auditoria proprietária: transparência total e segurança jurídica em cada lançamento analisado.</p>', unsafe_allow_html=True)

# --- ÁREA DE UPLOAD EM DESTAQUE ---
st.markdown('<div class="upload-box">', unsafe_allow_html=True)
upload = st.file_uploader("Arraste o extrato PDF aqui para iniciar a análise inteligente", type="pdf")
st.markdown('</div>', unsafe_allow_html=True)

# --- PROCESSAMENTO ---
if upload and selecionados:
    with st.spinner('Auditando dados com precisão...'):
        dados = []
        termos = [DICIONARIO_ALVOS[f] for f in selecionados]
        with pdfplumber.open(upload) as pdf:
            for p in pdf.pages:
                texto = p.extract_text()
                if texto:
                    for linha in texto.split('\n'):
                        for t in termos:
                            if re.search(t, linha, re.IGNORECASE):
                                data_match = re.search(r'(\d{2}/\d{2}/\d{4})', linha)
                                dados.append({
                                    "DATA": data_match.group(1) if data_match else "---",
                                    "CATEGORIA": [k for k, v in DICIONARIO_ALVOS.items() if v == t][0].upper(),
                                    "DESCRIÇÃO": linha.strip()
                                })
                                break
        
        df = pd.DataFrame(dados)
        if not df.empty:
            st.markdown("<br>", unsafe_allow_html=True)
            st.dataframe(df, use_container_width=True, hide_index=True)
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("EXPORTAR RELATÓRIO PDF/CSV", csv, "auditoria_oficial.csv", "text/csv")
        else:
            st.info("Nenhum registro encontrado para os filtros selecionados.")

# --- FOOTER (NÚMERO 3: MANTIDO PADRÃO) ---
st.markdown(f"""
    <div class="footer-signature">
        <p class="footer-name">Edson Medeiros</p>
        <p class="footer-tech">PROPRIETARY AUDIT TECHNOLOGY</p>
    </div>
    """, unsafe_allow_html=True)
