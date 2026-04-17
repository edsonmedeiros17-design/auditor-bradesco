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
        --emerald-success: #10B981;
        --off-white: #F8F9FA;
    }

    /* Fundo imersivo */
    .stApp { 
        background: radial-gradient(circle at center, #1E293B 0%, #0F172A 100%); 
        color: var(--off-white);
        font-family: 'Inter', sans-serif;
    }

    /* NÚMERO 1: TÍTULO SOFISTICADO COM EFEITO 3D */
    .consultoria-title {
        font-family: 'Playfair Display', serif !important;
        font-size: 4.5rem !important;
        font-weight: 700 !important;
        background: linear-gradient(180deg, #FFFFFF 0%, #BFAF83 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 
            0px 2px 0px #8A7650,
            0px 4px 10px rgba(0,0,0,0.5);
        line-height: 1.1;
        margin-bottom: 5px;
    }

    /* BOTÃO WHATSAPP (DESTAQUE VERMELHO NO SEU PRINT, MAS EM VERDE OFICIAL) */
    .btn-whatsapp {
        background-color: #25D366 !important;
        color: white !important;
        padding: 14px 28px !important;
        border-radius: 50px !important;
        text-decoration: none !important;
        font-weight: bold !important;
        font-family: 'Inter', sans-serif !important;
        display: inline-block !important;
        transition: 0.3s !important;
        box-shadow: 0 4px 15px rgba(37, 211, 102, 0.4) !important;
        border: none !important;
        text-align: center;
    }
    .btn-whatsapp:hover { 
        transform: scale(1.05); 
        background-color: #128C7E !important; 
    }

    /* CARDS DE IMPACTO */
    .impact-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(191, 175, 131, 0.2);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    }

    /* SEÇÃO COMO FUNCIONA */
    .how-it-works {
        background: rgba(15, 23, 42, 0.6);
        border-radius: 16px;
        padding: 40px;
        margin-top: 60px;
        border: 1px solid rgba(191, 175, 131, 0.1);
    }
    .step-number {
        color: var(--gold-matte);
        font-family: 'Cinzel', serif;
        font-size: 1.8rem;
        margin-bottom: 10px;
    }

    /* SIDEBAR */
    [data-testid="stSidebar"] { background-color: #080C14 !important; border-right: 1px solid #1E293B; }
    [data-testid="stSidebar"] h3 { color: var(--gold-matte) !important; font-family: 'Cinzel', serif; }

    /* NÚMERO 3: ASSINATURA EDSON MEDEIROS */
    .footer-signature {
        position: fixed;
        bottom: 30px;
        right: 40px;
        text-align: right;
        z-index: 100;
    }
    .footer-name { font-family: 'Great Vibes', cursive; color: var(--gold-matte); font-size: 2.2rem; margin: 0; }
    .footer-tech { font-family: 'Inter', sans-serif; font-size: 0.7rem; color: #64748B; letter-spacing: 3px; text-transform: uppercase; }

    /* ESTILO DO UPLOAD */
    .stFileUploader section { background-color: rgba(255,255,255,0.03) !important; border: 1px dashed var(--gold-matte) !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CABEÇALHO COM LINK DO WHATSAPP REAL ---
col_head, col_cta = st.columns([2.5, 1])

with col_head:
    st.markdown('<h1 class="consultoria-title">Consultoria de Ativos</h1>', unsafe_allow_html=True)
    st.markdown("<p style='color: #BFAF83; letter-spacing: 2px; font-weight: 300;'>AUDITORIA TÉCNICA PROPRIETÁRIA DE EXTRATOS</p>", unsafe_allow_html=True)

with col_cta:
    st.markdown("<br><br>", unsafe_allow_html=True)
    # LINK DO SEU WHATSAPP INTEGRADO AQUI
    st.markdown(f'''
        <a href="https://contate.me/5592995087379" class="btn-whatsapp" target="_blank">
            Falar com Consultor ⚖️
        </a>
    ''', unsafe_allow_html=True)

# --- 4. BARRA LATERAL (FILTROS) ---
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
selecionados = []
for nome in DICIONARIO_ALVOS.keys():
    if st.sidebar.checkbox(nome, value=True):
        selecionados.append(nome)

# --- 5. INTERFACE DE UPLOAD ---
st.markdown("<br>", unsafe_allow_html=True)
upload = st.file_uploader("Submeta o arquivo PDF para certificação automática", type="pdf", label_visibility="visible")

# --- 6. LÓGICA DE AUDITORIA ---
if upload and selecionados:
    with st.spinner('Realizando cruzamento técnico de dados...'):
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
            # Cards de Resumo
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f'<div class="impact-card"><p style="font-size: 0.7rem; color: #64748B;">OCORRÊNCIAS</p><h2 style="color: #BFAF83;">{len(df)}</h2></div>', unsafe_allow_html=True)
            with c2:
                st.markdown(f'<div class="impact-card"><p style="font-size: 0.7rem; color: #64748B;">CATEGORIAS</p><h2 style="color: #BFAF83;">{df["CATEGORIA"].nunique()}</h2></div>', unsafe_allow_html=True)
            with c3:
                st.markdown(f'<div class="impact-card"><p style="font-size: 0.7rem; color: #64748B;">STATUS</p><h2 style="color: #10B981;">AUDITADO</h2></div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 BAIXAR RELATÓRIO CERTIFICADO (CSV)", csv, "auditoria_medeiros.csv", "text/csv")
        else:
            st.info("Nenhuma divergência identificada nos parâmetros selecionados.")

# --- 7. SEÇÃO INFORMATIVA: COMO FUNCIONA ---
st.markdown("""
    <div class="how-it-works">
        <h3 style="font-family: 'Cinzel', serif; color: #BFAF83; text-align: center; margin-bottom: 40px; letter-spacing: 2px;">PROCESSO DE CONSULTORIA</h3>
        <div style="display: flex; justify-content: space-around; gap: 30px; flex-wrap: wrap; text-align: center;">
            <div style="flex: 1; min-width: 250px;">
                <div class="step-number">I</div>
                <p style="font-weight: 600; color: #FFF;">Upload Seguro</p>
                <p style="font-size: 0.8rem; color: #94A3B8;">O sistema processa seu PDF em milissegundos. Seus dados nunca são armazenados.</p>
            </div>
            <div style="flex: 1; min-width: 250px;">
                <div class="step-number">II</div>
                <p style="font-weight: 600; color: #FFF;">Análise de Siglas</p>
                <p style="font-size: 0.8rem; color: #94A3B8;">Nossa inteligência identifica cobranças escondidas sob siglas bancárias complexas.</p>
            </div>
            <div style="flex: 1; min-width: 250px;">
                <div class="step-number">III</div>
                <p style="font-weight: 600; color: #FFF;">Laudo Técnico</p>
                <p style="font-size: 0.8rem; color: #94A3B8;">Você recebe a base técnica para solicitar reembolsos e correções diretamente ao banco.</p>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- 8. FOOTER OFICIAL (NÚMERO 3) ---
st.markdown(f"""
    <div class="footer-signature">
        <p class="footer-name">Edson Medeiros</p>
        <p class="footer-tech">CONSULTORIA & COMPLIANCE</p>
    </div>
    """, unsafe_allow_html=True)
