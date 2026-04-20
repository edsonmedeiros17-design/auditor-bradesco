import streamlit as st
import pdfplumber
import pandas as pd
import re
from datetime import datetime

# --- 1. CONFIGURAÇÃO E ESTÉTICA PREMIUM (IMUTÁVEL) ---
st.set_page_config(page_title="Edson Medeiros | Consultoria de Ativos", layout="wide", page_icon="⚖️")

ESTILO_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600&family=Playfair+Display:ital,wght@0,700;1,700&family=Inter:wght@300;400;600&family=Great+Vibes&display=swap');
:root { --navy-deep: #0F172A; --gold-matte: #BFAF83; --emerald-success: #10B981; --off-white: #F8F9FA; }
.stApp { background: radial-gradient(circle at center, #1E293B 0%, #0F172A 100%); color: var(--off-white); font-family: 'Inter', sans-serif; }
.consultoria-title { font-family: 'Playfair Display', serif !important; font-size: 4.5rem !important; font-weight: 700 !important; background: linear-gradient(180deg, #FFFFFF 0%, #BFAF83 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 0px 2px 0px #8A7650, 0px 4px 10px rgba(0,0,0,0.5); line-height: 1.1; margin-bottom: 5px; }
.btn-whatsapp { background-color: #25D366 !important; color: white !important; padding: 14px 28px !important; border-radius: 50px !important; text-decoration: none !important; font-weight: bold !important; display: inline-block !important; transition: 0.3s !important; box-shadow: 0 4px 15px rgba(37, 211, 102, 0.4) !important; text-align: center; border: none !important; }
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

# --- 2. TELA DE ACESSO RESTRITO (LOGIN OBRIGATÓRIO) ---
def check_auth():
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False

    if not st.session_state["autenticado"]:
        _, col_login, _ = st.columns([1, 1.5, 1])
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
                    st.error("Credenciais inválidas. Verifique seu login.")
            
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.markdown('<div style="text-align: center;"><a href="https://contate.me/5592995087379" class="btn-whatsapp" target="_blank">Falar com Consultor ⚖️</a></div>', unsafe_allow_html=True)
        return False
    return True

if check_auth():
    # --- 3. INTERFACE PRINCIPAL ---
    col_head, col_cta = st.columns([2.5, 1])
    with col_head:
        st.markdown('<h1 class="consultoria-title">Consultoria de Ativos</h1>', unsafe_allow_html=True)
        st.markdown("<p style='color: #BFAF83; letter-spacing: 2px; font-size: 0.9rem;'>AUDITORIA TÉCNICA PROPRIETÁRIA DE EXTRATOS</p>", unsafe_allow_html=True)
    with col_cta:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown('<a href="https://contate.me/5592995087379" class="btn-whatsapp" target="_blank">Suporte Direto ⚖️</a>', unsafe_allow_html=True)

    # --- 4. SIDEBAR E PARÂMETROS ---
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
    selecionados = [n for n in DICIONARIO_ALVOS.keys() if st.sidebar.checkbox(n, value=True)]
    
    st.sidebar.markdown("<br>### PERÍODO DE AUDITORIA", unsafe_allow_html=True)
    usar_data = st.sidebar.checkbox("Ativar Limite (Prescrição)")
    if usar_data:
        d_inf = st.sidebar.date_input("Início", format="DD/MM/YYYY")
        d_sup = st.sidebar.date_input("Fim", format="DD/MM/YYYY")

    # --- 5. PROCESSAMENTO TÉCNICO COM LÓGICA DE DATAS HÍBRIDA ---
    st.markdown("<br>", unsafe_allow_html=True)
    upload = st.file_uploader("Submeta o arquivo PDF para certificação técnica automática", type="pdf")

    if upload:
        with st.spinner('Auditando Ativos e Validando Cronologia...'):
            dados = []
            termos = [DICIONARIO_ALVOS[f] for f in selecionados]
            
            with pdfplumber.open(upload) as pdf:
                for p in pdf.pages:
                    linhas = p.extract_text().split('\n') if p.extract_text() else []
                    
                    for i, linha in enumerate(linhas):
                        for t in termos:
                            if re.search(t, linha, re.IGNORECASE):
                                # LÓGICA DE DATA HÍBRIDA (SUP/INF)
                                data_final = "---"
                                m_linha = re.search(r'(\d{2}/\d{2}/\d{4})', linha)
                                
                                if m_linha:
                                    data_final = m_linha.group(1)
                                else:
                                    # Tenta Superior (Anexo 2)
                                    for j in range(i-1, -1, -1):
                                        m_up = re.search(r'(\d{2}/\d{2}/\d{4})', linhas[j])
                                        if m_up:
                                            data_final = m_up.group(1)
                                            break
                                    # Tenta Inferior (Anexo 3)
                                    if data_final == "---":
                                        for k in range(i+1, min(i+10, len(linhas))):
                                            m_down = re.search(r'(\d{2}/\d{2}/\d{4})', linhas[k])
                                            if m_down:
                                                data_final = m_down.group(1)
                                                break

                                if usar_data and data_final != "---":
                                    try:
                                        dt_val = datetime.strptime(data_final, "%d/%m/%Y").date()
                                        if dt_val < d_inf or dt_val > d_sup: continue
                                    except: pass

                                v_m = re.findall(r'(\d[\d\.]*,\d{2})', linha)
                                valor = v_m[-1] if v_m else "0,00"
                                cat_nome = next(k for k, v in DICIONARIO_ALVOS.items() if v == t)
                                
                                dados.append({
                                    "DATA": data_final,
                                    "CATEGORIA": cat_nome.upper(),
                                    "DESCRIÇÃO": linha.strip()[:100],
                                    "VALOR (R$)": valor
                                })
                                break

            if dados:
                df = pd.DataFrame(dados)
                total_rec = sum([float(v.replace('.','').replace(',','.')) for v in df["VALOR (R$)"]])
                cats_unicas = df["CATEGORIA"].unique()
                
                # --- CARDS DE IMPACTO (INOVAÇÃO CATEGORIAS) ---
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown(f'<div class="impact-card"><p style="font-size: 0.7rem; color: #64748B;">CATEGORIAS IDENTIFICADAS</p><h2 style="color: #BFAF83; font-family: Cinzel;">{len(cats_unicas)}</h2></div>', unsafe_allow_html=True)
                with c2:
                    st.markdown(f'<div class="impact-card"><p style="font-size: 0.7rem; color: #64748B;">TOTAL RECUPERÁVEL</p><h2 style="color: #BFAF83; font-family: Cinzel;">R$ {total_rec:,.2f}</h2></div>', unsafe_allow_html=True)
                with c3:
                    st.markdown(f'<div class="impact-card"><p style="font-size: 0.7rem; color: #64748B;">STATUS</p><h2 style="color: #10B981; font-family: Cinzel;">AUDITADO</h2></div>', unsafe_allow_html=True)

                # --- RESUMO CONCISO (INOVAÇÃO BADGES) ---
                st.markdown("<h4 style='color: #BFAF83; font-family: Cinzel; font-size: 1rem; margin-bottom: 15px;'>DÉBITOS IDENTIFICADOS (VISÃO RESUMIDA)</h4>", unsafe_allow_html=True)
                badges_html = "".join([f'<div class="categoria-badge">{cat}</div>' for cat in cats_unicas])
                st.markdown(f'<div class="resumo-direto">{badges_html}</div>', unsafe_allow_html=True)

                st.dataframe(df, use_container_width=True)
                st.download_button("📥 BAIXAR LAUDO TÉCNICO COMPLETO", df.to_csv(index=False).encode('utf-8-sig'), "laudo_medeiros.csv")
            else:
                st.info("Nenhum débito indevido encontrado no período e parâmetros selecionados.")

    # --- 6. PROCESSO DE CONSULTORIA (3 PASSOS) ---
    st.markdown("""
    <div class="how-it-works">
        <h3 style="font-family: 'Cinzel', serif; color: #BFAF83; text-align: center; margin-bottom: 40px; letter-spacing: 2px;">PROCESSO DE CONSULTORIA</h3>
        <div style="display: flex; justify-content: space-around; gap: 30px; flex-wrap: wrap; text-align: center;">
            <div style="flex: 1; min-width: 250px;">
                <div class="step-number">I</div>
                <p style="font-weight: 600; color: #FFF;">Identificação Digital</p>
                <p style="font-size: 0.8rem; color: #94A3B8;">O robô cruza siglas bancárias com o banco de dados de tarifas abusivas.</p>
            </div>
            <div style="flex: 1; min-width: 250px;">
                <div class="step-number">II</div>
                <p style="font-weight: 600; color: #FFF;">Extração de Valores</p>
                <p style="font-size: 0.8rem; color: #94A3B8;">Captura precisa de cada centavo debitado indevidamente no extrato.</p>
            </div>
            <div style="flex: 1; min-width: 250px;">
                <div class="step-number">III</div>
                <p style="font-weight: 600; color: #FFF;">Certificação de Ativos</p>
                <p style="font-size: 0.8rem; color: #94A3B8;">Geração de laudo técnico com o valor total para pedido de restituição.</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- 7. ASSINATURA FINAL ---
    st.markdown('<div class="footer-signature"><p class="footer-name">Edson Medeiros</p><p style="font-size: 0.7rem; color: #64748B; letter-spacing: 3px;">CONSULTORIA & COMPLIANCE</p></div>', unsafe_allow_html=True)
