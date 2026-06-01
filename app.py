import streamlit as st
import pandas as pd
import unicodedata
import pdfplumber
import io
import re

# ==========================================
# CONFIGURAÇÃO DE METADADOS DA PÁGINA
# ==========================================
st.set_page_config(
    page_title="EDSON MEDEIROS | Consultoria & Inteligência Digital",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# UI/UX MASTER-LEVEL: ESTÉTICA CYBER-LUXO
# ==========================================
master_css = """
<style>
    /* Importação de fontes e animações de core */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes glowPulse {
        0% { border-color: rgba(197, 165, 102, 0.2); box-shadow: 0 0 5px rgba(197, 165, 102, 0.1); }
        50% { border-color: rgba(197, 165, 102, 0.6); box-shadow: 0 0 20px rgba(197, 165, 102, 0.3); }
        100% { border-color: rgba(197, 165, 102, 0.2); box-shadow: 0 0 5px rgba(197, 165, 102, 0.1); }
    }
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* Reset e Fundo Global Escuro Profundo */
    .stApp {
        background: radial-gradient(circle at top right, #141A24, #080B0E) !important;
        color: #E2E8F0 !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Títulos Magnéticos com Gradiente Metálico Dourado */
    h1 {
        font-size: 46px !important;
        font-weight: 700 !important;
        background: linear-gradient(90px, #FFFFFF, #C5A566, #E5C158, #FFFFFF);
        background-size: 200% auto;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        animation: gradientShift 6s ease infinite, fadeInUp 0.8s cubic-bezier(0.16, 1, 0.3, 1);
        letter-spacing: -1px !important;
    }
    
    h3 {
        color: #C5A566 !important;
        font-weight: 600 !important;
        font-size: 19px !important;
        letter-spacing: 0.5px;
    }

    /* Cartões Estilo Glassmorphism Avançado */
    .master-card {
        background: rgba(22, 28, 38, 0.6);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 20px;
        transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
        animation: fadeInUp 0.8s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .master-card:hover {
        transform: translateY(-4px);
        border-color: rgba(197, 165, 102, 0.3);
        background: rgba(26, 34, 46, 0.8);
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.4);
    }
    
    /* Cartão de Destaque com Pulsação Ativa de Brilho */
    .auditor-card-active {
        border: 1px solid rgba(197, 165, 102, 0.2);
        animation: glowPulse 3s infinite ease-in-out, fadeInUp 0.8s cubic-bezier(0.16, 1, 0.3, 1);
    }

    /* Botões Customizados de Alta Resposta */
    div.stButton > button {
        background: linear-gradient(135deg, #1A2332, #111823) !important;
        color: #C5A566 !important;
        border: 1px solid rgba(197, 165, 102, 0.4) !important;
        border-radius: 6px !important;
        padding: 12px 28px !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        letter-spacing: 1px !important;
        text-transform: uppercase;
        transition: all 0.3s ease !important;
        width: 100%;
    }
    div.stButton > button:hover {
        color: #080B0E !important;
        background: linear-gradient(135deg, #E5C158, #C5A566) !important;
        border-color: #E5C158 !important;
        box-shadow: 0 0 20px rgba(197, 165, 102, 0.5) !important;
        transform: scale(1.01);
    }

    /* Inputs e File Uploader Customizados */
    .stFileUploader {
        border: 2px dashed rgba(197, 165, 102, 0.2) !important;
        border-radius: 10px !important;
        background: rgba(16, 20, 28, 0.4) !important;
        padding: 10px !important;
        transition: border-color 0.3s ease;
    }
    .stFileUploader:hover {
        border-color: #C5A566 !important;
    }

    /* Linhas Divisórias de Neon Sutil */
    .master-divider {
        height: 1px;
        background: linear-gradient(90deg, rgba(197,165,102,0) 0%, rgba(197,165,102,0.3) 50%, rgba(197,165,102,0) 100%);
        margin: 35px 0;
    }
</style>
"""
st.markdown(master_css, unsafe_allow_html=True)

# ==========================================
# PARAMETRIZAÇÃO DAS 15 RUBRICAS EXATAS
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
    """
    Extrai o texto original do PDF linha por linha com fidelidade total de caracteres.
    """
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
    """
    Executa a inteligência de Data Inferior e filtra EXCLUSIVAMENTE
    as rubricas de interesse, descartando qualquer ruído.
    """
    df = df_extrato.copy()
    df.columns = [c.strip().title() for c in df.columns]
    
    if 'Data' in df.columns and 'Descricao' in df.columns:
        # 1. Assegura integridade dos nulos antes de aplicar o preenchimento reverso
        df['Data'] = df['Data'].replace(r'^\s*$', pd.NA, regex=True)
        
        # 2. FIDELIDADE COMPLETA: Vincula transações sem data ao lote inferior correta (.bfill)
        df['Data'] = df['Data'].bfill()
        
        df['Alerta'] = 'Normal'
        df['Rubrica Detectada'] = 'Nenhuma'
        df['Descricao_Limpa'] = df['Descricao'].apply(remover_acentos_e_padronizar)
        
        # 3. Varredura de correspondência estrita
        for rubrica in rubricas_filtradas:
            rubrica_padrao = remover_acentos_e_padronizar(rubrica)
            condicao = df['Descricao_Limpa'].str.contains(rubrica_padrao, regex=False)
            df.loc[condicao, 'Alerta'] = '⚠️ AUDITAR'
            df.loc[condicao, 'Rubrica Detectada'] = rubrica
            
        df = df.drop(columns=['Descricao_Limpa'])
        
        # --- MUDANÇA SOLICITADA: EXCLUSÃO TOTAL DE MOVIMENTAÇÕES NÃO SELECIONADAS ---
        # Filtra o dataframe para manter APENAS as ocorrências das rubricas mapeadas
        df_filtrado_estrito = df[df['Alerta'] == '⚠️ AUDITAR'].copy()
        
        # Remove colunas auxiliares de checagem interna para entregar um relatório limpo
        if not df_filtrado_estrito.empty:
            df_filtrado_estrito = df_filtrado_estrito.drop(columns=['Alerta'])
            df_filtrado_estrito.columns = ['Data', 'Descrição Original do Extrato', 'Documento', 'Valor Real', 'Rubrica Identificada']
        
        return df_filtrado_estrito
        
    return pd.DataFrame()

# ==========================================
# INTERFACE GRÁFICA (VISUAL MASTERY)
# ==========================================

# Cabeçalho de Alta Perfomance
st.markdown("""
<div style='display: flex; justify-content: space-between; align-items: center; padding: 5px 0;'>
    <div style='font-size: 15px; letter-spacing: 3px; color: #C5A566; font-weight: 700;'>EDSON MEDEIROS</div>
    <div style='font-size: 10px; letter-spacing: 1.5px; color: #64748B; font-weight: 600;'>CONSULTORIA & INTELIGÊNCIA DIGITAL</div>
</div>
<div class='master-divider'></div>
""", unsafe_allow_html=True)

# Título Principal com efeito de carregamento fluido
st.markdown("""
<div style='text-align: center; padding: 15px 0 35px 0;'>
    <h1>Sistemas Avançados de Auditoria Cambial</h1>
    <p style='color: #94A3B8; font-size: 16px; max-width: 650px; margin: 15px auto 0 auto; font-weight: 300; line-height: 1.6;'>
        Ambiente algorítmico focado na extração e isolamento de débitos comerciais indevidos com reconstrução cronológica reversa.
    </p>
</div>
""", unsafe_allow_html=True)

# Grid Layout do Painel de Controle
col1, col2 = st.columns([1.7, 1.3])

with col1:
    st.markdown("<div class='master-card'><h3>1. Input de Dados do Extrato</h3>", unsafe_allow_html=True)
    arquivo_enviado = st.file_uploader("Submeta o arquivo digitalizado original para inspeção (PDF, XLSX ou CSV)", type=["pdf", "csv", "xlsx"])
    st.markdown("<p style='text-align: center; color: #475569; margin: 8px 0; font-size: 12px; font-weight: 600;'>OU EXECUTE EM MODO TESTE</p>", unsafe_allow_html=True)
    simular_dados = st.button("Simular Amostra de Auditoria (Padrão Anexo 1)")
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<div class='master-card auditor-card-active'><h3>2. Filtro Seletivo de Alvos</h3>", unsafe_allow_html=True)
    
    rubricas_selecionadas = st.multiselect(
        label="Selecione os Tipos de Descontos",
        options=RUBRICAS_ALERTA,
        default=RUBRICAS_ALERTA,
        help="Apenas as rubricas marcadas aqui entrarão no relatório final. O restante das movimentações comuns do banco será totalmente omitido."
    )
    st.markdown("</div>", unsafe_allow_html=True)

# Lógica de Captura e Processamento Centralizado
df_base = None

if arquivo_enviado is not None:
    bytes_do_arquivo = arquivo_enviado.read()
    nome_arquivo = arquivo_enviado.name.lower()
    try:
        if nome_arquivo.endswith('.pdf'):
            with st.spinner("Descriptografando e mapeando vetores textuais do PDF..."):
                df_base = converter_pdf_para_dataframe(bytes_do_arquivo)
        elif nome_arquivo.endswith('.csv'):
            df_base = pd.read_csv(io.BytesIO(bytes_do_arquivo))
        else:
            df_base = pd.read_excel(io.BytesIO(bytes_do_arquivo))
    except Exception as e:
        st.error(f"Falha crítica na aquisição do arquivo: {e}")

elif simular_dados:
    # Réplica fiel ao cenário real apresentado no documento "ANEXO 1"
    dados_simulados = {
        'Data': ['07/02/2017', '', '', '08/02/2017', '09/02/2017'],
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

# Exibição do Painel de Resultados Filtrados
if df_base is not None:
    st.markdown("<div class='master-divider'></div>", unsafe_allow_html=True)
    
    # Executa a varredura com reconstrução temporal e filtragem restrita
    relatorio_final = analisar_e_filtrar_estrito(df_base, rubricas_selecionadas)
    
    if relatorio_final.empty:
        st.info("Nenhuma das rubricas selecionadas foi encontrada no arquivo processado. O relatório de inconformidades está limpo.")
    else:
        st.markdown("<h3 style='text-align: center; margin-bottom: 25px;'>📋 RELATÓRIO EXCLUSIVO DE INCIDÊNCIAS LOCALIZADAS</h3>", unsafe_allow_html=True)
        
        # Bloco de KPI Customizado com HTML Avançado
        st.markdown(f"""
        <div style='display: flex; justify-content: center; margin-bottom: 25px;'>
            <div class='master-card' style='text-align: center; min-width: 320px; border: 1px solid rgba(229, 193, 88, 0.3);'>
                <span style='color: #94A3B8; font-size: 13px; text-transform: uppercase; letter-spacing: 1px;'>Rubricas Identificadas para Auditoria</span>
                <h2 style='margin: 8px 0 0 0; font-size: 38px; color: #E5C158; font-weight: 700;'>{len(relatorio_final)}</h2>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Exibição da tabela final de auditoria limpa (somente com os alvos de interesse)
        st.dataframe(relatorio_final, use_container_width=True)

# Rodapé Institucional Autoral
st.markdown("""
<div class='master-divider'></div>
<div style='text-align: center; padding: 10px 0;'>
    <p style='color: #475569; font-size: 11px; letter-spacing: 1.5px; font-weight: 500;'>
        PROPRIEDADE INTELECTUAL REGISTRADA © 2026 EDSON MEDEIROS. ENGENHARIA DE COMPLIANCE AVANÇADA.
    </p>
</div>
""", unsafe_allow_html=True)
