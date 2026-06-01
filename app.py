import streamlit as st
import pandas as pd
import unicodedata
import pdfplumber
import io
import re

# ==========================================
# METADADOS DA PÁGINA & BLINDAGEM DE INTERFACE
# ==========================================
st.set_page_config(
    page_title="EDSON MEDEIROS | Consultoria & Compliance",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# ESTÉTICA INTERNACIONAL (CSS PREMIUM)
# ==========================================
premium_ui_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none !important;}
    
    .stApp {
        background-color: #101418 !important;
        color: #E2E8F0 !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    
    .brand-gold {
        color: #C5A566 !important;
    }
    
    .section-title {
        font-size: 14px !important;
        font-weight: 600 !important;
        letter-spacing: 0.15em !important;
        color: #C5A566 !important;
        margin-bottom: 20px !important;
        text-transform: uppercase;
    }
    
    .nav-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 24px 0;
        border-bottom: 1px solid rgba(197, 165, 102, 0.1);
    }
    
    .hero-container {
        padding: 90px 0 60px 0;
        max-width: 850px;
    }
    
    .hero-title {
        font-size: 48px !important;
        font-weight: 700 !important;
        line-height: 1.15 !important;
        color: #FFFFFF !important;
        letter-spacing: -0.03em !important;
        margin-bottom: 24px !important;
    }
    
    .premium-card {
        background-color: #14191F;
        border: 1px solid rgba(255, 255, 255, 0.03);
        border-radius: 6px;
        padding: 32px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    }
    
    .stFileUploader {
        border: 1px dashed rgba(197, 165, 102, 0.2) !important;
        border-radius: 6px !important;
        background-color: #13181E !important;
    }
    
    div.stButton > button {
        background-color: transparent !important;
        color: #C5A566 !important;
        border: 1px solid #C5A566 !important;
        border-radius: 4px !important;
        padding: 12px 28px !important;
        font-weight: 500;
        text-transform: uppercase;
        width: 100%;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        background-color: #C5A566 !important;
        color: #101418 !important;
    }
    
    .corporate-divider {
        height: 1px;
        background-color: rgba(255, 255, 255, 0.05);
        margin: 40px 0;
    }
