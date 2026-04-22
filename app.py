import streamlit as st
import pdfplumber
import pandas as pd
import re
from datetime import datetime
import io
import PIL.Image as PILImage # CORREÇÃO AQUI
import pytesseract
from pdf2image import convert_from_bytes

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
.how-it-works { background: rgba(15, 23, 42, 0.6); border-radius: 16px; padding: 40px; margin-top: 60px; border: 1px solid rgba(191, 175, 131, 0.1); margin-bottom: 100px; }
.step-number { color: var(--gold-matte); font-family: 'Cinzel', serif; font-size: 1.8rem; margin-bottom: 10px; }
.footer-signature { position: fixed; bottom: 30px; right: 40px; text-align: right; z-index: 100; }
.footer-name { font-family: 'Great Vibes', cursive; color: var(--gold-matte); font-size: 2.2rem; margin: 0; }
[data-testid="stSidebar"] { background-color: #080C14 !important; border-right: 1px solid #1E293B; }
</style>
"""
st.markdown(ESTILO_CSS, unsafe_allow_html=True)

# --- 2. TELA DE ACESSO RESTRITO (LOGIN INTEGRADO) ---
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
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("AUTENTICAR SISTEMA", use_container_width=True):
                if email == "edson.senabr@gmail.com" and senha == "medeirosefernandes2026":
                    st.session_state["autenticado"] = True
                    st.rerun()
                else:
                    st.error("Credenciais incorretas.")
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div style="text-align: center;"><a href="https://contate.me/5592995087379" class="btn-whatsapp" target="_blank">Suporte Técnico ⚖️</a></div>', unsafe_allow_html=True)
        return False
    return True

if tela_login():
    # --- 3. DASHBOARD PRINCIPAL ---
    col_head, col_cta = st.columns([2.5, 1])
    with col_head:
        st.markdown('<h1 class="consultoria-title">Consultoria de Ativos</h1>', unsafe_allow_html=True)
        st.markdown("<p style='color: #BFAF83; letter-spacing: 2px; font-size: 0.9rem;'>AUDITORIA TÉCNICA PROPRIETÁRIA DE EXTRATOS</p>", unsafe_allow_html=True)
    with col_cta:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown('<a href="https://contate.me/5592995087379" class="btn-whatsapp" target="_blank">Falar com Consultor ⚖️</a>', unsafe_allow_html=True)

    # --- 4. SIDEBAR E PARÂMETROS ---
    st.sidebar.markdown("### PARÂMETROS DE BUSCA")
    
    DICIONARIO_ALVOS = {
        "CESTA/PACOTE": "CESTA|PACOTE",
        "MORA DE OPERAÇÃO": "MORA DE OPERAÇÃO|MORA DE OPERACAO",
        "MORA CREDITO PESSOAL": "MORA CREDITO PESSOAL|MORA CRÉDITO PESSOAL",
        "MORA OPERACAO DE CREDITO": "MORA OPERACAO DE CREDITO|MORA OPERAÇÃO DE CRÉDITO",
        "BX": r"\bBX\b",
        "PARCELA CREDITO PESSOAL": "PARCELA CREDITO PESSOAL|PARCELA CRÉDITO PESSOAL",
        "GASTOS CARTAO DE CREDITO": "GASTOS CARTAO DE CREDITO|GASTOS CARTÃO DE CRÉDITO",
        "SEGURO": "SEGURO",
        "ADIANT": "ADIANT",
        "APLIC": "APLIC",
        "ENCARGOS": "ENCARGOS",
        "ANUIDADE": "ANUIDADE",
        "OPERACOES VENCIDAS": "OPERACOES VENCIDAS|OPERAÇÕES VENCIDAS",
        "DIV. EM ATRASO": "DIV. EM ATRASO|DÍV. EM ATRASO"
    }
    
    selecionados = [n for n in DICIONARIO_ALVOS.keys() if st.sidebar.checkbox(n, value=True)]
    
    st.sidebar.markdown("<br>### PERÍODO DE AUDITORIA", unsafe_allow_html=True)
    usar_data = st.sidebar.checkbox("Ativar Limite (Prescrição)")
    if usar_data:
        d_inf = st.sidebar.date_input("Início", format="DD/MM/YYYY")
        d_sup = st.sidebar.date_input("Fim", format="DD/MM/YYYY")

    # --- 5. LÓGICA DE PROCESSAMENTO HÍBRIDO (DIGITAL + OCR) ---
    st.markdown("<br>", unsafe_allow_html=True)
    upload = st.file_uploader("Upload de Extratos (PDF Digital ou Scans/Fotos/Imagens)", type=["pdf", "png", "jpg", "jpeg"])

    if upload:
        with st.spinner('Visão Computacional Ativada: Executando Auditoria Crítica e Reconhecimento (OCR)...'):
            dados = []
            termos = [DICIONARIO_ALVOS[f] for f in selecionados]
            linhas_extraidas = []

            try:
                if upload.type == "application/pdf":
                    file_bytes = upload.read()
                    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                        for i, p in enumerate(pdf.pages):
                            texto_p = p.extract_text()
                            if texto_p and texto_p.strip():
                                linhas_extraidas.extend(texto_p.split('\n'))
                            else:
                                st.toast(f"Analisando Scan na Página {i+1}...")
                                imagens_pdf = convert_from_bytes(file_bytes, first_page=i+1, last_page=i+1)
                                if imagens_pdf:
                                    texto_ocr = pytesseract.image_to_string(imagens_pdf[0], lang='por')
                                    linhas_extraidas.extend(texto_ocr.split('\n'))
                else:
                    # CORREÇÃO APLICADA AQUI (Blindagem da biblioteca de imagem)
                    img = PILImage.open(upload)
                    texto_ocr = pytesseract.image_to_string(img, lang='por')
                    linhas_extraidas.extend(texto_ocr.split('\n'))
            except Exception as e:
                st.error("Erro na Visão Computacional. Certifique-se de que os pacotes do servidor (Tesseract/Poppler) estão instalados. Consulte o Suporte Técnico.")
                st.exception(e)

            # Passo 2: Auditoria Cronológica
            for i, linha in enumerate(linhas_extraidas):
                for t in termos:
                    if re.search(t, linha, re.IGNORECASE):
                        data_correta = "---"
                        match_linha = re.search(r'(\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4})', linha)
                        if match_linha:
                            data_correta = match_linha.group(1).replace('-', '/')
                        else:
                            for j in range(i-1, max(0, i-25), -1):
                                m_up = re.search(r'(\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4})', linhas_extraidas[j])
                                if m_up: 
                                    data_correta = m_up.group(1).replace('-', '/')
                                    break
                            if data_correta == "---":
                                for k in range(i+1, min(i+25, len(linhas_extraidas))):
                                    m_dw = re.search(r'(\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4})', linhas_extraidas[k])
                                    if m_dw: 
                                        data_correta = m_dw.group(1).replace('-', '/')
                                        break

                        if usar_data and data_correta != "---":
                            try:
                                dt_v = datetime.strptime(data_correta, "%d/%m/%Y").date()
                                if dt_v < d_inf or dt_v > d_sup: continue
                            except: pass

                        v_m = re.findall(r'(\d{1,3}(?:\.\d{3})*,\d{2}|\d+,\d{2}|\d+\.\d{2})', linha)
                        if v_m:
                            valor = v_m[-1].replace('.', ',') if '.' in v_m[-1][-3:] else v_m[-1]
                        else:
                            valor = "0,00"

                        cat_nome = next(k for k, v in DICIONARIO_ALVOS.items() if v == t)
                        dados.append({"DATA": data_correta, "CATEGORIA": cat_nome.upper(), "VALOR (R$)": valor, "DESCRIÇÃO": linha[:100]})
                        break

            # --- 6. EXIBIÇÃO DE RESULTADOS ---
            if dados:
                df = pd.DataFrame(dados)
                total_rec = sum([float(v.replace('.','').replace(',','.')) for v in df["VALOR (R$)"]])
                cats_unicas = df["CATEGORIA"].unique()
                
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown(f'<div class="impact-card"><p style="font-size: 0.7rem; color: #64748B;">CATEGORIAS IDENTIFICADAS</p><h2 style="color: #BFAF83; font-family: Cinzel;">{len(cats_unicas)}</h2></div>', unsafe_allow_html=True)
                with c2:
                    st.markdown(f'<div class="impact-card"><p style="font-size: 0.7rem; color: #64748B;">VALOR TOTAL RECUPERÁVEL</p><h2 style="color: #BFAF83; font-family: Cinzel;">R$ {total_rec:,.2f}</h2></div>', unsafe_allow_html=True)
                with c3:
                    st.markdown(f'<div class="impact-card"><p style="font-size: 0.7rem; color: #64748B;">STATUS</p><h2 style="color: #10B981; font-family: Cinzel;">AUDITADO</h2></div>', unsafe_allow_html=True)

                st.markdown("<h4 style='color: #BFAF83; font-family: Cinzel; font-size: 1rem; margin-bottom: 15px;'>DÉBITOS IDENTIFICADOS</h4>", unsafe_allow_html=True)
                badges_html = "".join([f'<div class="categoria-badge">{cat}</div>' for cat in cats_unicas])
                st.markdown(f'<div class="resumo-direto">{badges_html}</div>', unsafe_allow_html=True)

                st.dataframe(df, use_container_width=True)
                st.download_button("📥 BAIXAR LAUDO TÉCNICO", df.to_csv(index=False).encode('utf-8-sig'), "laudo_auditoria.csv")
            else:
                st.info("Nenhum débito abusivo encontrado com as configurações atuais.")

    # --- 7. PROCESSO DE CONSULTORIA ---
    st.markdown("""
    <div class="how-it-works">
        <h3 style="font-family: 'Cinzel', serif; color: #BFAF83; text-align: center; margin-bottom: 40px; letter-spacing: 2px;">PROCESSO DE CONSULTORIA</h3>
        <div style="display: flex; justify-content: space-around; gap: 30px; flex-wrap: wrap; text-align: center;">
            <div style="flex: 1; min-width: 250px;">
                <div class="step-number">I</div>
                <p style="font-weight: 600; color: #FFF;">Identificação Digital</p>
                <p style="font-size: 0.8rem; color: #94A3B8;">O robô identifica ativos indevidos em documentos digitais ou imagens (OCR).</p>
            </div>
            <div style="flex: 1; min-width: 250px;">
                <div class="step-number">II</div>
                <p style="font-weight: 600; color: #FFF;">Extração Técnica</p>
                <p style="font-size: 0.8rem; color: #94A3B8;">Captura precisa de valores ocultos nos extratos bancários físicos e digitais.</p>
            </div>
            <div style="flex: 1; min-width: 250px;">
                <div class="step-number">III</div>
                <p style="font-weight: 600; color: #FFF;">Certificação de Ativos</p>
                <p style="font-size: 0.8rem; color: #94A3B8;">Emissão de laudo técnico especializado para recuperação judicial ou amigável.</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- 8. FOOTER ---
    st.markdown('<div class="footer-signature"><p class="footer-name">Edson Medeiros</p><p style="font-size: 0.7rem; color: #64748B; letter-spacing: 3px;">CONSULTORIA & COMPLIANCE</p></div>', unsafe_allow_html=True)
