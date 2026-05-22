import streamlit as st
import pdfplumber
import pandas as pd
import re
from datetime import datetime
import io
try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from openpyxl.utils import get_column_letter
except ImportError:
    st.error("Erro: A biblioteca 'openpyxl' não está instalada. Certifique-se de incluir 'openpyxl' no seu arquivo requirements.txt.")

# --- CONFIGURAÇÃO PREMIUM EDSON MEDEIROS ---
st.set_page_config(
    page_title="Edson Medeiros | Consultorias e Compliance",
    layout="wide",
    page_icon="🏛️",
    initial_sidebar_state="expanded"
)

# --- PALETA DE CORES PREMIUM (Quiet Luxury) ---
COLORS = {
    "navy_deep": "#101418",
    "dourado_matte": "#C5A566",
    "off_white": "#F5F3F0",
    "cinza_quente": "#8B8680",
    "cinza_claro": "#D4CFCA",
    "card_bg": "#1A1E24",
    "border": "#2C3139",
}

# --- CSS PREMIUM UNIFICADO ---
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Inter:wght@300;400;500;600&display=swap');
    
    /* Reset e Tema Escuro Premium */
    .stApp {{
        background-color: {COLORS['navy_deep']};
        color: {COLORS['off_white']};
    }}
    
    /* Tipografia Premium */
    h1, h2, h3, h4, h5, h6 {{
        font-family: 'Playfair Display', serif !important;
        color: {COLORS['off_white']} !important;
        letter-spacing: -0.02em;
    }}
    
    body, .stMarkdown, .stText {{
        font-family: 'Inter', sans-serif !important;
        color: {COLORS['off_white']} !important;
    }}
    
    /* Header Premium */
    .header-premium {{
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 1.5rem 2rem;
        background: linear-gradient(135deg, {COLORS['navy_deep']} 0%, {COLORS['card_bg']} 100%);
        border-bottom: 1px solid {COLORS['border']};
        margin-bottom: 2rem;
    }}
    
    .logo-box {{
        width: 50px;
        height: 50px;
        background: linear-gradient(135deg, {COLORS['dourado_matte']} 0%, {COLORS['cinza_quente']} 100%);
        border-radius: 4px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        color: {COLORS['navy_deep']};
        font-size: 1.2rem;
        font-family: 'Playfair Display', serif;
    }}
    
    .header-text h1 {{
        margin: 0 !important;
        font-size: 1.5rem !important;
        color: {COLORS['off_white']} !important;
    }}
    
    .header-text p {{
        margin: 0 !important;
        font-size: 0.75rem !important;
        letter-spacing: 0.15em;
        color: {COLORS['cinza_claro']} !important;
    }}
    
    /* Botões Premium */
    .btn-premium {{
        background-color: transparent !important;
        color: {COLORS['dourado_matte']} !important;
        border: 1.5px solid {COLORS['dourado_matte']} !important;
        padding: 0.75rem 1.5rem !important;
        border-radius: 2px !important;
        font-weight: 500 !important;
        letter-spacing: 0.05em !important;
        text-transform: uppercase !important;
        font-size: 0.85rem !important;
        transition: all 0.3s ease-out !important;
        cursor: pointer !important;
    }}
    
    .btn-premium:hover {{
        background-color: {COLORS['dourado_matte']} !important;
        color: {COLORS['navy_deep']} !important;
        box-shadow: 0 4px 12px rgba(197, 165, 102, 0.2) !important;
    }}
    
    /* Cards Premium */
    .card-premium {{
        background-color: {COLORS['card_bg']};
        border: 1px solid {COLORS['border']};
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
        transition: all 0.3s ease;
    }}
    
    .card-premium:hover {{
        border-color: {COLORS['dourado_matte']};
        box-shadow: 0 4px 12px rgba(197, 165, 102, 0.1);
    }}
    
    /* Divider Premium */
    .divider-premium {{
        height: 1px;
        background: linear-gradient(90deg, transparent, {COLORS['dourado_matte']}, transparent);
        margin: 2rem 0;
        opacity: 0.3;
    }}
    
    /* Sidebar Premium */
    .stSidebar {{
        background-color: {COLORS['navy_deep']};
        border-right: 1px solid {COLORS['border']};
    }}
    
    .stSidebar [data-testid="stSidebarNav"] {{
        background-color: transparent;
    }}
    
    /* Inputs e Selects */
    .stMultiSelect, .stSelectbox, .stTextInput, .stNumberInput {{
        background-color: {COLORS['card_bg']} !important;
        color: {COLORS['off_white']} !important;
        border-color: {COLORS['border']} !important;
    }}
    
    /* Tabs Premium */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0;
        border-bottom: 1px solid {COLORS['border']};
    }}
    
    .stTabs [data-baseweb="tab"] {{
        color: {COLORS['cinza_claro']} !important;
        border-bottom: 2px solid transparent !important;
    }}
    
    .stTabs [aria-selected="true"] {{
        color: {COLORS['dourado_matte']} !important;
        border-bottom-color: {COLORS['dourado_matte']} !important;
    }}
    
    /* Métricas Premium */
    .metric-card {{
        background-color: {COLORS['card_bg']};
        border: 1px solid {COLORS['border']};
        border-radius: 8px;
        padding: 1.5rem;
        text-align: center;
    }}
    
    .metric-label {{
        color: {COLORS['cinza_claro']};
        font-size: 0.85rem;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }}
    
    .metric-value {{
        color: {COLORS['dourado_matte']};
        font-size: 2rem;
        font-weight: 700;
        font-family: 'Playfair Display', serif;
    }}
    
    /* Footer Premium */
    .footer-premium {{
        border-top: 1px solid {COLORS['border']};
        padding: 2rem;
        margin-top: 3rem;
        text-align: center;
        color: {COLORS['cinza_claro']};
        font-size: 0.85rem;
    }}
    
    .footer-signature {{
        color: {COLORS['dourado_matte']};
        font-style: italic;
        font-family: 'Playfair Display', serif;
        margin-top: 1rem;
    }}
    
    /* Animações Suaves */
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    .fade-in {{
        animation: fadeIn 0.5s ease-out;
    }}
