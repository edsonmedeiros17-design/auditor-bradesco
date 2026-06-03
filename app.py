import streamlit as st
import pdfplumber
import pandas as pd
import re
from datetime import datetime
import io
from typing import List, Dict, Tuple, Optional

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
    .debug-box { background: rgba(50, 150, 200, 0.1); border: 1px solid #3296C8; border-radius: 8px; padding: 10px; margin: 10px 0; font-size: 11px; max-height: 500px; overflow-y: auto; }
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

# --- 3. SESSION STATE ---
if 'rubricas_selecionadas' not in st.session_state:
    st.session_state.rubricas_selecionadas = {r: True for r in RUBRICAS_MESTRE.keys()}
if 'debug_mode' not in st.session_state:
    st.session_state.debug_mode = False
if 'log_debug' not in st.session_state:
    st.session_state.log_debug = []

# --- 4. FUNÇÕES AUXILIARES ---

def limpar_log():
    """Limpa o log de debug."""
    st.session_state.log_debug = []

def adicionar_log(mensagem: str):
    """Adiciona mensagem ao log de debug."""
    st.session_state.log_debug.append(mensagem)

def extrair_valor(texto: str) -> Optional[str]:
    """
    Extrai o PRIMEIRO valor monetário da string.
    PADRÃO BRASILEIRO: 1,23 | 10,00 | 1.234,56 | 1.234.567,89
    Retorna None se não encontrar valor.
    """
    # Padrão: captura valores com até 3 dígitos, depois pontos de milhar, depois 2 casas decimais
    pattern = r'(\d{1,3}(?:\.\d{3})*,\d{2})'
    match = re.search(pattern, texto)
    if match:
        return match.group(1)
    return None

def converter_valor_para_float(valor_str: Optional[str]) -> float:
    """
    Converte valor brasileiro para float com segurança total.
    """
    if not valor_str or valor_str == "PENDENTE":
        return 0.0
    
    try:
        valor_str = str(valor_str).strip()
        if '%' in valor_str or not valor_str:
            return 0.0
        
        # Remove pontos (separador de milhar)
        valor_str = valor_str.replace('.', '')
        # Substitui vírgula por ponto
        valor_str = valor_str.replace(',', '.')
        
        valor_float = float(valor_str)
        return valor_float if valor_float > 0 else 0.0
    except:
        return 0.0

def extrair_data(texto: str) -> Optional[str]:
    """
    Extrai a PRIMEIRA data do texto.
    PADRÃO: dd/mm/yyyy ou dd/mm/yy
    """
    pattern = r'(\d{2}/\d{2}/\d{2,4})'
    match = re.search(pattern, texto)
    if match:
        data_str = match.group(1)
        return formatar_data(data_str)
    return None

def formatar_data(data_str: str) -> str:
    """
    Formata data para padrão dd/mm/yyyy com validação.
    """
    if not data_str or data_str == "PENDENTE":
        return "PENDENTE"
    
    try:
        partes = data_str.split('/')
        if len(partes) != 3:
            return "PENDENTE"
        
        dia, mes, ano = partes
        
        # Valida dia e mês
        dia_int = int(dia)
        mes_int = int(mes)
        
        if not (1 <= dia_int <= 31 and 1 <= mes_int <= 12):
            return "PENDENTE"
        
        # Adiciona século se necessário
        if len(ano) == 2:
            ano = "20" + ano
        
        return f"{dia}/{mes}/{ano}"
    except:
        return "PENDENTE"

def detectar_rubrica(linha: str, rubricas_alvo: List[str]) -> Optional[str]:
    """
    Detecta a rubrica presente na linha.
    Retorna o nome da rubrica ou None.
    """
    linha_up = linha.upper().strip()
    
    # Não processa linhas com porcentagem
    if "%" in linha_up:
        return None
    
    for nome in rubricas_alvo:
        if re.search(RUBRICAS_MESTRE[nome], linha_up):
            return nome
    
    return None

# --- 5. MOTOR CIRÚRGICO - ANÁLISE LINHA POR LINHA ---

def realizar_auditoria_data_superior_cirurgica(arquivo, rubricas_alvo: List[str]) -> List[Dict]:
    """
    MOTOR CIRÚRGICO - DATA SUPERIOR (ANEXO 1)
    
    LÓGICA INFALÍVEL:
    - Varre TODA linha de cada página
    - Identifica DATA (atualiza contexto)
    - Identifica RUBRICA (captura imediatamente)
    - Captura VALOR da mesma linha ou próxima linha
    - NENHUMA rubrica é deixada passar
    """
    resultados = []
    limpar_log()
    
    try:
        with pdfplumber.open(arquivo) as pdf:
            ultima_data = None
            
            for page_num, page in enumerate(pdf.pages):
                texto = page.extract_text(x_tolerance=2, y_tolerance=2)
                if not texto:
                    adicionar_log(f"[PÁGINA {page_num + 1}] Sem texto extraído")
                    continue
                
                linhas = texto.split('\n')
                adicionar_log(f"\n[PÁGINA {page_num + 1}] {len(linhas)} linhas processadas")
                
                for idx_linha, linha in enumerate(linhas):
                    linha_stripped = linha.strip()
                    
                    # Ignora linhas vazias
                    if not linha_stripped:
                        continue
                    
                    linha_up = linha_stripped.upper()
                    
                    # ===== PASSO 1: Procura DATA =====
                    data_encontrada = extrair_data(linha_up)
                    if data_encontrada and data_encontrada != "PENDENTE":
                        ultima_data = data_encontrada
                        adicionar_log(f"  [L{idx_linha}] DATA ENCONTRADA: {ultima_data}")
                        continue
                    
                    # ===== PASSO 2: Verifica EXCLUSÃO =====
                    if re.search(TERMOS_EXCLUSAO, linha_up):
                        adicionar_log(f"  [L{idx_linha}] Linha descartada (exclusão)")
                        continue
                    
                    # ===== PASSO 3: Procura RUBRICA =====
                    rubrica = detectar_rubrica(linha_stripped, rubricas_alvo)
                    if rubrica:
                        # ===== PASSO 4: Extrai VALOR =====
                        valor_str = extrair_valor(linha_up)
                        
                        # Se não encontrou valor na mesma linha, procura na próxima
                        if not valor_str and idx_linha + 1 < len(linhas):
                            proxima_linha = linhas[idx_linha + 1].upper()
                            valor_str = extrair_valor(proxima_linha)
                            if valor_str:
                                adicionar_log(f"  [L{idx_linha}] RUBRICA: {rubrica} | VALOR NA PRÓXIMA LINHA: {valor_str}")
                        
                        if valor_str:
                            adicionar_log(f"  [L{idx_linha}] RUBRICA: {rubrica} | VALOR: {valor_str} | DATA: {ultima_data}")
                        else:
                            adicionar_log(f"  [L{idx_linha}] RUBRICA: {rubrica} | VALOR: NÃO ENCONTRADO")
                        
                        resultados.append({
                            "PÁGINA": page_num + 1,
                            "LINHA": idx_linha,
                            "CATEGORIA": rubrica,
                            "VALOR": valor_str if valor_str else "PENDENTE",
                            "HISTÓRICO": linha_stripped[:100],
                            "DATA": ultima_data if ultima_data else "PENDENTE"
                        })
    
    except Exception as e:
        st.error(f"❌ Erro ao processar PDF: {str(e)}")
        adicionar_log(f"ERRO: {str(e)}")
    
    return resultados


def realizar_auditoria_data_inferior_cirurgica(arquivo, rubricas_alvo: List[str]) -> List[Dict]:
    """
    MOTOR CIRÚRGICO - DATA INFERIOR (ANEXO 2)
    
    LÓGICA INFALÍVEL:
    - Varre TODA linha de cada página
    - Acumula RUBRICAS em buffer sem data
    - Quando encontra DATA, sela todas as rubricas com aquela data
    - NENHUMA rubrica é deixada passar
    """
    resultados = []
    limpar_log()
    
    try:
        with pdfplumber.open(arquivo) as pdf:
            buffer_rubricas = []  # Buffer: (rubrica, historico, valor, idx_linha)
            ultima_data_encontrada = None
            
            for page_num, page in enumerate(pdf.pages):
                texto = page.extract_text(x_tolerance=2, y_tolerance=2)
                if not texto:
                    adicionar_log(f"[PÁGINA {page_num + 1}] Sem texto extraído")
                    continue
                
                linhas = texto.split('\n')
                adicionar_log(f"\n[PÁGINA {page_num + 1}] {len(linhas)} linhas processadas")
                
                for idx_linha, linha in enumerate(linhas):
                    linha_stripped = linha.strip()
                    
                    # Ignora linhas vazias
                    if not linha_stripped:
                        continue
                    
                    linha_up = linha_stripped.upper()
                    
                    # ===== PASSO 1: Procura DATA (DATA INFERIOR) =====
                    data_encontrada = extrair_data(linha_up)
                    if data_encontrada and data_encontrada != "PENDENTE":
                        ultima_data_encontrada = data_encontrada
                        adicionar_log(f"  [L{idx_linha}] DATA ENCONTRADA: {ultima_data_encontrada}")
                        
                        # ===== PASSO 2: Sela todas as rubricas do buffer com essa data =====
                        if buffer_rubricas:
                            for rubrica, historico, valor, idx in buffer_rubricas:
                                # Se não tem valor, tenta extrair da linha da data
                                if valor == "PENDENTE":
                                    valor_tentativa = extrair_valor(linha_up)
                                    if valor_tentativa:
                                        valor = valor_tentativa
                                
                                resultados.append({
                                    "PÁGINA": page_num + 1,
                                    "LINHA": idx,
                                    "CATEGORIA": rubrica,
                                    "VALOR": valor,
                                    "HISTÓRICO": historico[:100],
                                    "DATA": ultima_data_encontrada
                                })
                                adicionar_log(f"    [SELLADO] {rubrica}: {valor} | DATA: {ultima_data_encontrada}")
                            
                            buffer_rubricas = []
                        
                        # Verifica se tem rubrica na mesma linha da data
                        rubrica = detectar_rubrica(linha_stripped, rubricas_alvo)
                        if rubrica:
                            valor_str = extrair_valor(linha_up)
                            if not valor_str and idx_linha + 1 < len(linhas):
                                valor_str = extrair_valor(linhas[idx_linha + 1].upper())
                            
                            resultados.append({
                                "PÁGINA": page_num + 1,
                                "LINHA": idx_linha,
                                "CATEGORIA": rubrica,
                                "VALOR": valor_str if valor_str else "PENDENTE",
                                "HISTÓRICO": linha_stripped[:100],
                                "DATA": ultima_data_encontrada
                            })
                            adicionar_log(f"  [L{idx_linha}] RUBRICA NA DATA: {rubrica} | VALOR: {valor_str}")
                        
                        continue
                    
                    # ===== PASSO 3: Verifica EXCLUSÃO =====
                    if re.search(TERMOS_EXCLUSAO, linha_up):
                        adicionar_log(f"  [L{idx_linha}] Linha descartada (exclusão)")
                        continue
                    
                    # ===== PASSO 4: Procura RUBRICA para buffer =====
                    rubrica = detectar_rubrica(linha_stripped, rubricas_alvo)
                    if rubrica:
                        # ===== PASSO 5: Extrai VALOR =====
                        valor_str = extrair_valor(linha_up)
                        
                        # Se não encontrou, procura na próxima linha
                        if not valor_str and idx_linha + 1 < len(linhas):
                            proxima_linha = linhas[idx_linha + 1].upper()
                            valor_str = extrair_valor(proxima_linha)
                        
                        buffer_rubricas.append((rubrica, linha_stripped, valor_str if valor_str else "PENDENTE", idx_linha))
                        adicionar_log(f"  [L{idx_linha}] BUFFER: {rubrica} | VALOR: {valor_str if valor_str else 'PENDENTE'}")
            
            # Processa rubricas restantes no buffer (ao final do PDF)
            if buffer_rubricas:
                adicionar_log(f"\n[FIM PDF] Processando {len(buffer_rubricas)} rubricas pendentes no buffer")
                for rubrica, historico, valor, idx in buffer_rubricas:
                    resultados.append({
                        "PÁGINA": "?",
                        "LINHA": idx,
                        "CATEGORIA": rubrica,
                        "VALOR": valor,
                        "HISTÓRICO": historico[:100],
                        "DATA": ultima_data_encontrada if ultima_data_encontrada else "PENDENTE"
                    })
                    adicionar_log(f"  {rubrica}: {valor} | DATA: {ultima_data_encontrada if ultima_data_encontrada else 'PENDENTE'}")
    
    except Exception as e:
        st.error(f"❌ Erro ao processar PDF: {str(e)}")
        adicionar_log(f"ERRO: {str(e)}")
    
    return resultados


def realizar_auditoria(arquivo, rubricas_alvo: List[str], modo_leitura: str = "DATA_SUPERIOR") -> List[Dict]:
    """
    Orquestrador: escolhe motor correto.
    """
    if not rubricas_alvo:
        return []
    
    if modo_leitura == "DATA_INFERIOR":
        return realizar_auditoria_data_inferior_cirurgica(arquivo, rubricas_alvo)
    else:
        return realizar_auditoria_data_superior_cirurgica(arquivo, rubricas_alvo)


# --- 6. GERADOR EXCEL ---

def gerar_excel_calculos(df: pd.DataFrame, rubrica_nome: str) -> Optional[bytes]:
    """
    Gera Excel com tabela de cálculos por mês/ano.
    """
    if df.empty:
        return None
    
    try:
        df = df.copy()
        
        # Conversão
        df['V_NUM'] = df['VALOR'].apply(converter_valor_para_float)
        df = df[df['V_NUM'] > 0]
        
        if df.empty:
            return None
        
        # Datas
        df['DT'] = pd.to_datetime(df['DATA'], format='%d/%m/%Y', errors='coerce')
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

        # Dimensionar
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


# --- 7. DASHBOARD ---
st.markdown('<h1 class="main-title">⚖️ Consultoria de Ativos</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">🔬 Auditoria Técnica Cirúrgica - Motor Linha-por-Linha</p>', unsafe_allow_html=True)

# SIDEBAR
st.sidebar.markdown("### ⚙️ CONFIGURAÇÃO DE LEITURA")

modo_leitura = st.sidebar.radio(
    "Selecione o formato do extrato:",
    options=["DATA_SUPERIOR", "DATA_INFERIOR"],
    format_func=lambda x: "📅 Data Superior (ANEXO 1)" if x == "DATA_SUPERIOR" else "📅 Data Inferior (ANEXO 2)",
    horizontal=False
)

if modo_leitura == "DATA_SUPERIOR":
    st.sidebar.success("✅ Modo DATA SUPERIOR")
else:
    st.sidebar.success("✅ Modo DATA INFERIOR")

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
st.sidebar.markdown(f"**🎯 Selecionadas:** {len(selecionadas)}/{len(RUBRICAS_MESTRE)}")

# Debug Mode
st.sidebar.markdown("---")
st.session_state.debug_mode = st.sidebar.checkbox("🐛 Modo Debug Detalhado", value=st.session_state.debug_mode)

# Upload
upload = st.file_uploader("📂 ARRASTE O EXTRATO BANCÁRIO (PDF)", type=["pdf"])

if upload:
    with st.spinner("⚡ ANALISANDO LINHA POR LINHA..."):
        dados = realizar_auditoria(upload, selecionadas, modo_leitura)
        
        if dados:
            df = pd.DataFrame(dados)
            
            # Conversão
            df['V_NUM'] = df['VALOR'].apply(converter_valor_para_float)
            
            # Filtra válidos
            df_valido = df[(df['V_NUM'] > 0) & (df['DATA'] != "PENDENTE")].copy()
            df_valido['DT'] = pd.to_datetime(df_valido['DATA'], format='%d/%m/%Y', errors='coerce')
            df_valido = df_valido.dropna(subset=['DT'])
            df_valido = df_valido.sort_values('DT', ascending=True)
            
            if df_valido.empty:
                st.error("❌ NENHUM VALOR VÁLIDO ENCONTRADO!")
            else:
                # Métricas
                total_geral = df_valido['V_NUM'].sum()
                
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
                        f'<h2 style="color:#BFAF83;">{len(df_valido)}</h2></div>',
                        unsafe_allow_html=True
                    )
                with c3:
                    st.markdown(
                        f'<div class="metric-card"><h4>💼 RUBRICAS</h4>'
                        f'<h2 style="color:#BFAF83;">{df_valido["CATEGORIA"].nunique()}</h2></div>',
                        unsafe_allow_html=True
                    )
                
                # Downloads
                st.markdown('<h2 style="color:#BFAF83; text-align:center; margin-top:30px;">📥 Baixar Tabelas</h2>', unsafe_allow_html=True)
                
                cats = sorted(df_valido['CATEGORIA'].unique())
                cols = st.columns(min(3, len(cats)))
                
                for idx, cat in enumerate(cats):
                    df_cat = df_valido[df_valido['CATEGORIA'] == cat]
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
                
                # Tabela
                st.markdown('<h3 style="color:#BFAF83; text-align:center; margin-top:30px;">📋 Extrato Completo</h3>', unsafe_allow_html=True)
                
                df_exib = df_valido[['DATA', 'CATEGORIA', 'VALOR', 'HISTÓRICO']].copy()
                df_exib.columns = ['DATA', 'CATEGORIA', 'VALOR (R$)', 'HISTÓRICO']
                df_exib = df_exib.reset_index(drop=True)
                
                st.dataframe(df_exib, use_container_width=True, hide_index=True)
                
                # Debug
                if st.session_state.debug_mode:
                    st.markdown("---")
                    st.markdown("### 🐛 DEBUG: ANÁLISE LINHA-POR-LINHA")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Total de registros extraídos:** {len(df)}")
                        st.write(f"**Registros com valor válido:** {len(df_valido)}")
                        st.write(f"**Registros descartados:** {len(df) - len(df_valido)}")
                    
                    with col2:
                        st.write(f"**Total de rubricas encontradas:** {df['CATEGORIA'].nunique()}")
                        st.write(f"**Período:** {df_valido['DATA'].min()} a {df_valido['DATA'].max()}")
                    
                    with st.expander("📋 Log Detalhado de Processamento"):
                        log_text = "\n".join(st.session_state.log_debug)
                        st.markdown(f'<div class="debug-box">{log_text}</div>', unsafe_allow_html=True)
                    
                    with st.expander("📊 Visualizar todos os registros (incluindo PENDENTES)"):
                        st.dataframe(df, use_container_width=True)
        else:
            st.error("❌ NENHUM DADO EXTRAÍDO!")

st.markdown("<br><br><p style='text-align:right; font-family:serif; font-style:italic; color:#BFAF83;'>🔬 Melhor Programador do Mundo - Edson Medeiros</p>", unsafe_allow_html=True)
