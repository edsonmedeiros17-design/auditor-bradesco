import streamlit as st
import pdfplumber
import pandas as pd
import re

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Auditoria Premium", layout="wide")

# --- CSS CUSTOMIZADO: QUIET LUXURY & MINIMALISMO ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Inter:wght@300;400&family=Great+Vibes&display=swap');

    /* Reset Geral para Tipografia Serif */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #2C3E50;
        background-color: #F8F4E6;
    }
    
    h1, h2, h3 {
        font-family: 'Playfair Display', serif !important;
        color: #001F3F !self !important;
        font-weight: 700;
        letter-spacing: -0.5px;
    }

    /* Barra Lateral Minimalista */
    [data-testid="stSidebar"] {
        background-color: #F5F5DC;
        border-right: 1px solid #D2B48C;
    }
    
    /* Botões Premium */
    .stButton>button {
        background-color: #001F3F;
        color: #F8F4E6;
        border-radius: 4px;
        border: none;
        padding: 0.5rem 2rem;
        transition: all 0.3s ease;
        font-family: 'Inter', sans-serif;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-size: 0.8rem;
    }
    
    .stButton>button:hover {
        background-color: #BFAF83;
        color: #001F3F;
        transform: translateY(-2px);
    }

    /* Cards de Resultados Estilo Banco Suíço */
    div[data-testid="stDataFrame"] {
        background-color: #FFFFFF;
        border: 1px solid #D2B48C;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        padding: 10px;
    }

    /* Footer Elegante */
    .footer {
        position: fixed;
        bottom: 20px;
        right: 30px;
        text-align: right;
    }
    
    .footer-line {
        border-top: 0.5px solid #D2B48C;
        width: 150px;
        margin-bottom: 5px;
        margin-left: auto;
    }
    
    .footer-text {
        font-family: 'Great Vibes', cursive;
        color: #BFAF83;
        font-size: 1.2rem;
    }

    /* Fade-in Animation */
    .main .block-container {
        animation: fadeIn 0.8s ease-in;
    }
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- TÍTULO E SUBTITULO ---
st.title("Auditoria de Ativos")
st.markdown("<p style='color: #A8A29E; font-style: italic;'>Relatórios de Precisão Bancária</p>", unsafe_allow_html=True)
st.write("---")

# --- DICIONÁRIO DE FILTROS ---
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

# --- BARRA LATERAL (CHECKBOXES) ---
st.sidebar.markdown("### Filtros Seletivos")
selecionados_nomes = []

for nome_amigavel in DICIONARIO_ALVOS.keys():
    if st.sidebar.checkbox(nome_amigavel, value=True):
        selecionados_nomes.append(nome_amigavel)

# --- LOGICA DE PROCESSAMENTO ---
def processar_pdf(arquivo_pdf, filtros_escolhidos):
    dados_encontrados = []
    termos_busca = [DICIONARIO_ALVOS[nome] for nome in filtros_escolhidos]
    
    with pdfplumber.open(arquivo_pdf) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if texto:
                linhas = texto.split('\n')
                for linha in linhas:
                    for termo in termos_busca:
                        if re.search(termo, linha, re.IGNORECASE):
                            data_match = re.search(r'(\d{2}/\d{2}/\d{4})', linha)
                            data = data_match.group(1) if data_match else "---"
                            dados_encontrados.append({
                                "Data": data,
                                "Categoria": [k for k, v in DICIONARIO_ALVOS.items() if v == termo][0],
                                "Lançamento": linha.strip()
                            })
                            break
    return pd.DataFrame(dados_encontrados)

# --- ÁREA CENTRAL ---
upload = st.file_uploader("Deposite o extrato em formato PDF", type="pdf")

if upload:
    if not selecionados_nomes:
        st.warning("Selecione os parâmetros de busca.")
    else:
        df_final = processar_pdf(upload, selecionados_nomes)
        
        if not df_final.empty:
            st.success(f"Análise Completa: {len(df_final)} ocorrências.")
            # DataFrame formatado com o estilo Premium do CSS
            st.dataframe(df_final, use_container_width=True)
            
            # Botão de Download
            csv = df_final.to_csv(index=False).encode('utf-8-sig')
            st.download_button("Exportar Relatório", csv, "auditoria_premium.csv")
        else:
            st.info("Nenhuma divergência identificada.")

# --- FOOTER BRANDING ---
st.markdown("""
    <div class="footer">
        <div class="footer-line"></div>
        <div class="footer-text">Fundado por Edson Medeiros</div>
    </div>
    """, unsafe_allow_html=True)