</style>
""", unsafe_allow_html=True)

# --- HEADER PREMIUM ---
st.markdown(f"""
<div class="header-premium">
    <div class="logo-box">EM</div>
    <div class="header-text">
        <h1>Edson Medeiros</h1>
        <p>CONSULTORIAS & COMPLIANCE</p>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="divider-premium"></div>', unsafe_allow_html=True)

# --- SIDEBAR CONFIGURAÇÃO ---
st.sidebar.markdown(f"""
<div style="text-align: center; padding: 1rem 0; border-bottom: 1px solid {COLORS['border']}; margin-bottom: 1.5rem;">
    <h3 style="color: {COLORS['dourado_matte']}; margin: 0;">Configuração de Análise</h3>
</div>
""", unsafe_allow_html=True)

# Lista de rubricas para busca
rubricas_disponiveis = [
    "CESTA",
    "PACOTE",
    "MORA DE OPERAÇÃO",
    "MORA CREDITO PESSOAL",
    "MORA OPERACAO DE CREDITO",
    "BX",
    "PARCELA CREDITO PESSOAL",
    "GASTOS CARTAO DE CREDITO",
    "SEGURO",
    "ADIANT",
    "APLIC",
    "ENCARGOS",
    "ANUIDADE",
    "OPERACOES VENCIDAS",
    "DIV. EM ATRASO"
]

# Botões de seleção em massa
col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("✓ Marcar Todas", key="marcar_todas", use_container_width=True):
        st.session_state.rubricas_selecionadas = rubricas_disponiveis.copy()

with col2:
    if st.button("✗ Desmarcar Todas", key="desmarcar_todas", use_container_width=True):
        st.session_state.rubricas_selecionadas = []

# Seleção de rubricas
if "rubricas_selecionadas" not in st.session_state:
    st.session_state.rubricas_selecionadas = []

