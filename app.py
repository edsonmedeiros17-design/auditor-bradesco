import streamlit as st
import pdfplumber
import pandas as pd
import re

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Auditoria Premium | Edson Medeiros", layout="wide")

# --- CSS CUSTOMIZADO: QUIET LUXURY REFINADO ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;500;600&family=Great+Vibes&display=swap');

    /* Variáveis de Cores e Estilo */
    :root {
        --navy-prime: #001F3F;
        --off-white: #F8F4E6;
        --cinza-chumbo: #2C3E50;
        --cinza-hover: #34495E;
        --bege-fendi: #D2B48C;
        --dourado-matte: #BFAF83;
        --text-main: #2C3E50;
    }

    /* Reset e Fundo Principal */
    .stApp {
        background-color: var(--off-white);
        font-family: 'Inter', sans-serif;
    }

    /* SIDEBAR: CORREÇÃO DE LEGIBILIDADE PRIORITÁRIA */
    section[data-testid="stSidebar"] {
        background-color: var(--cinza-chumbo) !important;
        width: 280px !important;
        padding: 24px 10px;
        border-right: 1px solid var(--bege-fendi);
    }

    /* Texto do Sidebar (Contraste > 7:1) */
    section[data-testid="stSidebar"] .stMarkdown p, 
    section[data-testid="stSidebar"] label {
        color: #FFFFFF !important;
        font-weight: 500 !important;
        font-family: 'Inter', sans-serif;
        font-size: 0.95rem;
    }

    /* Estilização das Checkboxes no Sidebar */
    div[data-testid="stCheckbox"] {
        background-color: transparent;
        padding: 8px 12px;
        border-radius: 8px;
        transition: all 0.3s ease;
        margin-bottom: 4px;
    }

    div[data-testid="stCheckbox"]:hover {
        background-color: var(--cinza-hover);
        transform: scale(1.02);
    }

    /* Ícone da Checkbox (Checkmark) */
    div[data-testid="stCheckbox"] [data-testid="stWidgetLabel"] span {
        color: #FFFFFF !important;
    }

    /* TÍTULOS */
    h1 {
        font-family: 'Playfair Display', serif !important;
        color: var(--navy-prime) !important;
        font-size: 2.8rem !important;
        padding-bottom: 0;
    }

    /* CARDS E DATASET (BANCO SUÍÇO) */
    div[data-testid="stDataFrame"] {
        background-color: #FFFFFF;
        border: 1px solid var(--bege-fendi);
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.08);
        padding: 15px;
        transition: transform 0.3s ease;
    }
    
    div[data-testid="stDataFrame"]:hover {
        transform: scale(1.01);
    }

    /* BOTÃO DE UPLOAD COM GRADIENTE */
    section[data-testid="stFileUploadDropzone"] {
        border: 2px dashed var(--bege-fendi) !important;
        border-radius: 12px;
        background: linear-gradient(145deg, #ffffff, #F5F5DC);
    }

    /* FOOTER BRANDING SUTIL */
    .footer {
        position: fixed;
        bottom: 20px;
        right: 30px;
        text-align: right;
        z-index: 100;
    }
    
    .footer-line {
        border-top: 1px solid var(--bege-fendi);
        width: 120px;
        margin-left: auto;
        margin-bottom: 8px;
        opacity: 0.6;
    }
    
    .footer-text {
        font-family: 'Great Vibes', cursive;
        color: var(--dourado-matte);
        font-size: 1.3rem;
        letter-spacing: 1px;
    }

    /* Animação Fade-in */
    .main .block-container {
        animation: fadeIn 0.6s ease-out;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    </style>
    """, unsafe_allow_html=True)

# --- HEADER ---
st.title("Auditoria de Ativos")
st.markdown(f"<p style='color: #5D6D7E; font-size: 1.1rem; margin-top:-15px;'>Inteligência em Leitura de Extratos Bancários</p>", unsafe_allow_html=True)

# --- SIDEBAR (CHECKBOXES) ---
st.sidebar.markdown("### Tipos de Descontos")

DICIONARIO_ALVOS = {
    "Mora Crédito Pessoal": "MORA CREDITO PESSOAL",
    "Encargos": "ENCARGOS",
    "Parcela Crédito Pessoal": "PARCELA CREDITO PESSOAL",
    "Gastos Cartão de Crédito": "GASTOS CARTAO DE CREDITO",
    "BX (Baixas)": r"\bBX\b",
    "APLIC (Aplicações)": r"\bAPLIC\b",
    "Tarifa Bancária": "TARIFA BANCARIA",
    "Anuidade Cartão": "CARTAO CREDITO ANUIDADE"
}

selecionados_nomes = []
for nome_amigavel in DICIONARIO_ALVOS.keys():
    if st.sidebar.checkbox(nome_amigavel, value=True):
        selecionados_nomes.append(nome_amigavel)

# --- LÓGICA DE PROCESSAMENTO ---
def analisar_extrato(file, filtros):
    dados = []
    termos = [DICIONARIO_ALVOS[f] for f in filtros]
    with pdfplumber.open(file) as pdf:
        for p in pdf.pages:
            texto = p.extract_text()
            if texto:
                for linha in texto.split('\n'):
                    for termo in termos:
                        if re.search(termo, linha, re.IGNORECASE):
                            data_match = re.search(r'(\d{2}/\d{2}/\d{4})', linha)
                            dados.append({
                                "Data": data_match.group(1) if data_match else "---",
                                "Categoria": [k for k, v in DICIONARIO_ALVOS.items() if v == termo][0],
                                "Lançamento": linha.strip()
                            })
                            break
    return pd.DataFrame(dados)

# --- ÁREA DE UPLOAD ---
st.markdown("<br>", unsafe_allow_html=True)
upload = st.file_uploader("", type="pdf", help="Arraste o extrato original em formato PDF")

if upload:
    if not selecionados_nomes:
        st.warning("Selecione os parâmetros de busca no menu lateral.")
    else:
        with st.spinner('Realizando leitura técnica...'):
            df = analisar_extrato(upload, selecionados_nomes)
            if not df.empty:
                st.success(f"Análise finalizada: {len(df)} registros identificados.")
                st.dataframe(df, use_container_width=True)
                
                # Botão de Exportação Elegante
                csv = df.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="BAIXAR RELATÓRIO DE AUDITORIA",
                    data=csv,
                    file_name=f"auditoria_{upload.name}.csv",
                    mime="text/csv"
                )
            else:
                st.info("Nenhuma ocorrência encontrada para os filtros aplicados.")

# --- FOOTER ---
st.markdown("""
    <div class="footer">
        <div class="footer-line"></div>
        <div class="footer-text">Fundado por Edson Medeiros</div>
    </div>
    """, unsafe_allow_html=True)