</style>
"""
st.markdown(premium_ui_css, unsafe_allow_html=True)

# ==========================================
# UNIVERSO DE RUBRICAS PADRÃO DE AUDITORIA
# ==========================================
RUBRICAS_ALERTA = [
    "CESTA", "PACOTE", "MORA DE OPERAÇÃO", "MORA CREDITO PESSOAL",
    "MORA OPERACAO DE CREDITO", "BX", "PARCELA CREDITO PESSOAL",
    "GASTOS CARTAO DE CREDITO", "SEGURO", "ADIANT", "APLIC",
    "ENCARGOS", "ANUIDADE", "OPERACOES VENCIDAS", "DIV. EM ATRASO",
    "ENCARGOS LIMITE DE CRED", "CESTA FACIL ECONOMICA", "TARIFA BANCARIA"
]

def remover_acentos_e_padronizar(texto):
    if not isinstance(texto, str):
        return ""
    texto_normalizado = unicodedata.normalize('NFD', texto)
    return "".join(c for c in texto_normalizado if unicodedata.category(c) != 'Mn').lower().strip()

def converter_pdf_para_dataframe(pdf_bytes):
    dados_extraidos = []
    descricao_buffer = []  # Buffer para acumular textos fragmentados entre linhas
    
    # Extração forçando o alinhamento de layout estrutural
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for pagina in pdf.pages:
            texto_da_pagina = pagina.extract_text(layout=True)
            if not texto_da_pagina:
                continue
                
            linhas = texto_da_pagina.split("\n")
            for linha in linhas:
                partes = linha.split()
                if not partes:
                    continue
                
                # Identifica se a linha começa com uma data válida
                tem_data = re.match(r'^\d{2}/\d{2}/\d{4}', partes[0])
                if tem_data:
                    data_linha = partes[0]
                    resto = partes[1:]
                else:
                    data_linha = pd.NA
                    resto = partes
                
                # Procura por padrões numéricos de valores financeiros (Ex: 51,60 ou 1.500,00)
                valores_candidatos = []
                for idx, token in enumerate(resto):
                    if re.search(r'^-?\d+([\.,]\d{2})+$', token) and '%' not in token:
                        valores_candidatos.append(idx)
                
                if valores_candidatos:
                    # Se encontramos valores financeiros, isolamos os índices
                    indices_valores = sorted(valores_candidatos)
                    
                    if len(indices_valores) >= 2:
                        idx_valor = indices_valores[-2]  # Penúltimo número costuma ser o Débito/Crédito
                        valor = resto[idx_valor]
                    else:
                        idx_valor = indices_valores[0]   # Único número encontrado
                        valor = resto[idx_valor]
                    
                    # Remove os valores financeiros para limpar a extração do texto descritivo
                    indices_para_remover = set(indices_valores)
                    resto_sem_valores = [resto[i] for i in range(len(resto)) if i not in indices_para_remover]
                    
                    doc = ""
                    descricao_tokens = []
                    for token in resto_sem_valores:
                        if token.isdigit() and len(token) >= 4:
                            doc = token
                        else:
                            descricao_tokens.append(token)
                    
                    descricao_atual = " ".join(descricao_tokens)
                    
                    # Se havia fragmento de texto acumulado de linhas anteriores, mescla agora
                    if descricao_buffer:
                        descricao_completa = " ".join(descricao_buffer) + " " + descricao_atual
                        descricao_buffer = []  # Limpa o buffer após o consumo
                    else:
                        descricao_completa = descricao_atual
                    
                    dados_extraidos.append({
                        'Data': data_linha,
                        'Descricao': descricao_completa.strip(),
                        'Docto': doc,
                        'Valor': valor
                    })
                else:
                    # SEGURANÇA TOTAL: Linha pura de texto (sem valores numéricos).
                    # Filtra possíveis números de documento soltos e joga o texto no buffer.
                    texto_limpo = " ".join([t for t in resto if not (t.isdigit() and len(t) >= 4)])
                    if texto_limpo:
                        descricao_buffer.append(texto_limpo)
                        
    return pd.DataFrame(dados_extraidos)

def analisar_e_filtrar_estrito(df_extrato, rubricas_filtradas):
    df = df_extrato.copy()
    df.columns = [c.strip().title() for c in df.columns]
    
    if 'Data' in df.columns and 'Descricao' in df.columns:
        # Aplicação perfeita da Regra DATA INFERIOR (Preenchimento reverso de baixo para cima)
        df['Data'] = df['Data'].replace(r'^\s*$', pd.NA, regex=True)
        df['Data'] = df['Data'].bfill()
        
        df['Alerta'] = 'Normal'
        df['Rubrica Detectada'] = 'Nenhuma'
        df['Descricao_Limpa'] = df['Descricao'].apply(remover_acentos_e_padronizar)
        
        for rubrica in rubricas_filtradas:
            rubrica_padrao = remover_acentos_e_padronizar(rubrica)
            condicao = df['Descricao_Limpa'].str.contains(rubrica_padrao, regex=False)
            df.loc[condicao, 'Alerta'] = '⚠️ AUDITAR'
            df.loc[condicao, 'Rubrica Detectada'] = rubrica
            
        df = df.drop(columns=['Descricao_Limpa'])
        df_filtrado_estrito = df[df['Alerta'] == '⚠️ AUDITAR'].copy()
        
        if not df_filtrado_estrito.empty:
            df_filtrado_estrito = df_filtrado_estrito[['Data', 'Rubrica Detectada', 'Valor']]
            df_filtrado_estrito.columns = ['DATA', 'NOME DA RUBRICA', 'VALOR DESCONTADO']
        
        return df_filtrado_estrito
        
    return pd.DataFrame()

# ==========================================
# PAINEL INSTITUCIONAL VISUAL
# ==========================================
st.markdown("""
<div class='nav-container'>
    <div style='font-size: 16px; letter-spacing: 0.15em; font-weight: 700; color: #FFFFFF;'>
        EDSON MEDEIROS <span class='brand-gold' style='font-weight: 300;'>| CONSULTORIA & COMPLIANCE</span>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class='hero-container'>
    <h1 class='hero-title'>Rigor Forense contra Passivos Bancários Indevidos.</h1>
