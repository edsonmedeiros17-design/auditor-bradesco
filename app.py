import streamlit as st
import pdfplumber
import pandas as pd
import re
import io
import PIL.Image as PILImage
import PIL.ImageOps as PILOps
import PIL.ImageEnhance as PILEnhance
import pytesseract
from pdf2image import convert_from_bytes
import shutil

# --- 1. CONFIGURAÇÃO E ESTÉTICA PREMIUM (FIDELIDADE TOTAL) ---
st.set_page_config(page_title="Edson Medeiros | Consultoria de Ativos", layout="wide", page_icon="⚖️")

ESTILO_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600&family=Playfair+Display:ital,wght@0,700;1,700&family=Inter:wght@300;400;600&family=Great+Vibes&display=swap');

:root { --navy-deep: #0F172A; --gold-matte: #BFAF83; --off-white: #F8F9FA; }

.stApp { background: radial-gradient(circle at center, #1E293B 0%, #0F172A 100%); color: var(--off-white); font-family: 'Inter', sans-serif; }

.consultoria-title { 
    font-family: 'Playfair Display', serif !important; 
    font-size: 4.5rem !important; 
    font-weight: 700 !important; 
    background: linear-gradient(180deg, #FFFFFF 0%, #BFAF83 100%); 
    -webkit-background-clip: text; 
    -webkit-text-fill-color: transparent; 
    text-shadow: 0px 2px 0px #8A7650, 0px 4px 10px rgba(0,0,0,0.5); 
    line-height: 1.1; 
    margin-bottom: 5px; 
}

.login-card {
    background: rgba(15, 23, 42, 0.8);
    border: 1px solid rgba(191, 175, 131, 0.3);
    border-radius: 15px;
    padding: 40px;
    box-shadow: 0 20px 50px rgba(0,0,0,0.5);
    text-align: center;
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
}

.impact-card { 
    background: rgba(255, 255, 255, 0.05); 
    border: 1px solid rgba(191, 175, 131, 0.2); 
    border-radius: 12px; 
    padding: 20px; 
    text-align: center; 
}

.footer-name { font-family: 'Great Vibes', cursive; color: var(--gold-matte); font-size: 2.2rem; margin: 0; }

div[data-baseweb="input"] { background-color: rgba(255,255,255,0.05) !important; border-radius: 8px !important; }
</style>
"""
st.markdown(ESTILO_CSS, unsafe_allow_html=True)

# --- 2. MOTOR DE PRECISÃO CIRÚRGICA ---
def extrair_dados_linha_precisa(linha_texto):
    # 1. Busca Data (DD/MM ou DD/MM/AAAA)
    match_data = re.search(r'(\d{2}/\d{2}(?:/\d{2,4})?)', linha_texto)
    data = match_data.group(1) if match_data else "---"
    
    # 2. Busca Valor (O último número com vírgula da linha - Padrão Bancário)
    matches_valor = re.findall(r'(\d{1,3}(?:\.\d{3})*,\d{2}|\d+,\d{2})', linha_texto)
    valor = matches_valor[-1] if matches_valor else "0,00"
    
    return data, valor

# --- 3. TELA DE ACESSO RESTRITO (MANTIDA) ---
def tela_login():
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False

    if not st.session_state["autenticado"]:
        _, col_central, _ = st.columns([1, 1.2, 1])
        with col_central:
            st.markdown("<br><br><br>", unsafe_allow_html=True)
            st.markdown("""
                <div class="login-card">
                    <h2 style='font-family: Cinzel; color: #BFAF83; letter-spacing: 4px;'>SISTEMA DE AUDITORIA</h2>
                    <p style='font-size: 0.8rem; color: #64748B; margin-bottom: 30px;'>CONSULTORIA DE ATIVOS | ACESSO EXCLUSIVO</p>
                </div>
            """, unsafe_allow_html=True)
            
            email = st.text_input("E-mail de Acesso", value="edson.senabr@gmail.com")
            senha = st.text_input("Senha", type="password")
            
            if st.button("AUTENTICAR NO SERVIDOR", use_container_width=True):
                if email == "edson.senabr@gmail.com" and senha == "medeirosefernandes2026":
                    st.session_state["autenticado"] = True
                    st.rerun()
                else:
                    st.error("Credenciais inválidas.")
        return False
    return True

# --- 4. EXECUÇÃO DO SITE E NOVOS PARÂMETROS ---
if tela_login():
    col_head, col_cta = st.columns([2.5, 1])
    with col_head:
        st.markdown('<h1 class="consultoria-title">Consultoria de Ativos</h1>', unsafe_allow_html=True)
        st.markdown("<p style='color: #BFAF83; letter-spacing: 3px; font-size: 0.9rem;'>AUDITORIA TÉCNICA DE ALTA PRECISÃO</p>", unsafe_allow_html=True)

    # --- DICIONÁRIO COMPLETO BASEADO NA IMAGEM ANEXA ---
    st.sidebar.markdown("### PARÂMETROS DE BUSCA")
    DICIONARIO_ALVOS = {
        "ENC LIM CREDITO": r"ENC LIM CREDITO|ENCARGO LIMITE",
        "IOF UTIL LIMITE": r"IOF UTIL LIMITE|IOF LIMITE",
        "MORA CRED PESS": r"MORA CRED PESS|MORA CREDITO PESSOAL",
        "CART CRED ANUID": r"CART CRED ANUID|ANUIDADE CARTAO",
        "PARC CRED PESS": r"PARC CRED PESS|PARCELA CREDITO",
        "TARIFA BANCARIA": r"TARIFA BANCARIA|TAR BANC",
        "CESTA B EXPRESSO": r"CESTA B EXPRESSO|CESTA BANCARIA",
        "ENCARGO 13,41%": r"ENCARGO 13,41%|ENCARGO PERCENTUAL",
        "DEP DINHEIRO CB": r"DEP DINHEIRO CB",
        "SALDO ANTERIOR": r"SALDO ANTERIOR",
    }
    
    selecionados = [n for n in DICIONARIO_ALVOS.keys() if st.sidebar.checkbox(n, value=True)]
    upload = st.file_uploader("Upload de Extratos", type=["pdf", "png", "jpg", "jpeg"])

    if upload:
        with st.spinner('Executando Varredura Linear de Precisão...'):
            dados_finais = []
            linhas_brutas = []

            # Extração (PDF/Imagem)
            if upload.type == "application/pdf":
                with pdfplumber.open(upload) as pdf:
                    for p in pdf.pages:
                        txt = p.extract_text()
                        if txt: linhas_brutas.extend(txt.split('\n'))
            else:
                img = PILImage.open(upload)
                txt_ocr = pytesseract.image_to_string(PILOps.grayscale(img), lang='por')
                linhas_brutas.extend(txt_ocr.split('\n'))

            # Processamento com a Trava de Linha
            for linha in linhas_brutas:
                for cat in selecionados:
                    if re.search(DICIONARIO_ALVOS[cat], linha, re.IGNORECASE):
                        data, valor = extrair_dados_linha_precisa(linha)
                        if valor != "0,00":
                            dados_finais.append({
                                "DATA": data,
                                "CATEGORIA": cat,
                                "VALOR (R$)": valor,
                                "DESCRIÇÃO NO EXTRATO": linha.strip()[:65]
                            })
                        break

            if dados_finais:
                df = pd.DataFrame(dados_finais)
                total_float = sum([float(v.replace('.','').replace(',','.')) for v in df["VALOR (R$)"]])
                
                c1, c2 = st.columns(2)
                with c1: st.markdown(f'<div class="impact-card"><h6>DÉBITOS</h6><h2>{len(df)}</h2></div>', unsafe_allow_html=True)
                with c2: st.markdown(f'<div class="impact-card"><h6>TOTAL</h6><h2 style="color:#BFAF83;">R$ {total_float:,.2f}</h2></div>', unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                st.dataframe(df, use_container_width=True)
                st.download_button("📥 BAIXAR LAUDO TÉCNICO", df.to_csv(index=False).encode('utf-8-sig'), "auditoria_precisao.csv")

    st.markdown('<div style="text-align: right; margin-top: 50px;"><p class="footer-name">Edson Medeiros</p></div>', unsafe_allow_html=True)
