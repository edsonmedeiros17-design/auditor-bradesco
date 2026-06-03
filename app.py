import streamlit as st
import pdfplumber
import pandas as pd
import re
from datetime import datetime
import io
import numpy as np
from typing import List, Dict, Tuple

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from openpyxl.utils import get_column_letter
except ImportError:
    st.error("Erro: A biblioteca 'openpyxl' não está instalada.")

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Edson Medeiros | Consultoria de Ativos", layout="wide", page_icon="⚖️")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;600&display=swap');
    .stApp { background-color: #0E1117; color: #FFFFFF; font-family: 'Inter', sans-serif; }
    .main-title { font-family: 'Playfair Display', serif; font-size: 3rem; color: #BFAF83; text-align: center; margin-bottom: 0; }
    .sub-title { text-align: center; color: #64748B; letter-spacing: 2px; text-transform: uppercase; font-size: 0.9rem; margin-bottom: 40px; }
    .metric-card { background: rgba(255,255,255,0.05); border: 1px solid #BFAF83; border-radius: 10px; padding: 20px; text-align: center; }
    .config-box { background: rgba(191, 175, 131, 0.1); border: 1px solid #BFAF83; border-radius: 8px; padding: 10px; margin: 10px 0; }
    .debug-box { background: rgba(50, 150, 200, 0.1); border: 1px solid #3296C8; border-radius: 8px; padding: 10px; margin: 10px 0; font-size: 12px; max-height: 400px; overflow-y: auto; }
</style>
""", unsafe_allow_html=True)

# --- 2. RÚBRICAS EXATAS ---
RUBRICAS_MESTRE = {
    "CESTA": r"CESTA",
    "PACOTE": r"PACOTE",
    "MORA DE OPERAÇÃO": r"MORA DE OPERAÇÃO|MORA OPERACAO",
    "MORA CREDITO PESSOAL": r"MORA CREDITO PESSOAL|MORA CRED PESS",
    "MORA OPERACAO DE CREDITO": r"MORA OPERACAO DE CREDITO|MORA OPER CRED",
    "BX": r"\bBX\b",
    "PARCELA CREDITO PESSOAL": r"PARCELA CREDITO PESSOAL|PARC CRED PESS",
    "GASTOS CARTAO DE CREDITO": r"GASTOS CARTAO DE CREDITO|CARTAO DE CREDITO|GASTOS CARTAO",
    "SEGURO": r"SEGURO|SEGURADORA|SEG\b",
    "ADIANT": r"ADIANT|ADIANTAMENTO DEPOSITANTE",
    "APLIC": r"APLICACAO|APLIC\b",
    "ENCARGOS": r"ENCARGOS|ENCARGO|ENC LIMITE|LIMITE DE CRED",
    "ANUIDADE": r"ANUIDADE|CARTAO CREDITO ANUIDADE",
    "OPERACOES VENCIDAS": r"OPERACOES VENCIDAS|OPERAÇÕES VENCIDAS",
    "DIV. EM ATRASO": r"DIV\. EM ATRASO|DIVIDA EM ATRASO"
}

TERMOS_EXCLUSAO = r"TRANSF|SALDO|SDO|TRANSFERENCIA|SALARIO"

# --- 3. INICIALIZAR SESSION STATE ---
if 'rubricas_selecionadas' not in st.session_state:
    st.session_state.rubricas_selecionadas = {r: True for r in RUBRICAS_MESTRE.keys()}
if 'debug_mode' not in st.session_state:
    st.session_state.debug_mode = False

# --- 4. FUNÇÕES AUXILIARES AVANÇADAS ---

def extrair_todos_valores(texto: str) -> List[str]:
    """
    Extrai TODOS os valores monetários da linha com extrema precisão.
    Captura: 1,23 | 10,00 | 1.234,56 | 1.234.567,89
    """
    valores = []
    # Padrão robusto: captura valores brasileiros com até 3 casas decimais
    # Formato: X,XX ou X.XXX,XX ou X.XXX.XXX,XX
    pattern = r'(\d{1,3}(?:\.\d{3})*,\d{2})'
    matches = re.finditer(pattern, texto)
    for match in matches:
        valor = match.group(1)
        # Valida que não está seguido de %
        pos_final = match.end()
        if pos_final < len(texto) and '%' not in texto[pos_final:pos_final+2]:
            valores.append(valor)
    return valores


def converter_valor_para_float(valor_str: str) -> float:
    """
    Conversão INFALÍVEL de valores brasileiros para float.
    """
    if not valor_str or valor_str == "PENDENTE":
        return 0.0
    
    try:
        valor_str = str(valor_str).strip()
        if '%' in valor_str or not valor_str:
            return 0.0
        
        # Remove pontos (separador de milhar) e substitui vírgula por ponto
        valor_str = valor_str.replace('.', '')
        valor_str = valor_str.replace(',', '.')
        
        valor_float = float(valor_str)
        return valor_float if valor_float > 0 else 0.0
    except:
        return 0.0


def extrair_todas_datas(texto: str) -> List[str]:
    """
    Extrai TODAS as datas do texto com máxima flexibilidade.
    Captura: dd/mm/yyyy | dd/mm/yy
    """
    datas = []
    pattern = r'(\d{2}/\d{2}/\d{2,4})'
    matches = re.finditer(pattern, texto)
    for match in matches:
        datas.append(match.group(1))
    return datas


def formatar_data(data_str: str) -> str:
    """
    Formata data para padrão dd/mm/yyyy.
    """
    if not data_str or data_str == "PENDENTE":
        return "PENDENTE"
    
    try:
        partes = data_str.split('/')
        if len(partes) != 3:
            return "PENDENTE"
        
        dia, mes, ano = partes
        
        # Valida dia e mês
        if not (1 <= int(dia) <= 31 and 1 <= int(mes) <= 12):
            return "PENDENTE"
        
        # Adiciona século se necessário
        if len(ano) == 2:
            ano = "20" + ano
        
        return f"{dia}/{mes}/{ano}"
    except:
        return "PENDENTE"


def buscar_rubrica(linha: str, rubricas_alvo: List[str]) -> Tuple[str, bool]:
    """
    Busca rubrica na linha com máxima precisão.
    Retorna: (nome_rubrica, encontrada)
    """
    linha_up = linha.upper().strip()
    
    if "%" in linha_up:
        return None, False
    
    for nome in rubricas_alvo:
        if re.search(RUBRICAS_MESTRE[nome], linha_up):
            return nome, True
    
    return None, False


def rastrear_valor_contexto(linhas: List[str], idx_atual: int, max_distancia: int = 5) -> str:
    """
    ALGORITMO AVANÇADO: Rastreia valor mesmo se não estiver na mesma linha.
    Procura em linhas vizinhas (para frente e para trás).
    """
    valores_encontrados = []
    
    # Procura para trás (linhas anteriores)
    for i in range(max(0, idx_atual - max_distancia), idx_atual):
        vals = extrair_todos_valores(linhas[i])
        valores_encontrados.extend(vals)
    
    # Procura para frente (próximas linhas)
    for i in range(idx_atual + 1, min(len(linhas), idx_atual + max_distancia + 1)):
        vals = extrair_todos_valores(linhas[i])
        valores_encontrados.extend(vals)
    
    # Retorna o primeiro valor encontrado (mais próximo)
    if valores_encontrados:
        return valores_encontrados[0]
    
    return "PENDENTE"


# --- 5. MOTOR ULTRA-PRECISO DATA SUPERIOR ---

def realizar_auditoria_data_superior(arquivo, rubricas_alvo: List[str]) -> List[Dict]:
    """
    MOTOR ULTRA-PRECISO - DATA SUPERIOR (ANEXO 1)
    Captura TUDO com múltiplas estratégias de extração.
    """
    resultados = []
    
    try:
        with pdfplumber.open(arquivo) as pdf:
            todas_linhas = []
            
            # FASE 1: Extrair todas as linhas de todas as páginas
            for page_num, page in enumerate(pdf.pages):
                texto = page.extract_text(x_tolerance=2, y_tolerance=2)
                if not texto:
                    continue
                
                linhas = texto.split('\n')
                todas_linhas.extend([(line, page_num) for line in linhas])
            
            # FASE 2: Processar com contexto de múltiplas linhas
            ultima_data = None
            buffer_rubricas = []  # Buffer para acumular rubricas
            
            for idx, (linha, page_num) in enumerate(todas_linhas):
                linha_up = linha.upper().strip()
                
                if not linha_up:
                    continue
                
                # Busca data na linha
                datas = extrair_todas_datas(linha_up)
                if datas:
                    ultima_data = formatar_data(datas[0])
                    
                    # Se temos rubricas bufferizadas, processa-as com essa data
                    for rubrica, historico in buffer_rubricas:
                        # Tenta encontrar valor na linha atual
                        valores = extrair_todos_valores(linha_up)
                        valor = valores[0] if valores else "PENDENTE"
                        
                        if valor == "PENDENTE":
                            # Rastreia em contexto
                            valor = rastrear_valor_contexto([l[0] for l in todas_linhas], idx, max_distancia=3)
                        
                        resultados.append({
                            "CATEGORIA": rubrica,
                            "VALOR": valor,
                            "HISTÓRICO": historico[:80],
                            "DATA": ultima_data
                        })
                    
                    buffer_rubricas = []
                    continue
                
                # Verifica exclusão
                if re.search(TERMOS_EXCLUSAO, linha_up):
                    buffer_rubricas = []
                    continue
                
                # Busca rubrica
                rubrica, encontrada = buscar_rubrica(linha, rubricas_alvo)
                
                if encontrada:
                    valores = extrair_todos_valores(linha_up)
                    valor = valores[0] if valores else "PENDENTE"
                    
                    if valor == "PENDENTE":
                        valor = rastrear_valor_contexto([l[0] for l in todas_linhas], idx, max_distancia=3)
                    
                    resultados.append({
                        "CATEGORIA": rubrica,
                        "VALOR": valor,
                        "HISTÓRICO": linha_up[:80],
                        "DATA": ultima_data if ultima_data else "PENDENTE"
                    })
                    
                    buffer_rubricas = []
    
    except Exception as e:
        st.error(f"❌ Erro ao processar PDF (DATA_SUPERIOR): {str(e)}")
    
    return resultados


# --- 6. MOTOR ULTRA-PRECISO DATA INFERIOR ---

def realizar_auditoria_data_inferior(arquivo, rubricas_alvo: List[str]) -> List[Dict]:
    """
    MOTOR ULTRA-PRECISO - DATA INFERIOR (ANEXO 2)
    Captura com lógica inteligente de contexto e rastreamento.
    """
    resultados = []
    
    try:
        with pdfplumber.open(arquivo) as pdf:
            todas_linhas = []
            
            # FASE 1: Extrair todas as linhas
            for page_num, page in enumerate(pdf.pages):
                texto = page.extract_text(x_tolerance=2, y_tolerance=2)
                if not texto:
                    continue
                
                linhas = texto.split('\n')
                todas_linhas.extend([(line, page_num) for line in linhas])
            
            # FASE 2: Processar com lógica de data inferior
            bloco_acumulador = []
            ultima_data_inferida = None
            
            for idx, (linha, page_num) in enumerate(todas_linhas):
                linha_up = linha.upper().strip()
                
                if not linha_up:
                    continue
                
                # Procura por data (data inferior)
                datas = extrair_todas_datas(linha_up)
                
                if datas:
                    data_encontrada = formatar_data(datas[0])
                    ultima_data_inferida = data_encontrada
                    
                    # Processa bloco acumulado com esta data
                    for rubrica, historico, valor_parcial in bloco_acumulador:
                        # Se não conseguiu valor antes, tenta agora
                        if valor_parcial == "PENDENTE":
                            valor_parcial = rastrear_valor_contexto([l[0] for l in todas_linhas], idx, max_distancia=5)
                        
                        resultados.append({
                            "CATEGORIA": rubrica,
                            "VALOR": valor_parcial,
                            "HISTÓRICO": historico[:80],
                            "DATA": data_encontrada
                        })
                    
                    bloco_acumulador = []
                    
                    # Verifica se tem rubrica na mesma linha da data
                    rubrica, encontrada = buscar_rubrica(linha, rubricas_alvo)
                    if encontrada:
                        valores = extrair_todos_valores(linha_up)
                        valor = valores[0] if valores else rastrear_valor_contexto([l[0] for l in todas_linhas], idx, max_distancia=3)
                        
                        resultados.append({
                            "CATEGORIA": rubrica,
                            "VALOR": valor,
                            "HISTÓRICO": linha_up[:80],
                            "DATA": data_encontrada
                        })
                    continue
                
                # Verifica exclusão
                if re.search(TERMOS_EXCLUSAO, linha_up):
                    bloco_acumulador = []
                    continue
                
                # Busca rubrica para acumular
                rubrica, encontrada = buscar_rubrica(linha, rubricas_alvo)
                
                if encontrada:
                    valores = extrair_todos_valores(linha_up)
                    valor = valores[0] if valores else "PENDENTE"
                    
                    bloco_acumulador.append((rubrica, linha_up, valor))
            
            # FASE 3: Processa itens restantes com última data conhecida
            for rubrica, historico, valor in bloco_acumulador:
                if valor == "PENDENTE":
                    valor = rastrear_valor_contexto([l[0] for l in todas_linhas], len(todas_linhas) - 1, max_distancia=5)
                
                resultados.append({
                    "CATEGORIA": rubrica,
                    "VALOR": valor,
                    "HISTÓRICO": historico[:80],
                    "DATA": ultima_data_inferida if ultima_data_inferida else "PENDENTE"
                })
    
    except Exception as e:
        st.error(f"❌ Erro ao processar PDF (DATA_INFERIOR): {str(e)}")
    
    return resultados


def realizar_auditoria(arquivo, rubricas_alvo: List[str], modo_leitura: str = "DATA_SUPERIOR") -> List[Dict]:
    """
    Orquestrador: escolhe motor correto.
    """
    if not rubricas_alvo:
        return []
    
    if modo_leitura == "DATA_INFERIOR":
        return realizar_auditoria_data_inferior(arquivo, rubricas_alvo)
    else:
        return realizar_auditoria_data_superior(arquivo, rubricas_alvo)


# --- 7. GERADOR EXCEL ROBUSTO ---

def gerar_excel_calculos(df: pd.DataFrame, rubrica_nome: str) -> bytes:
    """
    Gera Excel com máxima compatibilidade e robustez.
    """
    if df.empty:
        return None
    
    try:
        df = df.copy()
        
        # Conversão agressiva de valores
        df['V_NUM'] = df['VALOR'].apply(converter_valor_para_float)
        
        # Filtra zeros
        df = df[df['V_NUM'] > 0]
        
        if df.empty:
            return None
        
        # Processamento de datas
        df['DATA_FORMATO'] = df['DATA'].apply(formatar_data)
        df['DT'] = pd.to_datetime(df['DATA_FORMATO'], format='%d/%m/%Y', errors='coerce')
        df = df.dropna(subset=['DT'])
        
        if df.empty:
            return None
        
        df['ANO'] = df['DT'].dt.year.astype(int)
        df['MES_NUM'] = df['DT'].dt.month.astype(int)
        
        # Agregação
        agrupado = df.groupby(['ANO', 'MES_NUM'])['V_NUM'].sum().reset_index()
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Tabela de Cálculos"
        
        # Estilos
        font_header = Font(bold=True, size=11, color="FFFFFF")
        font_title = Font(bold=True, size=12, color="FFFFFF")
        fill_blue = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
        fill_peach = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid")
        fill_total = PatternFill(start_color="92D050", end_color="92D050", fill_type="solid")
        border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
        align_center = Alignment(horizontal='center', vertical='center')
        align_right = Alignment(horizontal='right', vertical='center')
        
        # Cabeçalho
        ws.merge_cells('A1:E1')
        cell_header = ws['A1']
        cell_header.value = f"VALORES DESCONTADOS INDEVIDAMENTE - \"{rubrica_nome}\""
        cell_header.font = font_title
        cell_header.fill = fill_blue
        cell_header.alignment = align_center
        
        meses_nomes = ["JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO", 
                       "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"]
        
        ws['A2'] = "MESES"
        ws['A2'].font = font_header
        ws['A2'].fill = fill_blue
        ws['A2'].alignment = align_center
        
        anos = sorted(agrupado['ANO'].unique())
        if not anos:
            anos = [datetime.now().year]
        
        # Cabeçalhos de anos
        for idx, ano in enumerate(anos):
            col = idx + 2
            cell = ws.cell(row=2, column=col, value=int(ano))
            cell.font = font_header
            cell.fill = fill_blue
            cell.alignment = align_center
            cell.border = border
        
        # Preencher valores
        for m_idx, mes in enumerate(meses_nomes):
            row = m_idx + 3
            cell_mes = ws.cell(row=row, column=1, value=mes)
            cell_mes.font = font_header
            cell_mes.fill = fill_blue
            cell_mes.alignment = align_center
            cell_mes.border = border
            
            for a_idx, ano in enumerate(anos):
                col = a_idx + 2
                val = agrupado[(agrupado['ANO'] == ano) & (agrupado['MES_NUM'] == m_idx + 1)]['V_NUM'].sum()
                
                cell = ws.cell(row=row, column=col)
                if val > 0:
                    cell.value = val
                    cell.number_format = '"R$ " #,##0.00'
                
                cell.fill = fill_peach
                cell.border = border
                cell.alignment = align_right

        # VALOR ANUAL
        row_anual = 15
        cell_anual_label = ws.cell(row=row_anual, column=1, value="VALOR ANUAL:")
        cell_anual_label.font = font_header
        cell_anual_label.fill = fill_blue
        cell_anual_label.border = border
        
        for idx, ano in enumerate(anos):
            col = idx + 2
            col_letter = get_column_letter(col)
            cell = ws.cell(row=row_anual, column=col, value=f"=SUM({col_letter}3:{col_letter}14)")
            cell.number_format = '"R$ " #,##0.00'
            cell.font = font_header
            cell.fill = fill_total
            cell.border = border
            cell.alignment = align_right

        # VALOR TOTAL
        row_total = 16
        cell_total_label = ws.cell(row=row_total, column=1, value="VALOR TOTAL:")
        cell_total_label.font = font_header
        cell_total_label.fill = fill_blue
        cell_total_label.border = border
        
        last_col_letter = get_column_letter(len(anos) + 1)
        ws.merge_cells(start_row=row_total, start_column=2, end_row=row_total, end_column=len(anos)+1)
        cell_total = ws.cell(row=row_total, column=2, value=f"=SUM(B{row_anual}:{last_col_letter}{row_anual})")
        cell_total.number_format = '"R$ " #,##0.00'
        cell_total.font = font_header
        cell_total.fill = fill_total
        cell_total.alignment = align_right
        cell_total.border = border

        # VALOR EM DOBRO
        row_dobro = 17
        ws.merge_cells(start_row=row_dobro, start_column=1, end_row=row_dobro+1, end_column=1)
        cell_dobro_label = ws.cell(row=row_dobro, column=1, value="VALOR EM DOBRO\nART. 42 DO CDC")
        cell_dobro_label.font = font_header
        cell_dobro_label.fill = fill_blue
        cell_dobro_label.alignment = Alignment(wrap_text=True, horizontal='center', vertical='center')
        cell_dobro_label.border = border
        
        ws.merge_cells(start_row=row_dobro, start_column=2, end_row=row_dobro+1, end_column=len(anos)+1)
        cell_dobro = ws.cell(row=row_dobro, column=2, value=f"=B{row_total}*2")
        cell_dobro.number_format = '"R$ " #,##0.00'
        cell_dobro.font = font_header
        cell_dobro.fill = fill_total
        cell_dobro.alignment = align_right
        cell_dobro.border = border

        # Dimensionar colunas
        ws.column_dimensions['A'].width = 25
        for i in range(2, len(anos) + 2):
            ws.column_dimensions[get_column_letter(i)].width = 15

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output.getvalue()
    
    except Exception as e:
        st.error(f"❌ Erro ao gerar Excel: {str(e)}")
        return None


# --- 8. DASHBOARD ---
st.markdown('<h1 class="main-title">⚖️ Consultoria de Ativos</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">🔬 Auditoria Técnica Especializada - Motor ULTRA-PRECISO</p>', unsafe_allow_html=True)

# SIDEBAR
st.sidebar.markdown("### ⚙️ CONFIGURAÇÃO DE LEITURA")

modo_leitura = st.sidebar.radio(
    "Selecione o formato do extrato:",
    options=["DATA_SUPERIOR", "DATA_INFERIOR"],
    format_func=lambda x: "📅 Data Superior (ANEXO 1)" if x == "DATA_SUPERIOR" else "📅 Data Inferior (ANEXO 2)",
    horizontal=False
)

if modo_leitura == "DATA_SUPERIOR":
    st.sidebar.success("✅ Modo DATA SUPERIOR: A data aparece no início")
else:
    st.sidebar.success("✅ Modo DATA INFERIOR: A data aparece abaixo")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 RUBRICAS DE AUDITORIA")

col_b1, col_b2 = st.sidebar.columns(2)
with col_b1:
    if st.button("✅ Marcar Todas", use_container_width=True):
        for rubrica in RUBRICAS_MESTRE.keys():
            st.session_state.rubricas_selecionadas[rubrica] = True
        st.rerun()

with col_b2:
    if st.button("❌ Desmarcar Todas", use_container_width=True):
        for rubrica in RUBRICAS_MESTRE.keys():
            st.session_state.rubricas_selecionadas[rubrica] = False
        st.rerun()

st.sidebar.markdown("")

selecionadas = []
for r in RUBRICAS_MESTRE.keys():
    checked = st.sidebar.checkbox(
        r, 
        value=st.session_state.rubricas_selecionadas.get(r, True),
        key=f"check_{r}"
    )
    st.session_state.rubricas_selecionadas[r] = checked
    if checked:
        selecionadas.append(r)

st.sidebar.markdown("---")
st.sidebar.markdown(f"**🎯 Modo:** {modo_leitura.replace('_', ' ')}")
st.sidebar.markdown(f"**📊 Selecionadas:** {len(selecionadas)}/{len(RUBRICAS_MESTRE)}")

# Debug Mode
st.sidebar.markdown("---")
st.session_state.debug_mode = st.sidebar.checkbox("🐛 Modo Debug", value=st.session_state.debug_mode)

# Upload
upload = st.file_uploader("📂 ARRASTE O EXTRATO BANCÁRIO (PDF)", type=["pdf"])

if upload:
    with st.spinner("⚡ ANALISANDO COM MOTOR ULTRA-PRECISO..."):
        dados = realizar_auditoria(upload, selecionadas, modo_leitura)
        
        if dados:
            df = pd.DataFrame(dados)
            
            # Conversão robusta
            df['V_NUM'] = df['VALOR'].apply(converter_valor_para_float)
            
            # Formata datas
            df['DATA_FORMATO'] = df['DATA'].apply(formatar_data)
            df['DT'] = pd.to_datetime(df['DATA_FORMATO'], format='%d/%m/%Y', errors='coerce')
            
            # Remove linhas sem dados válidos
            df_filtrado = df[(df['V_NUM'] > 0) & (df['DT'].notna())].copy()
            df_filtrado = df_filtrado.sort_values('DT', ascending=True)
            
            if df_filtrado.empty:
                st.error("❌ NENHUM VALOR VÁLIDO FOI EXTRAÍDO DO PDF!")
            else:
                # Métricas
                total_geral = df_filtrado['V_NUM'].sum()
                
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown(
                        f'<div class="metric-card"><h4>💰 TOTAL RECUPERÁVEL</h4>'
                        f'<h2 style="color:#BFAF83;">R$ {total_geral:,.2f}</h2></div>',
                        unsafe_allow_html=True
                    )
                with c2:
                    st.markdown(
                        f'<div class="metric-card"><h4>📝 LANÇAMENTOS</h4>'
                        f'<h2 style="color:#BFAF83;">{len(df_filtrado)}</h2></div>',
                        unsafe_allow_html=True
                    )
                with c3:
                    st.markdown(
                        f'<div class="metric-card"><h4>💼 RUBRICAS</h4>'
                        f'<h2 style="color:#BFAF83;">{df_filtrado["CATEGORIA"].nunique()}</h2></div>',
                        unsafe_allow_html=True
                    )
                
                # Downloads
                st.markdown('<h2 style="color:#BFAF83; text-align:center; margin-top:30px;">📥 Baixar Tabelas</h2>', unsafe_allow_html=True)
                
                cats = sorted(df_filtrado['CATEGORIA'].unique())
                cols = st.columns(min(3, len(cats)))
                
                for idx, cat in enumerate(cats):
                    df_cat = df_filtrado[df_filtrado['CATEGORIA'] == cat]
                    excel_file = gerar_excel_calculos(df_cat, cat)
                    
                    if excel_file:
                        with cols[idx % len(cols)]:
                            st.download_button(
                                label=f"📊 {cat}",
                                data=excel_file,
                                file_name=f"Tabela_{cat.replace(' ', '_')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True
                            )
                
                # Tabela detalhada
                st.markdown('<h3 style="color:#BFAF83; text-align:center; margin-top:30px;">📋 Lista Detalhada</h3>', unsafe_allow_html=True)
                
                df_exib = df_filtrado[['DATA_FORMATO', 'CATEGORIA', 'VALOR', 'HISTÓRICO']].copy()
                df_exib.columns = ['DATA', 'CATEGORIA', 'VALOR (R$)', 'HISTÓRICO']
                
                st.dataframe(df_exib, use_container_width=True, hide_index=True)
                
                # Debug
                if st.session_state.debug_mode:
                    st.markdown("---")
                    st.markdown("### 🐛 INFORMAÇÕES DE DEBUG")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Total de registros extraídos:** {len(df)}")
                        st.write(f"**Registros com valor válido:** {len(df_filtrado)}")
                        st.write(f"**Registros descartados:** {len(df) - len(df_filtrado)}")
                    
                    with col2:
                        st.write(f"**Período:** {df_filtrado['DATA_FORMATO'].min()} a {df_filtrado['DATA_FORMATO'].max()}")
                        st.write(f"**Maior valor:** R$ {df_filtrado['V_NUM'].max():,.2f}")
                        st.write(f"**Menor valor:** R$ {df_filtrado['V_NUM'].min():,.2f}")
                    
                    with st.expander("📊 Visualizar dados brutos"):
                        st.dataframe(df, use_container_width=True)
        else:
            st.error("❌ NENHUM DADO EXTRAÍDO! Verifique o PDF e as rubricas selecionadas.")

st.markdown("<br><br><p style='text-align:right; font-family:serif; font-style:italic; color:#BFAF83;'>🔬 Motor Ultra-Preciso - Edson Medeiros</p>", unsafe_allow_html=True)