rubricas_selecionadas = st.sidebar.multiselect(
    "Selecione as Rubricas para Análise:",
    rubricas_disponiveis,
    default=st.session_state.rubricas_selecionadas,
    key="rubrica_selector"
)
st.session_state.rubricas_selecionadas = rubricas_selecionadas

# Upload de PDF
st.sidebar.markdown(f"<div class='divider-premium'></div>", unsafe_allow_html=True)
arquivo_pdf = st.sidebar.file_uploader(
    "📄 Carregue o Extrato Bancário (PDF)",
    type="pdf",
    help="Selecione um arquivo PDF com os extratos bancários para análise"
)

# --- MAIN CONTENT ---
if arquivo_pdf is None:
    st.markdown(f"""
    <div class="card-premium" style="text-align: center; padding: 3rem;">
        <h2 style="color: {COLORS['dourado_matte']}; margin-bottom: 1rem;">Bem-vindo à Análise de Extratos</h2>
        <p style="color: {COLORS['cinza_claro']}; font-size: 1.1rem; line-height: 1.8;">
            Sistema especializado em auditoria técnica e identificação de débitos indevidos.
        </p>
        <p style="color: {COLORS['cinza_claro']}; margin-top: 1.5rem;">
            📋 Carregue um arquivo PDF na barra lateral para começar a análise.
        </p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class="card-premium">
        <h3 style="color: {COLORS['dourado_matte']}; margin-top: 0;">📊 Análise em Progresso</h3>
        <p style="color: {COLORS['cinza_claro']};">Processando arquivo: <strong>{arquivo_pdf.name}</strong></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Processamento do PDF
    try:
        with pdfplumber.open(arquivo_pdf) as pdf:
            texto_completo = ""
            for page in pdf.pages:
                texto_completo += page.extract_text() or ""
        
        # Extração de dados com lógica de Data Inferior
        linhas = texto_completo.split('\n')
        dados_extratos = []
        cesto_acumulador = []
        data_atual = None
        
        for i, linha in enumerate(linhas):
            linha_limpa = linha.strip()
            
            # Detecta data no formato DD/MM/YYYY ou DD/MM/YY no início da linha
            match_data = re.match(r'^(\d{2}/\d{2}/\d{2,4})\s+', linha_limpa)
            
            if match_data:
                data_str = match_data.group(1)
                
                # Converte ano de 2 dígitos para 4 dígitos
                partes_data = data_str.split('/')
                if len(partes_data[2]) == 2:
                    ano = int(partes_data[2])
                    ano = 2000 + ano if ano < 50 else 1900 + ano
                    data_str = f"{partes_data[0]}/{partes_data[1]}/{ano}"
                
                # Selá o cesto com a data encontrada
                if cesto_acumulador:
                    for item in cesto_acumulador:
                        dados_extratos.append({
                            'data': data_str,
                            'rubrica': item['rubrica'],
                            'valor': item['valor'],
                            'historico': item['historico']
                        })
                    cesto_acumulador = []
                
                data_atual = data_str
                
                # Extrai valor da mesma linha (formato: XXX,XX no final)
                match_valor = re.search(r'(\d+[.,]\d{2})\s*$', linha_limpa)
                if match_valor:
                    valor = match_valor.group(1)
                    # Detecta rubrica na mesma linha
                    for rubrica in rubricas_selecionadas:
                        if rubrica.upper() in linha_limpa.upper():
                            cesto_acumulador.append({
                                'rubrica': rubrica,
                                'valor': valor,
                                'historico': linha_limpa[:100]
                            })
            else:
                # Se não é uma linha de data, verifica se é uma rubrica
                for rubrica in rubricas_selecionadas:
                    if rubrica.upper() in linha_limpa.upper():
                        # Busca valor na próxima linha
                        if i + 1 < len(linhas):
                            proxima_linha = linhas[i + 1].strip()
                            # Tenta extrair data e valor da próxima linha
                            match_prox_data = re.match(r'^(\d{2}/\d{2}/\d{2,4})\s+.*?(\d+[.,]\d{2})\s*$', proxima_linha)
                            if match_prox_data:
                                data_prox = match_prox_data.group(1)
                                valor_prox = match_prox_data.group(2)
                                
                                # Converte ano de 2 dígitos
                                partes_data_prox = data_prox.split('/')
                                if len(partes_data_prox[2]) == 2:
                                    ano = int(partes_data_prox[2])
                                    ano = 2000 + ano if ano < 50 else 1900 + ano
                                    data_prox = f"{partes_data_prox[0]}/{partes_data_prox[1]}/{ano}"
                                
                                dados_extratos.append({
                                    'data': data_prox,
                                    'rubrica': rubrica,
                                    'valor': valor_prox,
                                    'historico': linha_limpa[:100]
                                })
        
        # Filtra dados vazios
        dados_extratos = [d for d in dados_extratos if d['valor'] != '0,00']
        
        if dados_extratos:
            df = pd.DataFrame(dados_extratos)
            
            # Ordena por data
            df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y')
            df = df.sort_values('data')
            df['data'] = df['data'].dt.strftime('%d/%m/%Y')
            
            # Exibe métricas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Total de Débitos</div>
                    <div class="metric-value">{len(df)}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Período Analisado</div>
                    <div class="metric-value">{df['data'].min()} a {df['data'].max()}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Rubricas Identificadas</div>
                    <div class="metric-value">{df['rubrica'].nunique()}</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('<div class="divider-premium"></div>', unsafe_allow_html=True)
            
            # Relatório consolidado
            st.markdown(f"<h3 style='color: {COLORS['dourado_matte']};'>📋 Relatório Consolidado</h3>", unsafe_allow_html=True)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Download de relatórios
            st.markdown('<div class="divider-premium"></div>', unsafe_allow_html=True)
            st.markdown(f"<h3 style='color: {COLORS['dourado_matte']};'>📥 Exportar Relatórios</h3>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            # CSV
            with col1:
                csv = df.to_csv(index=False, sep=';', encoding='utf-8-sig')
                st.download_button(
                    label="📊 Baixar Relatório (CSV)",
                    data=csv,
                    file_name=f"relatorio_extratos_{datetime.now().strftime('%d%m%Y')}.csv",
                    mime="text/csv"
                )
            
            # Excel com fórmulas
            with col2:
                output = io.BytesIO()
                wb = Workbook()
                ws = wb.active
                ws.title = "Extratos"
                
                # Cabeçalhos
                headers = ['DATA', 'RUBRICA', 'VALOR', 'HISTÓRICO']
                for col_num, header in enumerate(headers, 1):
                    cell = ws.cell(row=1, column=col_num)
                    cell.value = header
                    cell.font = Font(bold=True, color="FFFFFF", name="Calibri", size=11)
                    cell.fill = PatternFill(start_color="101418", end_color="101418", fill_type="solid")
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                
                # Dados
                for row_num, row_data in enumerate(df.values, 2):
                    for col_num, value in enumerate(row_data, 1):
                        cell = ws.cell(row=row_num, column=col_num)
                        cell.value = value
                        cell.alignment = Alignment(horizontal="left", vertical="center")
                
                wb.save(output)
                output.seek(0)
                
                st.download_button(
                    label="📈 Baixar Tabela (Excel)",
                    data=output.getvalue(),
                    file_name=f"tabela_calculos_{datetime.now().strftime('%d%m%Y')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.warning("⚠️ Nenhum débito foi identificado com as rubricas selecionadas.")
    
    except Exception as e:
        st.error(f"❌ Erro ao processar o arquivo: {str(e)}")

# --- FOOTER PREMIUM ---
st.markdown(f"""
<div class="footer-premium">
    <p>© 2026 Edson Medeiros - Consultorias e Compliance. Todos os direitos reservados.</p>
    <div class="footer-signature">Fundado por Edson Medeiros</div>
</div>
""", unsafe_allow_html=True)
