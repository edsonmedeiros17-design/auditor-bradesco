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
# ESTÉTICA INTERNACIONAL (CSS LUXO SILENCIOSO)
# ==========================================
premium_ui_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
    
    /* Remoção estrita de componentes nativos do Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none !important;}
    
    /* Configurações Globais da Identidade Visual */
    .stApp {
        background-color: #101418 !important;
        color: #E2E8F0 !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    
    /* Tipografia de Alto Padrão */
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
    
    /* Componentes Institucionais Organizados */
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
    
    .hero-subtitle {
        font-size: 18px !important;
        color: #94A3B8 !important;
        line-height: 1.6 !important;
        font-weight: 300 !important;
    }
    
    /* Cards Executivos de Serviços e Diferenciais */
    .premium-card {
        background-color: #14191F;
        border: 1px solid rgba(255, 255, 255, 0.03);
        border-radius: 6px;
        padding: 32px;
        height: 100%;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .premium-card:hover {
        border-color: rgba(197, 165, 102, 0.2);
        transform: translateY(-2px);
    }
    
    /* Customização de Inputs Operacionais */
    .stFileUploader {
        border: 1px dashed rgba(197, 165, 102, 0.2) !important;
        border-radius: 6px !important;
        background-color: #13181E !important;
    }
    
    .stMultiSelect div[data-baseweb="select"] {
        background-color: #13181E !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 6px !important;
    }
    
    /* Botões de Ação Sofisticados */
    div.stButton > button {
        background-color: transparent !important;
        color: #C5A566 !important;
        border: 1px solid #C5A566 !important;
        border-radius: 4px !important;
        padding: 12px 28px !important;
        font-weight: 500 !important;
        font-size: 13px !important;
        letter-spacing: 0.05em !important;
        text-transform: uppercase;
        transition: all 0.3s ease !important;
        width: 100%;
    }
    div.stButton > button:hover {
        background-color: #C5A566 !important;
        color: #101418 !important;
        box-shadow: 0 4px 15px rgba(197, 165, 102, 0.15) !important;
    }
    
    .contact-link-box {
        display: inline-block;
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 16px 24px;
        border-radius: 4px;
        color: #E2E8F0 !important;
        text-decoration: none !important;
        font-weight: 500;
        font-size: 14px;
        margin-right: 15px;
        transition: all 0.2s ease;
    }
    .contact-link-box:hover {
        border-color: #C5A566;
        color: #C5A566 !important;
    }
    
    .corporate-divider {
        height: 1px;
        background-color: rgba(255, 255, 255, 0.05);
        margin: 55px 0;
    }
</style>
"""
st.markdown(premium_ui_css, unsafe_allow_html=True)

# ==========================================
# PARÂMETROS E MOTOR DE AUDITORIA FORENSE
# ==========================================
RUBRICAS_ALERTA = [
    "CESTA", "PACOTE", "MORA DE OPERAÇÃO", "MORA CREDITO PESSOAL",
    "MORA OPERACAO DE CREDITO", "BX", "PARCELA CREDITO PESSOAL",
    "GASTOS CARTAO DE CREDITO", "SEGURO", "ADIANT", "APLIC",
    "ENCARGOS", "ANUIDADE", "OPERACOES VENCIDAS", "DIV. EM ATRASO",
    "ENCARGOS LIMITE DE CRED"
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
                
                # Passo 1: Identificação da Data Inicial (se houver na linha)
                tem_data = re.match(r'^\d{2}/\d{2}/\d{4}', partes[0])
                if tem_data:
                    data = partes[0]
                    resto = partes[1:]
                else:
                    data = pd.NA  # Deixa vazio para capturar a DATA INFERIOR depois
                    resto = partes
                
                # Passo 2: Mapeamento Reverso Inteligente de Valores Contábeis
                valores_candidatos = []
                for idx in range(len(resto) - 1, -1, -1):
                    token = resto[idx]
                    # Identifica padrões numéricos decimais de moeda (ex: 115,62 ou 19,31) e ignora taxas com %
                    if re.search(r'^-?\d+([\.,]\d{2})+$', token) and '%' not in token:
                        valores_candidatos.append(idx)
                
                indices_para_remover = set()
                valor = ""
                
                if len(valores_candidatos) >= 2:
                    # Conforme a estrutura padrão: o último valor à direita é o Saldo, o penúltimo é o Valor do Débito
                    idx_saldo = valores_candidatos[0]
                    idx_valor = valores_candidatos[1]
                    valor = resto[idx_valor]
                    indices_para_remover.add(idx_saldo)
                    indices_para_remover.add(idx_valor)
                elif len(valores_candidatos) == 1:
                    # Se houver apenas uma ocorrência decimal isolada, ela representa o valor movimentado
                    idx_valor = valores_candidatos[0]
                    valor = resto[idx_valor]
                    indices_para_remover.add(idx_valor)
                else:
                    # Fallback de contingência estrutural
                    valor = resto[-1] if len(resto) > 0 else ""
                    if len(resto) > 0:
                        indices_para_remover.add(len(resto) - 1)
                
                # Passo 3: Limpeza e isolamento do Histórico de Rubricas
                resto_sem_valores = [resto[i] for i in range(len(resto)) if i not in indices_para_remover]
                
                # Extração do número do documento corporativo (tokens puramente numéricos longos)
                doc = ""
                descricao_tokens = []
                for token in resto_sem_valores:
                    if token.isdigit() and len(token) >= 4:
                        doc = token
                    else:
                        descricao_tokens.append(token)
                
                descricao = " ".join(descricao_tokens)
                
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
        # Aplicação cirúrgica da Regra de DATA INFERIOR demonstrada no "ANEXA 1"
        df['Data'] = df['Data'].replace(r'^\s*$', pd.NA, regex=True)
        df['Data'] = df['Data'].bfill()  # Preenche de baixo para cima puxando a data limite inferior
        
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
        
        # Formatação final estrita exigida pelo escopo do projeto
        if not df_filtrado_estrito.empty:
            df_filtrado_estrito = df_filtrado_estrito[['Data', 'Rubrica Detectada', 'Valor']]
            df_filtrado_estrito.columns = ['DATA', 'NOME DA RUBRICA', 'VALOR DESCONTADO']
        
        return df_filtrado_estrito
        
    return pd.DataFrame()

# ==========================================
# CONSTRUTOR DA INTERFACE INSTITUCIONAL PRESTÍGIO
# ==========================================

# 1. Header Minimalista
st.markdown("""
<div class='nav-container'>
    <div style='font-size: 16px; letter-spacing: 0.15em; font-weight: 700; color: #FFFFFF;'>
        EDSON MEDEIROS <span class='brand-gold' style='font-weight: 300;'>| CONSULTORIA & COMPLIANCE</span>
    </div>
    <div style='font-size: 13px; color: #94A3B8; font-weight: 400;'>
        <span style='margin-left: 20px; color: #C5A566;'>• Corporate</span>
        <span style='margin-left: 20px;'>• Soluções</span>
        <span style='margin-left: 20px;'>• Auditoria</span>
    </div>
</div>
""", unsafe_allow_html=True)

# 2. Hero Section Impactante
st.markdown("""
<div class='hero-container'>
    <h1 class='hero-title'>Excelência Estratégica e Rigor Contábil de Classe Mundial.</h1>
    <p class='hero-subtitle'>
        Salvaguardamos o patrimônio de corporações de alta performance através de blindagem financeira, auditoria cambial avançada e inteligência regulatória. Luxo silencioso traduzido em precisão absoluta.
    </p>
</div>
<div class='corporate-divider' style='margin-top: 10px;'></div>
""", unsafe_allow_html=True)

# 3. Seção Sobre a Empresa
st.markdown("<div class='section-title'>Sobre a Empresa</div>", unsafe_allow_html=True)
st.markdown("""
<div style='max-width: 900px; font-size: 16px; color: #94A3B8; line-height: 1.8; font-weight: 300; margin-bottom: 40px;'>
    A <b style='color: #FFFFFF;'>EDSON MEDEIROS - Consultoria & Compliance</b> consolida-se como uma boutique estratégica de inteligência digital e integridade corporativa. Atendemos com total discrição e exclusividade, desenvolvendo metodologias sob medida baseadas em auditoria forense de alto padrão para identificar assimetrias, mitigar riscos operacionais e reestruturar passivos bancários com autoridade inabalável.
</div>
""", unsafe_allow_html=True)

# 4. Seção de Serviços (Cards Organizados)
st.markdown("<div class='section-title'>Nossos Serviços</div>", unsafe_allow_html=True)
s_col1, s_col2, s_col3 = st.columns(3, gap="medium")

with s_col1:
    st.markdown("""
    <div class='premium-card'>
        <h4 style='color: #FFFFFF; font-size: 18px; margin-bottom: 12px; font-weight: 600;'>Corporate Compliance</h4>
        <p style='color: #94A3B8; font-size: 14px; line-height: 1.6; font-weight: 300;'>
            Alinhamento estrito às matrizes regulatórias e governança avançada para mitigar contingências comerciais perante órgãos fiscalizadores.
        </p>
    </div>
    """, unsafe_allow_html=True)

with s_col2:
    st.markdown("""
    <div class='premium-card'>
        <h4 style='color: #C5A566; font-size: 18px; margin-bottom: 12px; font-weight: 600;'>Auditoria Digital de Ativos</h4>
        <p style='color: #94A3B8; font-size: 14px; line-height: 1.6; font-weight: 300;'>
            Varredura algorítmica de extratos com rastreamento reverso para captura e eliminação cirúrgica de débitos comerciais indevidos.
        </p>
    </div>
    """, unsafe_allow_html=True)

with s_col3:
    st.markdown("""
    <div class='premium-card'>
        <h4 style='color: #FFFFFF; font-size: 18px; margin-bottom: 12px; font-weight: 600;'>Consultoria Estratégica</h4>
        <p style='color: #94A3B8; font-size: 14px; line-height: 1.6; font-weight: 300;'>
            Engenharia de proteção de caixa estruturada para empresas maduras que demandam exclusividade e tomada de decisão de alto nível.
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div class='corporate-divider'></div>", unsafe_allow_html=True)

# ==========================================
# 5. MÓDULO INTEGRADO DA FERRAMENTA DE AUDITORIA
# ==========================================
st.markdown("<div class='section-title'>Console de Inteligência Cambial</div>", unsafe_allow_html=True)

tool_col1, tool_col2 = st.columns([1.6, 1.4], gap="large")

with tool_col1:
    st.markdown("<div style='font-size: 14px; color: #E2E8F0; margin-bottom: 10px; font-weight: 500;'>Entrada de Documentos Digitais</div>", unsafe_allow_html=True)
    arquivo_enviado = st.file_uploader("Arraste ou selecione o arquivo original (PDF, XLSX, CSV)", type=["pdf", "csv", "xlsx"], label_visibility="collapsed")
    st.markdown("<div style='margin: 15px 0; text-align: center; color: #475569; font-size: 11px; font-weight: 600; letter-spacing: 0.05em;'>OU DEFLAGRE O PROCESSO EM AMBIENTE SEGURO DE SIMULAÇÃO</div>", unsafe_allow_html=True)
    simular_dados = st.button("Simular Análise Baseada no Modelo de Extrato Anexo 1")

with tool_col2:
    st.markdown("<div style='font-size: 14px; color: #E2E8F0; margin-bottom: 10px; font-weight: 500;'>Parametrização Estrita de Busca</div>", unsafe_allow_html=True)
    rubricas_selecionadas = st.multiselect(
        label="Parâmetros ativos de auditoria",
        options=RUBRICAS_ALERTA,
        default=RUBRICAS_ALERTA,
        label_visibility="collapsed"
    )
    st.markdown("""
        <div style='margin-top: 15px; font-size: 12px; color: #64748B; line-height: 1.5; font-weight: 300;'>
            * O sistema isolará apenas as ocorrências dos alvos marcados acima, efetuando o recálculo retroativo baseado no fechamento por <b>Data Inferior</b> do lote de movimentações.
        </div>
    """, unsafe_allow_html=True)

# Processamento Lógico Ativo
df_base = None

if arquivo_enviado is not None:
    bytes_do_arquivo = arquivo_enviado.read()
    nome_arquivo = arquivo_enviado.name.lower()
    try:
        if nome_arquivo.endswith('.pdf'):
            with st.spinner("Decodificando camadas contábeis do PDF..."):
                df_base = converter_pdf_para_dataframe(bytes_do_arquivo)
        elif nome_arquivo.endswith('.csv'):
            df_base = pd.read_csv(io.BytesIO(bytes_do_arquivo))
        else:
            df_base = pd.read_excel(io.BytesIO(bytes_do_arquivo))
    except Exception as e:
        st.error(f"Erro na aquisição do documento: {e}")

elif simular_dados:
    # Cenário reconstruído identicamente ao exemplo real da imagem "ANEXA 1"
    dados_simulados = {
        'Data': ['07/02/2017', None, None, '08/02/2017'],
        'Descricao': [
            'SAQUE DINHEIRO ATM',
            'MORA CREDITO PESSOAL', 
            'ENCARGOS LIMITE DE CRED ENCARGO - 14,31%', 
            'SAQUE DIN CORBAN CARTAO ESPECIE'
        ],
        'Docto': ['6017411', '5070038', '8118726', '3714083'],
        'Valor': ['500,00', '115,62', '19,31', '130,00']
    }
    df_base = pd.DataFrame(dados_simulados)

# Saída do Relatório da Auditoria
if df_base is not None:
    relatorio_final = analisar_e_filtrar_estrito(df_base, rubricas_selecionadas)
    st.markdown("<br>", unsafe_allow_html=True)
    
    if relatorio_final.empty:
        st.info("Nenhuma inconsistência contendo as rubricas selecionadas foi detectada neste lote de documentos.")
    else:
        st.markdown("<div style='font-size: 14px; color: #C5A566; font-weight: 600; letter-spacing: 0.05em; margin-bottom: 15px;'>RESULTADO DA EXTRAÇÃO DE PASSIVOS REGULATÓRIOS</div>", unsafe_allow_html=True)
        st.dataframe(
            relatorio_final, 
            use_container_width=True,
            hide_index=True
        )

st.markdown("<div class='corporate-divider'></div>", unsafe_allow_html=True)

# 6. Seção de Diferenciais
st.markdown("<div class='section-title'>Nossos Diferenciais</div>", unsafe_allow_html=True)
d_col1, d_col2, d_col3, d_col4 = st.columns(4, gap="small")

with d_col1:
    st.markdown("<div class='premium-card'><h5 style='color:#FFF;font-size:15px;margin-bottom:8px;'>Excelência</h5><p style='color:#94A3B8;font-size:13px;font-weight:300;line-height:1.5;'>Rigor analítico internacional em cada linha de dados avaliada.</p></div>", unsafe_allow_html=True)
with d_col2:
    st.markdown("<div class='premium-card'><h5 style='color:#C5A566;font-size:15px;margin-bottom:8px;'>Estratégia</h5><p style='color:#94A3B8;font-size:13px;font-weight:300;line-height:1.5;'>Abordagem preventiva focada na otimização de ativos reais.</p></div>", unsafe_allow_html=True)
with d_col3:
    st.markdown("<div class='premium-card'><h5 style='color:#FFF;font-size:15px;margin-bottom:8px;'>Segurança</h5><p style='color:#94A3B8;font-size:13px;font-weight:300;line-height:1.5;'>Ambiente operacional seguro com total sigilo de dados contábeis.</p></div>", unsafe_allow_html=True)
with d_col4:
    st.markdown("<div class='premium-card'><h5 style='color:#FFF;font-size:15px;margin-bottom:8px;'>Confiança</h5><p style='color:#94A3B8;font-size:13px;font-weight:300;line-height:1.5;'>Parcerias consolidadas construídas sob o pilar do luxo silencioso.</p></div>", unsafe_allow_html=True)

st.markdown("<div class='corporate-divider'></div>", unsafe_allow_html=True)

# 7. Área de Contato Elegante
st.markdown("<div class='section-title'>Canais de Atendimento Restritos</div>", unsafe_allow_html=True)
st.markdown("""
<div style='margin-bottom: 25px; font-size: 15px; color: #94A3B8; font-weight: 300;'>
    Inicie uma interlocução corporativa com nosso comitê de compliance por meio dos canais de alta prioridade abaixo:
</div>
<div>
    <a href='https://wa.me/seu_numero' target='_blank' class='contact-link-box'>Comunicação via WhatsApp</a>
    <a href='mailto:contato@edsonmedeiros.com' class='contact-link-box'>Abertura de Chamado por E-mail</a>
</div>
""", unsafe_allow_html=True)

# 8. Rodapé Discreto e Refinado
st.markdown("""
<div class='corporate-divider' style='margin-top: 60px;'></div>
<div style='display: flex; justify-content: space-between; align-items: center; padding: 10px 0; color: #475569; font-size: 11px; font-weight: 500; letter-spacing: 0.02em;'>
    <div>© 2026 EDSON MEDEIROS - CONSULTORIA & COMPLIANCE. ALL RIGHTS RESERVED.</div>
    <div>SISTEMA PROTEGIDO POR PROTOCOLOS DE ALTA CRIPTOGRAFIA</div>
</div>
""", unsafe_allow_html=True)
