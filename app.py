import streamlit as st
import pdfplumber
import pandas as pd
import re

# --- CONFIGURAÇÃO DE ELITE ---
st.set_page_config(page_title="Edson Medeiros | Consultoria de Ativos", layout="wide", page_icon="⚖️")

# --- CSS ARCHITECTURE (REFINAMENTO EMPRESARIAL) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600&family=Playfair+Display:wght@700&family=Inter:wght@300;400;600&family=Great+Vibes&display=swap');

    :root {
        --navy-deep: #0F172A;
        --gold-matte: #BFAF83;
        --emerald-success: #10B981;
    }

    /* Fundo imersivo com vinheta técnica */
    .stApp { 
        background: radial-gradient(circle at center, #1E293B 0%, #0F172A 100%); 
        color: #F8F9FA;
    }

    /* Título 3D Estilo Times New Roman Modernizado */
    .consultoria-title {
        font-family: 'Playfair Display', serif;
        font-size: 4rem;
        background: linear-gradient(180deg, #FFFFFF 0%, #BFAF83 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0px 10px 20px rgba(0,0,0,0.4);
        margin-bottom: 5px;
    }

    /* Cards de Impacto (Valor Percebido) */
    .impact-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(191, 175, 131, 0.2);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        transition: 0.3s;
    }
    .impact-card:hover { border-color: var(--gold-matte); background: rgba(255, 255, 255, 0.08); }

    /* Estilização da Sidebar Profissional */
    [data-testid="stSidebar"] { background-color: #080C14 !important; border-right: 1px solid #1E293B; }
    [data-testid="stSidebar"] h3 { color: var(--gold-matte) !important; font-family: 'Cinzel', serif; letter-spacing: 1px; }

    /* Assinatura Edson Medeiros */
    .footer-signature {
        position: fixed;
        bottom: 30px;
        right: 40px;
        text-align: right;
    }
    .footer-name { font-family: 'Great Vibes', cursive; color: var(--gold-matte); font-size: 2rem; margin: 0; }
    .footer-tech { font-family: 'Inter', sans-serif; font-size: 0.7rem; color: #64748B; letter-spacing: 3px; }
    </style>
    """, unsafe_allow_html=True)

# --- CABEÇALHO ---
st.markdown('<h1 class="consultoria-title">Consultoria de Ativos</h1>', unsafe_allow_html=True)
st.markdown("<p style='color: #BFAF83; letter-spacing: 2px; font-weight: 300; margin-bottom: 40px;'>AUDITORIA TÉCNICA PROPRIETÁRIA DE EXTRATOS BANCÁRIOS</p>", unsafe_allow_html=True)

# --- SIDEBAR (CONFIGURAÇÃO TÉCNICA) ---
st.sidebar.markdown("### ESCOPO DA ANÁLISE")
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

# --- APP INTERFACE ---
upload = st.file_uploader("Submeta o arquivo PDF para certificação de auditoria", type="pdf")

if upload and selecionados:
    with st.spinner('Realizando cruzamento de dados...'):
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
            # DASHBOARD DE CONSULTORIA (VALOR PERCEBIDO)
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f'<div class="impact-card"><p style="font-size: 0.8rem; color: #64748B;">OCORRÊNCIAS</p><h2 style="color: #BFAF83;">{len(df)}</h2></div>', unsafe_allow_html=True)
            with c2:
                st.markdown(f'<div class="impact-card"><p style="font-size: 0.8rem; color: #64748B;">CATEGORIAS</p><h2 style="color: #BFAF83;">{df["CATEGORIA"].nunique()}</h2></div>', unsafe_allow_html=True)
            with c3:
                st.markdown(f'<div class="impact-card"><p style="font-size: 0.8rem; color: #64748B;">STATUS</p><h2 style="color: #10B981;">AUDITADO</h2></div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # EXPORTAÇÃO
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 BAIXAR RELATÓRIO CERTIFICADO (CSV)", csv, "auditoria_medeiros.csv", "text/csv")
        else:
            st.info("Nenhuma irregularidade encontrada nos parâmetros selecionados.")

# --- FOOTER ---
st.markdown(f"""
    <div class="footer-signature">
        <p class="footer-name">Edson Medeiros</p>
        <p class="footer-tech">EDSON MEDEIROS CONSULTORIA & COMPLIANCE</p>
    </div>
    """, unsafe_allow_html=True)
