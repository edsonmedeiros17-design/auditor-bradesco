import streamlit as st
import pandas as pd
import unicodedata
import pdfplumber
import io
import re

# ==========================================
# METADADOS E REMOÇÃO TOTAL DE ARTEFATOS PADRÃO
# ==========================================
st.set_page_config(
    page_title="EDSON MEDEIROS | Consultoria & Inteligência Digital",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# ARQUITETURA DE DESIGN ULTRA-PROFISSIONAL (CSS)
# ==========================================
corporate_css = """
<style>
    /* Importação da fonte padrão de interfaces governamentais e bancárias europeias */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
    
    /* Ocultação total e estrita de cabeçalhos, rodapés e menus do Streamlit para parecer um sistema nativo */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none !important;}
    
    /* Suavização de renderização e transição global */
    * {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        transition: background-color 0.3s ease, border-color 0.3s ease;
    }

    /* Fundo Executivo Premium Sólido e Elegante */
    .stApp {
        background-color: #0B0E14 !important;
        color: #F1F5F9 !important;
    }
    
    /* Tipografia de Alta Autoridade */
    h1 {
        font-size: 38px !important;
        font-weight: 700 !important;
        letter-spacing: -0.03em !important;
        color: #FFFFFF !important;
        line-height: 1.2 !important;
        margin-bottom: 8px !important;
    }
    
    .subtitle-executive {
        color: #94A3B8 !important;
        font-size: 16px !important;
        font-weight: 400 !important;
        max-width: 700px;
        line-height: 1.6;
    }
    
    h3 {
        color: #F1F5F9 !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        letter-spacing: -0.01em !important;
        text-transform: uppercase;
        color: #C5A566 !important;
    }

    /* Bloco Organizador Minimalista de Alta Classe */
    .corporate-card {
        background-color: #111622;
        border: 1px solid #1E293B;
        border-radius: 8px;
        padding: 30px;
        margin-bottom: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);
    }
    .corporate-card:hover {
        border-color: #334155;
    }
    
    /* Destaque Ativo de Configurações */
    .active-card {
        border-left: 3px solid #C5A566 !important;
    }

    /* Botões Executivos Foscos com Resposta Touch/Click Limpa */
    div.stButton > button {
        background-color: #C5A566 !important;
        color: #0B0E14 !important;
        border: 1px solid #C5A566 !important;
        border-radius: 6px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        letter-spacing: -0.01em !important;
        transition: all 0.2s ease-in-out !important;
        width: 100%;
    }
    div.stButton > button:hover {
        background-color: #DFBA73 !important;
        border-color: #DFBA73 !important;
        box-shadow: 0 4px 12px rgba(197, 165, 102, 0.2) !important;
        transform: translateY(-1px);
    }
    div.stButton > button:active {
        transform: translateY(0);
    }

    /* Input de Upload Customizado */
    .stFileUploader {
        border: 1px dashed #334155 !important;
        border-radius: 8px !important;
        background-color: #0E131F !important;
        padding: 12px !important;
    }

    /* Divisores Sutis de Alta Precisão */
    .corporate-divider {
        height: 1px;
        background-color: #1E293B;
        margin: 32px 0;
    }
    
    /* Customização fina de tabelas e inputs Streamlit */
    .stMultiSelect div[data-baseweb="select"] {
        background-color: #0E131F !important;
        border: 1px solid #334155 !important;
        border-radius: 6px !important;
    }
</style>
"""
st.markdown(corporate_css, unsafe_allow_html=True)

# ==========================================
# REGRAS DE NEGÓCIO E CONSTANTES (PRESERVADAS)
# ==========================================
RUBRICAS_ALERTA = [
    "CESTA", "PACOTE", "MORA DE OPERAÇÃO", "MORA CREDITO PESSOAL",
    "MORA OPERACAO DE CREDITO", "BX", "PARCELA CREDITO PESSOAL",
    "GASTOS CARTAO DE CREDITO", "SEGURO", "ADIANT", "APLIC",
    "ENCARGOS", "ANUIDADE", "OPERACOES VENCIDAS", "DIV. EM ATRASO"
]

def remover_acentos_e_padronizar(texto):
    if not isinstance(texto, str):
        return ""
    texto_normalizado = unicodedata.normalize('NFD', texto)
    return "".join(c for c in texto_normalizado if unicodedata.category(c) != 'Mn').lower().strip()

def converter_pdf_para_dataframe(pdf_bytes):
    dados_extraidos = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for pagina in pdf.pages:
            texto_da_pagina = pagina.extract_text()
            if not texto_da_pagina:
                continue
            linhas = texto_da_pagina.split("\n")
            for linha in linhas:
                partes = linha.split()
                if len(partes) < 2:
                    continue
                
                tem_data = re.match(r'^\d{2}/\d{2}/\d{4}', partes[0])
                if tem_data:
                    data = partes[0]
                    resto = partes[1:]
                else:
                    data = pd.NA
                    resto = partes
                
                valor = resto[-1] if len(resto) > 0 else ""
                doc = resto[-2] if len(resto) > 1 and resto[-2].isdigit() else ""
                
                if doc:
                    descricao = " ".join(resto[:-2])
                else:
                    descricao = " ".join(resto[:-1])
                
                if descricao:
                    dados_extraidos.append({
                        'Data': data,
                        'Descricao': descricao,
                        'Docto': doc,
                        'Valor': valor
                    })
    return pd.DataFrame(dados_extraidos)

def analisar_e_filtrar_estrito(df_extrato, rubricas_filtradas):
    df = df_extrato.copy()
    df.columns = [c.strip().title() for c in df.columns]
    
    if 'Data' in df.columns and 'Descricao' in df.columns:
        df['Data'] = df['Data'].replace(r'^\s*$', pd.NA, regex=True)
        df['Data'] = df['Data'].bfill()  # Motor de Data Inferior
        
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
        
        # FILTRAGEM ESTRETA EXIGIDA: Apenas DATA, NOME DA RUBRICA, VALOR
        if not df_filtrado_estrito.empty:
            df_filtrado_estrito = df_filtrado_estrito[['Data', 'Rubrica Detectada', 'Valor']]
            df_filtrado_estrito.columns = ['DATA', 'NOME DA RUBRICA', 'VALOR']
        
        return df_filtrado_estrito
        
    return pd.DataFrame()

# ==========================================
# INTERFACE GRÁFICA (ALTA RESOLUÇÃO CORPORATIVA)
# ==========================================

# Barra Topo de Identidade de Marca
st.markdown("""
<div style='display: flex; justify-content: space-between; align-items: center; padding: 10px 0;'>
    <div style='font-size: 13px; letter-spacing: 0.15em; color: #C5A566; font-weight: 700;'>EDSON MEDEIROS</div>
    <div style='font-size: 11px; color: #64748B; font-weight: 500;'>SISTEMA DE COMPLIANCE DIGITAL v3.2</div>
</div>
<div class='corporate-divider' style='margin-top: 10px; margin-bottom: 30px;'></div>
""", unsafe_allow_html=True)

# Seção de Entrada Principal (Hero Alinhado à Esquerda - Estilo Enterprise)
st.markdown("""
<div>
    <h1>Console de Auditoria e Análise Bancária</h1>
    <p class='subtitle-executive'>
        Plataforma restrita para cruzamento de dados analíticos, extração automatizada de passivos e reconciliação cronológica estruturada com motor de retroalimentação temporal.
    </p>
</div>
<div class='corporate-divider'></div>
""", unsafe_allow_html=True)

# Painel Duplo Simétrico de Operações
col1, col2 = st.columns([1.6, 1.4], gap="large")

with col1:
    st.markdown("<div class='corporate-card'><h3>1. Carregamento de Documentos</h3>", unsafe_allow_html=True)
    arquivo_enviado = st.file_uploader("Selecione ou arraste o extrato bancário original para análise imediata", type=["pdf", "csv", "xlsx"])
    st.markdown("<div style='margin: 18px 0; text-align: center; color: #475569; font-size: 11px; font-weight: 600; letter-spacing: 0.05em;'>OU UTILIZE O AMBIENTE DE SIMULAÇÃO</div>", unsafe_allow_html=True)
    simular_dados = st.button("Executar Demonstração com Padrão de Dados Real")
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<div class='corporate-card active-card'><h3>2. Escopo de Monitoramento</h3>", unsafe_allow_html=True)
    rubricas_selecionadas = st.multiselect(
        label="Selecione as rubricas específicas para rastreamento ativo:",
        options=RUBRICAS_ALERTA,
        default=RUBRICAS_ALERTA,
        help="As movimentações que não corresponderem a estes critérios serão integralmente desconsideradas do relatório."
    )
    st.markdown("""
        <div style='margin-top: 20px; font-size: 12px; color: #64748B; line-height: 1.5;'>
            * O motor executa a varredura baseando-se no modelo de <b>Data Inferior</b>, associando débitos sem data explícita ao lote subsequente imediato.
        </div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Processamento da Informação
df_base = None

if arquivo_enviado is not None:
    bytes_do_arquivo = arquivo_enviado.read()
    nome_arquivo = arquivo_enviado.name.lower()
    try:
        if nome_arquivo.endswith('.pdf'):
            with st.spinner("Decodificando strings estruturadas do arquivo PDF..."):
                df_base = converter_pdf_para_dataframe(bytes_do_arquivo)
        elif nome_arquivo.endswith('.csv'):
            df_base = pd.read_csv(io.BytesIO(bytes_do_arquivo))
        else:
            df_base = pd.read_excel(io.BytesIO(bytes_do_arquivo))
    except Exception as e:
        st.error(f"Erro ao processar o arquivo de entrada: {e}")

elif simular_dados:
    dados_simulados = {
        'Data': ['07/02/2017', '', '', '08/02/2017'],
        'Descricao': [
            'SAQUE DINHEIRO ATM',
            'MORA CREDITO PESSOAL', 
            'ENCARGOS LIMITE DE CRED ENCARGO - 14,31%', 
            'SAQUE DIN CORBAN CARTAO ESPECIE'
        ],
        'Docto': ['6017411', '5070038', '8118726', '3714083'],
        'Valor': ['-500,00', '-115,62', '-19,31', '-130,00']
    }
    df_base = pd.DataFrame(dados_simulados)

# Exibição do Relatório Final de Auditoria
if df_base is not None:
    st.markdown("<div class='corporate-divider'></div>", unsafe_allow_html=True)
    relatorio_final = analisar_e_filtrar_estrito(df_base, rubricas_selecionadas)
    
    if relatorio_final.empty:
        st.info("Nenhuma inconsistência contendo as rubricas selecionadas foi detectada neste lote de documentos.")
    else:
        st.markdown("<h2 style='font-size: 20px; font-weight: 600; margin-bottom: 20px;'>Relatório Consolidado de Inconformidades</h2>", unsafe_allow_html=True)
        
        # Grid Executivo de Resumo de Dados
        kpi_col1, kpi_col2 = st.columns(2)
        with kpi_col1:
            st.markdown(f"""
            <div class='corporate-card' style='padding: 20px; text-align: left;'>
                <div style='color: #64748B; font-size: 12px; font-weight: 600; text-transform: uppercase;'>Status da Análise</div>
                <div style='color: #EF4444; font-size: 24px; font-weight: 700; margin-top: 5px;'>REGISTROS DETECTADOS</div>
            </div>
            """, unsafe_allow_html=True)
        with kpi_col2:
            st.markdown(f"""
            <div class='corporate-card' style='padding: 20px; text-align: left;'>
                <div style='color: #64748B; font-size: 12px; font-weight: 600; text-transform: uppercase;'>Total de Ocorrências</div>
                <div style='color: #FFFFFF; font-size: 24px; font-weight: 700; margin-top: 5px;'>{len(relatorio_final)} Lançamentos</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Renderização Limpa e Impecável da Tabela Corporativa
        st.dataframe(
            relatorio_final, 
            use_container_width=True,
            hide_index=True
        )

# Rodapé com Assinatura Legal e Corporativa
st.markdown("""
<div class='corporate-divider' style='margin-top: 60px;'></div>
<div style='display: flex; justify-content: space-between; align-items: center; padding: 10px 0; color: #475569; font-size: 11px; font-weight: 500;'>
    <div>© 2026 EDSON MEDEIROS - CONSULTORIA & INTELIGÊNCIA DIGITAL</div>
    <div>CONVENÇÃO DE SEGURANÇA E PRIVACIDADE DE DADOS ATIVA</div>
</div>
""", unsafe_allow_html=True)
