import streamlit as st
import pdfplumber
import pandas as pd
import re
from datetime import datetime
import io
import PIL.Image as PILImage
import PIL.ImageOps as PILOps
import PIL.ImageEnhance as PILEnhance
import pytesseract
from pdf2image import convert_from_bytes
import shutil

# --- 1. CONFIGURAÇÃO E ESTÉTICA PREMIUM (MANUTENÇÃO TOTAL) ---
st.set_page_config(page_title="Edson Medeiros | Consultoria de Ativos", layout="wide", page_icon="⚖️")

ESTILO_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600&family=Playfair+Display:ital,wght@0,700;1,700&family=Inter:wght@300;400;600&family=Great+Vibes&display=swap');
:root { --navy-deep: #0F172A; --gold-matte: #BFAF83; --emerald-success: #10B981; --off-white: #F8F9FA; }
.stApp { background: radial-gradient(circle at center, #1E293B 0%, #0F172A 100%); color: var(--off-white); font-family: 'Inter', sans-serif; }
.consultoria-title { font-family: 'Playfair Display', serif !important; font-size: 4.5rem !important; font-weight: 700 !important; background: linear-gradient(180deg, #FFFFFF 0%, #BFAF83 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 0px 2px 0px #8A7650, 0px 4px 10px rgba(0,0,0,0.5); line-height: 1.1; margin-bottom: 5px; }
.btn-whatsapp { background-color: #25D366 !important; color: white !important; padding: 14px 28px !important; border-radius: 50px !important; text-decoration: none !important; font-weight: bold !important; display: inline-block !important; transition: 0.3s !important; box-shadow: 0 4px 15px rgba(37, 211, 102, 0.4) !important; text-align: center; border: none !important; margin-top: 10px; }
.impact-card { background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(191, 175, 131, 0.2); border-radius: 12px; padding: 20px; text-align: center; margin-bottom: 20px; }
.resumo-direto { background: rgba(191, 175, 131, 0.05); border: 1px solid rgba(191, 175, 131, 0.2); padding: 20px; border-radius: 12px; margin-bottom: 30px; }
.categoria-badge { background: rgba(191, 175, 131, 0.15); color: #BFAF83; border: 1px solid #BFAF83; padding: 6px 15px; border-radius: 20px; font-size: 0.75rem; margin: 5px; display: inline-block; font-weight: 600; letter-spacing: 1px; }
.footer-signature { position: fixed; bottom: 30px; right: 40px; text-align: right; z-index: 100; }
.footer-name { font-family: 'Great Vibes', cursive; color: var(--gold-matte); font-size: 2.2rem; margin: 0; }
[data-testid="stSidebar"] { background-color: #080C14 !important; border-right: 1px solid #1E293B; }
</style>
"""
st.markdown(ESTILO_CSS, unsafe_allow_html=True)

# --- FUNÇÕES DE VISÃO COMPUTACIONAL ---
def tesseract_instalado():
    return shutil.which("tesseract") is not None

def melhorar_imagem(imagem_pil):
    """Aplica filtros para facilitar a leitura de fotos de extratos"""
    # Converter para escala de cinza
    imagem = PILOps.grayscale(imagem_pil)
    # Aumentar contraste
    enhancer = PILEnhance.Contrast(imagem)
    imagem = enhancer.enhance(2.0)
    return imagem

# --- 2. TELA DE ACESSO RESTRITO ---
def tela_login():
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False
    if not st.session_state["autenticado"]:
        _, col_login, _ = st.columns([1, 1.2, 1])
        with col_login:
            st.markdown("<br><br><br>", unsafe_allow_html=True)
            st.markdown("<h2 style='font-family: Cinzel; color: #BFAF83; letter-spacing: 3px; text-align: center;'>ACESSO RESTRITO</h2>", unsafe_allow_html=True)
            email = st.text_input("E-mail de Acesso")
            senha = st.text_input("Senha", type="password")
            if st.button("AUTENTICAR SISTEMA", use_container_width=True):
                if email == "edson.senabr@gmail.com" and senha == "medeirosefernandes2026":
                    st.session_state["autenticado"] = True
                    st.rerun()
                else: st.error("Credenciais incorretas.")
        return False
    return True

if tela_login():
    if not tesseract_instalado():
        st.warning("⚠️ O motor de OCR está sendo configurado pelo servidor. Aguarde 30 segundos e atualize.")
        st.stop()

    # --- 3. DASHBOARD ---
    col_head, col_cta = st.columns([2.5, 1])
    with col_head:
        st.markdown('<h1 class="consultoria-title">Consultoria de Ativos</h1>', unsafe_allow_html=True)
        st.markdown("<p style='color: #BFAF83; letter-spacing: 2px; font-size: 0.9rem;'>AUDITORIA TÉCNICA PROPRIETÁRIA DE EXTRATOS</p>", unsafe_allow_html=True)
    with col_cta:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown('<a href="https://contate.me/5592995087379" class="btn-whatsapp" target="_blank">Falar com Consultor ⚖️</a>', unsafe_allow_html=True)

    # --- 4. SIDEBAR COM DICIONÁRIO DE ABREVIAÇÕES (SOLUÇÃO SITUAÇÃO 1) ---
    st.sidebar.markdown("### PARÂMETROS DE BUSCA")
    
    # Adicionado variações encontradas na imagem 1 (MORA CRED PESS, PARC CRED PESS, etc.)
    DICIONARIO_ALVOS = {
        "CESTA/PACOTE": r"CESTA|PACOTE|TARIFA BANCARIA",
        "MORA DE OPERAÇÃO": r"MORA DE OPERAÇÃO|MORA DE OPERACAO|MORA OPER",
        "MORA CREDITO PESSOAL": r"MORA CREDITO PESSOAL|MORA CRÉDITO PESSOAL|MORA CRED PESS",
        "MORA OPERACAO DE CREDITO": r"MORA OPERACAO DE CREDITO|MORA OPERAÇÃO DE CRÉDITO|MORA OPER CRED",
        "BX": r"\bBX\b",
        "PARCELA CREDITO PESSOAL": r"PARCELA CREDITO PESSOAL|PARCELA CRÉDITO PESSOAL|PARC CRED PESS",
        "GASTOS CARTAO DE CREDITO": r"GASTOS CARTAO DE CREDITO|GASTOS CARTÃO DE CRÉDITO|CART CRED",
        "SEGURO": r"SEGURO|SEG\.",
        "ADIANT": r"ADIANT|AD DEP",
        "APLIC": r"APLIC",
        "ENCARGOS": r"ENCARGOS|ENC LIM|ENCARGO",
        "ANUIDADE": r"ANUIDADE|ANUID",
        "OPERACOES VENCIDAS": r"OPERACOES VENCIDAS|OPERAÇÕES VENCIDAS|OPER VENC",
        "DIV. EM ATRASO": r"DIV. EM ATRASO|DÍV. EM ATRASO|DIV ATRASO"
    }
    
    selecionados = [n for n in DICIONARIO_ALVOS.keys() if st.sidebar.checkbox(n, value=True)]
    usar_data = st.sidebar.checkbox("Ativar Limite (Prescrição)")
    if usar_data:
        d_inf = st.sidebar.date_input("Início")
        d_sup = st.sidebar.date_input("Fim")

    # --- 5. LÓGICA DE PROCESSAMENTO ---
    upload = st.file_uploader("Upload de Extratos (PDF ou Fotos)", type=["pdf", "png", "jpg", "jpeg"])

    if upload:
        with st.spinner('Visão Computacional Ativada: Reconstruindo dados de imagem...'):
            dados = []
            termos_regex = {k: DICIONARIO_ALVOS[k] for k in selecionados}
            linhas_extraidas = []

            # Captura de Texto (Digital ou Imagem)
            if upload.type == "application/pdf":
                file_bytes = upload.read()
                with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                    for i, p in enumerate(pdf.pages):
                        texto = p.extract_text()
                        if texto and len(texto.strip()) > 50:
                            linhas_extraidas.extend(texto.split('\n'))
                        else:
                            # PDF Escaneado - OCR página a página
                            imgs = convert_from_bytes(file_bytes, first_page=i+1, last_page=i+1)
                            for img in imgs:
                                img_limpa = melhorar_imagem(img)
                                texto_ocr = pytesseract.image_to_string(img_limpa, lang='por')
                                linhas_extraidas.extend(texto_ocr.split('\n'))
            else:
                img_u = PILImage.open(upload)
                img_limpa = melhorar_imagem(img_u)
                texto_ocr = pytesseract.image_to_string(img_limpa, lang='por')
                linhas_extraidas.extend(texto_ocr.split('\n'))

            # Auditoria das Linhas (Solução Situação 2 - Extração de Valores)
            for idx, linha in enumerate(linhas_extraidas):
                for categoria, padrao in termos_regex.items():
                    if re.search(padrao, linha, re.IGNORECASE):
                        # 1. Busca Data
                        data = "---"
                        m_data = re.search(r'(\d{2}/\d{2}/\d{4}|\d{2}/\d{2}/\d{2}|\d{2}/\d{2})', linha)
                        if m_data: data = m_data.group(1)
                        else:
                            # Busca nas 5 linhas acima se não achou na linha atual
                            for offset in range(1, 6):
                                if idx-offset >= 0:
                                    m_data_up = re.search(r'(\d{2}/\d{2}/\d{4}|\d{2}/\d{2})', linhas_extraidas[idx-offset])
                                    if m_data_up: 
                                        data = m_data_up.group(1)
                                        break

                        # 2. Busca Valor (Otimizado para OCR que gruda números)
                        # Procura o último grupo numérico que tenha formato de moeda (xx,xx)
                        valor = "0,00"
                        # Regex procura por: espaço ou fim de string, seguido de números, vírgula e dois dígitos
                        m_valor = re.findall(r'(\d+[\.,]\d{2})(?=\s|$)', linha)
                        if m_valor:
                            valor = m_valor[-1].replace('.', ',')
                        
                        # Filtro de Data Prescricional
                        if usar_data and "/" in data:
                            try:
                                data_format = data if len(data) > 5 else f"{data}/{datetime.now().year}"
                                dt_v = pd.to_datetime(data_format, dayfirst=True).date()
                                if dt_v < d_inf or dt_v > d_sup: continue
                            except: pass

                        dados.append({
                            "DATA": data,
                            "CATEGORIA": categoria,
                            "VALOR (R$)": valor,
                            "DESCRIÇÃO DO EXTRATO": linha.strip()[:80]
                        })
                        break

            # --- 6. EXIBIÇÃO DE RESULTADOS ---
            if dados:
                df = pd.DataFrame(dados)
                # Limpeza de valores para soma
                val_soma = df["VALOR (R$)"].str.replace('.','', regex=False).str.replace(',','.', regex=False).astype(float)
                total_rec = val_soma.sum()
                
                c1, c2, c3 = st.columns(3)
                with c1: st.markdown(f'<div class="impact-card"><p style="font-size: 0.7rem;">DÉBITOS ACHADOS</p><h2 style="color:#BFAF83;">{len(df)}</h2></div>', unsafe_allow_html=True)
                with c2: st.markdown(f'<div class="impact-card"><p style="font-size: 0.7rem;">TOTAL ESTIMADO</p><h2 style="color:#BFAF83;">R$ {total_rec:,.2f}</h2></div>', unsafe_allow_html=True)
                with c3: st.markdown(f'<div class="impact-card"><p style="font-size: 0.7rem;">STATUS</p><h2 style="color:#10B981;">CONCLUÍDO</h2></div>', unsafe_allow_html=True)

                st.dataframe(df, use_container_width=True)
                st.download_button("📥 BAIXAR LAUDO TÉCNICO", df.to_csv(index=False).encode('utf-8-sig'), "laudo_auditoria.csv")
            else:
                st.info("Nenhum débito identificado na imagem. Tente uma foto com mais iluminação ou verifique os filtros ao lado.")

    # --- 8. FOOTER ---
    st.markdown('<div class="footer-signature"><p class="footer-name">Edson Medeiros</p><p style="font-size: 0.7rem; color: #64748B; letter-spacing: 3px;">CONSULTORIA & COMPLIANCE</p></div>', unsafe_allow_html=True)
