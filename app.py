import streamlit as st
import pdfplumber
import pandas as pd
import re
import PIL.Image as PILImage
import PIL.ImageOps as PILOps
import pytesseract

# --- 1. CONFIGURAÇÃO E ESTÉTICA ---
st.set_page_config(page_title="Edson Medeiros | Consultoria", layout="wide", page_icon="⚖️")

ESTILO_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600&family=Playfair+Display:wght@700&family=Inter:wght@300;400;600&family=Great+Vibes&display=swap');
:root { --navy: #0F172A; --gold: #BFAF83; }
.stApp { background: radial-gradient(circle, #1E293B 0%, #0F172A 100%); color: #F8F9FA; font-family: 'Inter', sans-serif; }
.consultoria-title { 
    font-family: 'Playfair Display', serif; font-size: 4rem; 
    background: linear-gradient(180deg, #FFFFFF, #BFAF83); 
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
    text-shadow: 0px 4px 10px rgba(0,0,0,0.5); text-align: center;
}
.footer-name { font-family: 'Great Vibes', cursive; color: var(--gold); font-size: 2.2rem; text-align: right; }
</style>
"""
st.markdown(ESTILO_CSS, unsafe_allow_html=True)

# --- 2. MOTOR DE PRECISÃO POR COLUNA (DÉBITO vs SALDO) ---
def extrair_valor_debito_real(linha_texto):
    """
    Lógica: Ignora números sem vírgula (Docto) e o último número com vírgula (Saldo).
    O alvo é o valor de Débito, que fica entre a descrição e o saldo.
    """
    # 1. Busca Data
    match_data = re.search(r'(\d{2}/\d{2}(?:/\d{2,4})?)', linha_texto)
    data = match_data.group(1) if match_data else "---"
    
    # 2. Busca todos os valores monetários (com vírgula)
    # Exemplo na linha: "MORA CRED PESS 5070009 116,11 131,82"
    # matches_valor resultaria em ['116,11', '131,82']
    padrao_valor = r'\d{1,3}(?:\.\d{3})*,\d{2}|\d+,\d{2}'
    matches_valor = re.findall(padrao_valor, linha_texto)
    
    valor_debito = "0,00"
    
    if len(matches_valor) >= 2:
        # Se temos 2 ou mais valores, o primeiro é o Débito e o último é o Saldo.
        # Pegamos o index 0 para garantir que é o DÉBITO.
        valor_debito = matches_valor[0]
    elif len(matches_valor) == 1:
        # Se houver apenas um valor com vírgula, assumimos que é o valor da operação.
        valor_debito = matches_valor[0]
        
    return data, valor_debito

# --- 3. INTERFACE ---
st.markdown('<h1 class="consultoria-title">Consultoria de Ativos</h1>', unsafe_allow_html=True)

st.sidebar.markdown("### PARÂMETROS DE BUSCA")
ALVOS = {
    "MORA CREDITO PESSOAL": r"MORA CREDITO PESSOAL|MORA CRED PESS",
    "ENCARGOS LIMITE": r"ENCARGOS LIMITE|ENC LIM CREDITO",
    "TARIFAS": r"TARIFA BANCARIA|CESTA B\.EXPRESSO",
    "IOF": r"IOF S/ UTILIZACAO|IOF UTIL LIMITE",
    "ANUIDADE": r"CARTAO CREDITO ANUIDADE|CART CRED ANUID"
}

selecionados = [k for k, v in ALVOS.items() if st.sidebar.checkbox(k, value=True)]
upload = st.file_uploader("Arraste o Extrato PDF ou Imagem", type=["pdf", "png", "jpg", "jpeg"])

if upload:
    with st.spinner('Auditando Colunas de Débito...'):
        resultados = []
        linhas = []
        
        if upload.type == "application/pdf":
            with pdfplumber.open(upload) as pdf:
                for p in pdf.pages:
                    linhas.extend(p.extract_text().split('\n'))
        else:
            img = PILImage.open(upload)
            linhas.extend(pytesseract.image_to_string(PILOps.grayscale(img), lang='por').split('\n'))

        for linha in linhas:
            for nome, regex in ALVOS.items():
                if nome in selecionados and re.search(regex, linha, re.IGNORECASE):
                    data, valor = extrair_valor_debito_real(linha)
                    if valor != "0,00":
                        resultados.append({
                            "DATA": data,
                            "CATEGORIA": nome,
                            "VALOR DÉBITO (R$)": valor,
                            "LINHA ORIGINAL": linha.strip()[:50] + "..."
                        })
                    break

        if resultados:
            df = pd.DataFrame(resultados)
            st.dataframe(df, use_container_width=True)
            total = sum([float(v.replace('.','').replace(',','.')) for v in df["VALOR DÉBITO (R$)"]])
            st.metric("Total de Débitos Identificados", f"R$ {total:,.2f}")
        else:
            st.info("Nenhum débito encontrado com os critérios de precisão.")

st.markdown('<p class="footer-name">Edson Medeiros</p>', unsafe_allow_html=True)