</div>
""", unsafe_allow_html=True)

st.markdown("<div class='section-title'>Console de Inteligência Cambial</div>", unsafe_allow_html=True)

tool_col1, tool_col2 = st.columns([1.6, 1.4], gap="large")

with tool_col1:
    st.markdown("<div style='font-size: 14px; color: #E2E8F0; margin-bottom: 10px; font-weight: 500;'>Entrada de Documentos Digitais</div>", unsafe_allow_html=True)
    arquivo_enviado = st.file_uploader("Arraste ou selecione o arquivo original", type=["pdf", "csv", "xlsx"], label_visibility="collapsed")
    st.markdown("<div style='margin: 15px 0; text-align: center; color: #475569; font-size: 11px; font-weight: 600;'>SIMULAÇÃO ATIVA DE ACORDO COM O SEU ANEXO ENVIADO</div>", unsafe_allow_html=True)
    simular_dados = st.button("Simular Cenário Fiel (Múltiplas Linhas sem Data + Cesta Fácil)")

with tool_col2:
    st.markdown("<div style='font-size: 14px; color: #E2E8F0; margin-bottom: 10px; font-weight: 500;'>Parametrização de Busca</div>", unsafe_allow_html=True)
    rubricas_selecionadas = st.multiselect(
        label="Parâmetros ativos",
        options=RUBRICAS_ALERTA,
        default=["CESTA", "MORA CREDITO PESSOAL", "ENCARGOS LIMITE DE CRED"],
        label_visibility="collapsed"
    )

df_base = None

if arquivo_enviado is not None:
    bytes_do_arquivo = arquivo_enviado.read()
    nome_arquivo = arquivo_enviado.name.lower()
    try:
        if nome_arquivo.endswith('.pdf'):
            df_base = converter_pdf_para_dataframe(bytes_do_arquivo)
        elif nome_arquivo.endswith('.csv'):
            df_base = pd.read_csv(io.BytesIO(bytes_do_arquivo))
        else:
            df_base = pd.read_excel(io.BytesIO(bytes_do_arquivo))
    except Exception as e:
        st.error(f"Erro no processamento: {e}")

elif simular_dados:
    # Cenário montado baseado estritamente na imagem f05b84 que você enviou:
    # Duas movimentações acima órfãs de data, herdando a data inferior "17/08/2023"
    dados_simulados = {
        'Data': [pd.NA, pd.NA, '17/08/2023'],
        'Descricao': [
            'COMPRA ELO DEBITO VISTA COMERCIAL DALLAS', 
            'TARIFA BANCARIA CESTA FACIL ECONOMICA', 
            'COMPRA ELO DEBITO VISTA DROGAFARMA'
        ],
        'Docto': ['0198663', '0010823', '0257481'],
        'Valor': ['100,32', '51,60', '9,00']
    }
    df_base = pd.DataFrame(dados_simulados)

if df_base is not None:
    relatorio_final = analisar_e_filtrar_estrito(df_base, rubricas_selecionadas)
    st.markdown("<br>", unsafe_allow_html=True)
    
    if relatorio_final.empty:
        st.info("Nenhuma inconsistência contendo as rubricas selecionadas foi detectada.")
    else:
        st.markdown("<div style='font-size: 14px; color: #C5A566; font-weight: 600; margin-bottom: 15px;'>RESULTADO DA EXTRAÇÃO (DATA INFERIOR CORRIGIDA)</div>", unsafe_allow_html=True)
        st.dataframe(relatorio_final, use_container_width=True, hide_index=True)

st.markdown("""
<div class='corporate-divider'></div>
<div style='color: #475569; font-size: 11px;'>© 2026 EDSON MEDEIROS - CONSULTORIA & COMPLIANCE.</div>
""", unsafe_allow_html=True)
