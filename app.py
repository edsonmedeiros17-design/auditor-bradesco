import streamlit as st
import pdfplumber
import pandas as pd
import re
from PIL import Image
import pytesseract

# --- 1. CONFIGURAÇÃO DE DESIGN E ESTÉTICA LUXUOSA ---
st.set_page_config(page_title="Edson Medeiros | Consultoria de Ativos", layout="wide", page_icon="⚖️")

ESTILO_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600&family=Playfair+Display:ital,wght@0,700;1,700&family=Inter:wght@300;400;600&family=Great+Vibes&display=swap');
:root { --navy: #0F172A; --gold: #BFAF83; --off-white: #F8F9FA; }
.stApp { background: radial-gradient(circle at center, #1E293B 0%, #0F172A 100%); color: var(--off-white); font-family: 'Inter', sans-serif; }

.consultoria-title { 
    font-family: 'Playfair Display', serif !important; 
    font-size: 4.5rem !important; 
    background: linear-gradient(180deg, #FFFFFF 0%, #BFAF83 100%); 
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
    text-shadow: 0px 4px 10px rgba(0,0,0,0.5); text-align: center; line-height: 1.1;
}

.impact-card { 
    background: rgba(255, 255, 255, 0.05); 
    border: 1px solid rgba(191, 175, 131, 0.3); 
    border-radius: 15px; padding: 25px; text-align: center;
    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
}

.step-card {
    background: rgba(15, 23, 42, 0.6);
    border-left: 3px solid var(--gold);
    padding: 20px; border-radius: 8px; margin-bottom: 20px;
}

.footer-name { font-family: 'Great Vibes', cursive; color: var(--gold); font-size: 2.5rem; text-align: right; }
</style>
"""
st.markdown(ESTILO_CSS, unsafe_allow_html=True)

# --- 2. PARÂMETROS DE BUSCA (RESTABELECIDOS) ---
DICIONARIO_ALVOS = {
    "CESTA/PACOTE": r"CESTA|PACOTE|TARIFA BANC",
    "MORA CREDITO PESSOAL": r"MORA CRED PESS|MORA CRÉDITO",
    "MORA OPERACAO": r"MORA OPER|MORA DE OPERAÇÃO",
    "ENCARGOS LIMITE": r"ENC LIM CREDITO|ENCARGOS",
    "PARCELA CREDITO": r"PARC CRED PESS|PARCELA CRÉDITO",
    "GASTOS CARTAO": r"CART CRED ANUID|ANUIDADE|GASTOS CARTÃO",
    "SEGURO": r"SEGURO|SEGURADORA",
    "IOF": r"IOF UTIL LIMITE|IOF S/ UTIL",
    "ADIANT. DEPOSITANTE": r"ADIANT|DEP DINHEIRO",
    "OPERACOES VENCIDAS": r"OPERAÇÕES VENCIDAS|DIV\. EM ATRASO",
    "BX": r"BX ",
}

# --- 3. MOTOR DE AUDITORIA COM FILTRO DE CRÉDITO (AZUL) ---
def auditoria_precisa(arquivo):
    resultados = []
    with pdfplumber.open(arquivo) as pdf:
        for page in pdf.pages:
            # Extração baseada em estrutura de tabela para separar Débito de Crédito
            tabela = page.extract_table({
                "vertical_strategy": "text", 
                "horizontal_strategy": "text",
                "snap_tolerance": 4
            })
            
            if not tabela: continue
            
            for linha in tabela:
                # Filtragem de segurança: Uma linha válida precisa de dados e histórico
                if len(linha) < 4: continue
                
                texto_linha = " ".join([str(c) for c in linha if c]).upper()
                
                for cat, regex in DICIONARIO_ALVOS.items():
                    if re.search(regex, texto_linha):
                        # MAPEAMENTO DE COLUNAS BRADESCO/GENÉRICO:
                        # [0]Data | [1]Histórico | [2]Docto | [3]Crédito | [4]Débito | [5]Saldo
                        
                        # Pegamos o valor da penúltima coluna (Débito)
                        try:
                            val_credito = linha[-3] if len(linha) >= 6 else None
                            val_debito = linha[-2] if len(linha) >= 6 else linha[-1]
                            
                            # REGRA DE OURO: Se o débito estiver vazio ou for o crédito (azul), ignora.
                            if not val_debito or val_debito in ["", "0,00", None]:
                                continue
                            
                            # Se houver valor no crédito, mas o robô se confundiu, verificamos se o débito existe
                            if val_credito and "," in str(val_credito) and not (val_debito and "," in str(val_debito)):
                                continue

                            resultados.append({
                                "DATA": linha[0],
                                "CATEGORIA": cat,
                                "VALOR DÉBITO (R$)": val_debito,
                                "ORIGEM": linha[1][:40]
                            })
                        except:
                            continue
                        break
    return resultados

# --- 4. INTERFACE PRINCIPAL ---
st.markdown('<h1 class="consultoria-title">Consultoria de Ativos</h1>', unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#BFAF83; letter-spacing:2px;'>SISTEMA DE AUDITORIA TÉCNICA V.2026</p>", unsafe_allow_html=True)

# Sidebar com os parâmetros restaurados
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/584/584011.png", width=50)
st.sidebar.markdown("### FILTROS DE AUDITORIA")
selecionados = [k for k in DICIONARIO_ALVOS.keys() if st.sidebar.checkbox(k, value=True)]

# Área de Upload (3 Passos)
st.markdown("<br>", unsafe_allow_html=True)
upload = st.file_uploader("📂 ARRASTE O EXTRATO BANCÁRIO (PDF) PARA ANÁLISE", type=["pdf"])

if upload:
    with st.spinner('AUDITANDO COLUNAS... IGNORANDO CRÉDITOS (AZUL)'):
        dados_finais = auditoria_precisa(upload)
        
        if dados_finais:
            df = pd.DataFrame(dados_finais)
            
            # Cards de Impacto Organizadom
            c1, c2 = st.columns(2)
            total_float = sum([float(v.replace('.','').replace(',','.')) for v in df["VALOR DÉBITO (R$)"]])
            
            with c1:
                st.markdown(f'<div class="impact-card"><h4>DÉBITOS IDENTIFICADOS</h4><h2 style="color:#BFAF83;">{len(df)}</h2></div>', unsafe_allow_html=True)
            with c2:
                st.markdown(f'<div class="impact-card"><h4>TOTAL RECUPERÁVEL</h4><h2 style="color:#BFAF83;">R$ {total_float:,.2f}</h2></div>', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.dataframe(df, use_container_width=True)
            st.download_button("📥 BAIXAR LAUDO TÉCNICO (CSV)", df.to_csv(index=False).encode('utf-8-sig'), "laudo_auditoria.csv")
        else:
            st.warning("Nenhum débito indevido encontrado com os parâmetros atuais. Créditos foram filtrados.")

# --- 5. RODAPÉ TÉCNICO (3 PASSOS) ---
st.markdown("<br><hr style='border-color: rgba(191,175,131,0.2);'><br>", unsafe_allow_html=True)
col_a, col_b, col_c = st.columns(3)

with col_a:
    st.markdown('<div class="step-card"><strong>I - Identificação Digital</strong><br><small>Varredura de rubricas e códigos bancários via OCR de alta sensibilidade.</small></div>', unsafe_allow_html=True)
with col_b:
    st.markdown('<div class="step-card"><strong>II - Extração Técnica</strong><br><small>Isolamento de colunas de débito, expurgando entradas de crédito ou saldos.</small></div>', unsafe_allow_html=True)
with col_c:
    st.markdown('<div class="step-card"><strong>III - Certificação</strong><br><small>Geração de relatório técnico para instrução de processos de recuperação.</small></div>', unsafe_allow_html=True)

st.markdown('<p class="footer-name">Edson Medeiros</p>', unsafe_allow_html=True)
