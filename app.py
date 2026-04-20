import streamlit as st
import pdfplumber
import pandas as pd
import re
from datetime import datetime

# --- 1. CONFIGURAÇÃO DE TELA E ESTÉTICA (MANTIDA 100%) ---
st.set_page_config(page_title="Edson Medeiros | Consultoria de Ativos", layout="wide", page_icon="⚖️")

ESTILO_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600&family=Playfair+Display:ital,wght@0,700;1,700&family=Inter:wght@300;400;600&family=Great+Vibes&display=swap');
:root { --navy-deep: #0F172A; --gold-matte: #BFAF83; --emerald-success: #10B981; --off-white: #F8F9FA; }
.stApp { background: radial-gradient(circle at center, #1E293B 0%, #0F172A 100%); color: var(--off-white); font-family: 'Inter', sans-serif; }
.consultoria-title { font-family: 'Playfair Display', serif !important; font-size: 4.5rem !important; font-weight: 700 !important; background: linear-gradient(180deg, #FFFFFF 0%, #BFAF83 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 0px 2px 0px #8A7650, 0px 4px 10px rgba(0,0,0,0.5); line-height: 1.1; margin-bottom: 5px; }
.btn-whatsapp { background-color: #25D366 !important; color: white !important; padding: 14px 28px !important; border-radius: 50px !important; text-decoration: none !important; font-weight: bold !important; display: inline-block !important; transition: 0.3s !important; box-shadow: 0 4px 15px rgba(37, 211, 102, 0.4) !important; text-align: center; border: none !important; }
.impact-card { background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(191, 175, 131, 0.2); border-radius: 12px; padding: 20px; text-align: center; margin-bottom: 20px; }
.resumo-direto { background: rgba(191, 175, 131, 0.1); border-left: 4px solid #BFAF83; padding: 15px; margin: 10px 0; border-radius: 4px; }
.footer-signature { position: fixed; bottom: 30px; right: 40px; text-align: right; z-index: 100; }
.footer-name { font-family: 'Great Vibes', cursive; color: var(--gold-matte); font-size: 2.2rem; margin: 0; }
[data-testid="stSidebar"] { background-color: #080C14 !important; border-right: 1px solid #1E293B; }
</style>
"""
st.markdown(ESTILO_CSS, unsafe_allow_html=True)

# --- 2. SISTEMA DE ACESSO RESTRITO ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("<br><br><h2 style='text-align: center; color: #BFAF83;'>ACESSO RESTRITO</h2>", unsafe_allow_html=True)
            user = st.text_input("Usuário")
            password = st.text_input("Senha", type="password")
            if st.button("Acessar Sistema"):
                if user == "edson" and password == "medeiros17": # Defina suas credenciais aqui
                    st.session_state["authenticated"] = True
                    st.rerun()
                else:
                    st.error("Credenciais Inválidas")
        return False
    return True

if check_password():
    # --- 3. INTERFACE PRINCIPAL ---
    col_head, col_cta = st.columns([2.5, 1])
    with col_head:
        st.markdown('<h1 class="consultoria-title">Consultoria de Ativos</h1>', unsafe_allow_html=True)
        st.markdown("<p style='color: #BFAF83; letter-spacing: 2px; font-size: 0.9rem;'>AUDITORIA TÉCNICA PROPRIETÁRIA DE EXTRATOS</p>", unsafe_allow_html=True)
    with col_cta:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown('<a href="https://contate.me/5592995087379" class="btn-whatsapp" target="_blank">Falar com Consultor ⚖️</a>', unsafe_allow_html=True)

    # --- 4. PARÂMETROS ---
    st.sidebar.markdown("### PARÂMETROS DE BUSCA")
    DICIONARIO_ALVOS = {
        "Cesta / Pacote": "CESTA|PACOTE",
        "Tarifas Bancárias": "TARIFA BANCARIA",
        "Mora": "MORA",
        "Baixas e Débitos (BX)": r"\bBX\b",
        "Crédito Pessoal": "PARCELA CREDITO PESSOAL",
        "Gastos Cartão de Crédito": "GASTOS CARTAO DE CREDITO",
        "Seguro": "SEGURO",
        "Adiantamento": "ADIANT",
        "Aplicações": "APLIC",
        "Encargos": "ENCARGOS",
        "Anuidade": "ANUIDADE",
        "Operações Vencidas": "OPERACOES VENCIDAS",
        "Dívidas em Atraso": "DIV. EM ATRASO"
    }
    
    selecionados = [nome for nome in DICIONARIO_ALVOS.keys() if st.sidebar.checkbox(nome, value=True)]
    
    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    st.sidebar.markdown("### PERÍODO DE AUDITORIA")
    usar_filtro = st.sidebar.checkbox("Ativar Limite de Datas (Prescrição)")
    if usar_filtro:
        data_inf = st.sidebar.date_input("Início", format="DD/MM/YYYY")
        data_sup = st.sidebar.date_input("Fim", format="DD/MM/YYYY")

    upload = st.file_uploader("Submeta o arquivo PDF para certificação técnica", type="pdf")

    if upload:
        with st.spinner('Auditando...'):
            dados = []
            termos = [DICIONARIO_ALVOS[f] for f in selecionados]
            data_atual = "---"
            
            with pdfplumber.open(upload) as pdf:
                for p in pdf.pages:
                    texto = p.extract_text()
                    if texto:
                        for linha in texto.split('\n'):
                            m_data = re.search(r'(\d{2}/\d{2}/\d{4})', linha)
                            if m_data: data_atual = m_data.group(1)
                            
                            # Filtro de Data
                            if usar_filtro:
                                try:
                                    dt_obj = datetime.strptime(data_atual, "%d/%m/%Y").date()
                                    if dt_obj < data_inf or dt_obj > data_sup: continue
                                except: pass

                            for t in termos:
                                if re.search(t, linha, re.IGNORECASE):
                                    v_m = re.findall(r'(\d[\d\.]*,\d{2})', linha)
                                    valor = v_m[-1] if v_m else "0,00"
                                    cat = next(k for k, v in DICIONARIO_ALVOS.items() if v == t)
                                    dados.append({"DATA": data_atual, "CATEGORIA": cat.upper(), "DESCRIÇÃO": linha.strip()[:100], "VALOR": valor})
                                    break
            
            if dados:
                df = pd.DataFrame(dados)
                total_val = sum([float(v.replace('.','').replace(',','.')) for v in df["VALOR"]])
                
                # INOVAÇÃO: Contador de Categorias Únicas
                categorias_unicas = df["CATEGORIA"].unique()
                
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown(f'<div class="impact-card"><p style="font-size: 0.7rem; color: #64748B;">CATEGORIAS IDENTIFICADAS</p><h2 style="color: #BFAF83;">{len(categorias_unicas)}</h2></div>', unsafe_allow_html=True)
                with c2:
                    st.markdown(f'<div class="impact-card"><p style="font-size: 0.7rem; color: #64748B;">TOTAL RECUPERÁVEL</p><h2 style="color: #BFAF83;">R$ {total_val:,.2f}</h2></div>', unsafe_allow_html=True)
                with c3:
                    st.markdown(f'<div class="impact-card"><p style="font-size: 0.7rem; color: #64748B;">STATUS</p><h2 style="color: #10B981;">AUDITADO</h2></div>', unsafe_allow_html=True)

                # INOVAÇÃO: Resumo Conciso
                st.markdown("<h4 style='color: #BFAF83; font-family: Cinzel;'>RESUMO DE DÉBITOS IDENTIFICADOS</h4>", unsafe_allow_html=True)
                resumo_html = "".join([f"<span style='background: rgba(191,175,131,0.2); padding: 5px 12px; border-radius: 15px; margin-right: 10px; font-size: 0.8rem;'>{cat}</span>" for cat in categorias_unicas])
                st.markdown(f'<div class="resumo-direto">{resumo_html}</div>', unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                st.dataframe(df, use_container_width=True)
                st.download_button("📥 BAIXAR LAUDO TÉCNICO", df.to_csv(index=False).encode('utf-8-sig'), "laudo.csv")

    st.markdown('<div class="footer-signature"><p class="footer-name">Edson Medeiros</p></div>', unsafe_allow_html=True)
