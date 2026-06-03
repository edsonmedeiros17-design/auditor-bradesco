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

# --- 1. CONFIGURAÇÃO E ESTILO ---
st.set_page_config(page_title="Edson Medeiros | Consultoria de Ativos", layout="wide", page_icon="⚖️")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;600&display=swap');
    .stApp { background-color: #0E1117; color: #FFFFFF; font-family: 'Inter', sans-serif; }
    .main-title { font-family: 'Playfair Display', serif; font-size: 3rem; color: #BFAF83; text-align: center; margin-bottom: 0; }
    .sub-title { text-align: center; color: #64748B; letter-spacing: 2px; text-transform: uppercase; font-size: 0.9rem; margin-bottom: 40px; }
    .metric-card { background: rgba(255,255,255,0.05); border: 1px solid #BFAF83; border-radius: 10px; padding: 20px; text-align: center; }
    .info-card { background: rgba(191,175,131,0.1); border: 2px solid #BFAF83; border-radius: 10px; padding: 15px; margin: 15px 0; }
</style>
""", unsafe_allow_html=True)

# --- 2. RÚBRICAS ATUALIZADAS ---
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

# --- 3. MOTOR COM LÓGICA DE DATA SUPERIOR/INFERIOR ---
def realizar_auditoria_data_superior(arquivo, rubricas_alvo):
    """
    Análise no formato DATA SUPERIOR (ANEXO 1):
    - Data aparece logo ao lado da primeira movimentação
    - Todas as movimentações abaixo até a próxima 'linha divisória' pertencem àquela data
    - O robô segue para a coluna débito e coleta o valor EXATO da rubrica
    """
    resultados = []
    linhas_processadas = []
    
    with pdfplumber.open(arquivo) as pdf:
        for page in pdf.pages:
            texto = page.extract_text(x_tolerance=3, y_tolerance=3)
            if not texto:
                continue
            linhas = texto.split('\n')
            linhas_processadas.extend(linhas)
    
    i = 0
    data_atual = None
    
    while i < len(linhas_processadas):
        linha = linhas_processadas[i].strip()
        if not linha:
            i += 1
            continue
        
        linha_up = linha.upper()
        
        # Detecta data no formato DD/MM/YYYY ou DD/MM/YY
        match_data = re.search(r"(\d{2}/\d{2}/\d{2,4})", linha_up)
        
        # Detecta valor no formato brasileiro (1.234,56)
        match_valor = re.search(r"([\d\.]+,\d{2})", linha)
        
        # Detecta linha divisória
        eh_linha_divisoria = re.search(r"^[\s\-_=]{5,}$", linha)
        
        # LÓGICA DATA SUPERIOR: Data identifica o período
        if match_data:
            data_encontrada = match_data.group(1)
            data_atual = data_encontrada
            
            # Verifica se há rubrica na mesma linha da data
            rubrica_detectada = detectar_rubrica(linha_up, rubricas_alvo)
            if rubrica_detectada and match_valor:
                resultados.append({
                    "DATA": data_atual,
                    "CATEGORIA": rubrica_detectada,
                    "VALOR": match_valor.group(1),
                    "HISTÓRICO": linha[:80],
                    "TIPO": "DATA_SUPERIOR"
                })
        
        # Coleta rubricas no período até próxima data/divisória
        elif data_atual:
            # Reset por termos de exclusão
            if re.search(TERMOS_EXCLUSAO, linha_up):
                i += 1
                continue
            
            rubrica_detectada = detectar_rubrica(linha_up, rubricas_alvo)
            
            if rubrica_detectada and match_valor:
                resultados.append({
                    "DATA": data_atual,
                    "CATEGORIA": rubrica_detectada,
                    "VALOR": match_valor.group(1),
                    "HISTÓRICO": linha[:80],
                    "TIPO": "DATA_SUPERIOR"
                })
            
            # Linha divisória = reset da data atual
            if eh_linha_divisoria:
                data_atual = None
        
        i += 1
    
    return resultados


def realizar_auditoria_data_inferior(arquivo, rubricas_alvo):
    """
    Análise no formato DATA INFERIOR (ANEXO 2):
    - Movimentações aparecem com a data ao lado ou apenas na última movimentação
    - Todas as movimentações que não possuem data pertencem à data da última movimentação daquele período
    - Usa linha divisória como marcador de fim do período
    """
    resultados = []
    linhas_processadas = []
    
    with pdfplumber.open(arquivo) as pdf:
        for page in pdf.pages:
            texto = page.extract_text(x_tolerance=3, y_tolerance=3)
            if not texto:
                continue
            linhas = texto.split('\n')
            linhas_processadas.extend(linhas)
    
    i = 0
    bloco_movimentacoes = []
    data_do_bloco = None
    
    while i < len(linhas_processadas):
        linha = linhas_processadas[i].strip()
        if not linha:
            i += 1
            continue
        
        linha_up = linha.upper()
        
        # Detecta data
        match_data = re.search(r"(\d{2}/\d{2}/\d{2,4})", linha_up)
        
        # Detecta valor
        match_valor = re.search(r"([\d\.]+,\d{2})", linha)
        
        # Detecta linha divisória
        eh_linha_divisoria = re.search(r"^[\s\-_=]{5,}$", linha)
        
        # Reset por termos de exclusão
        if re.search(TERMOS_EXCLUSAO, linha_up):
            if bloco_movimentacoes:
                resultados.extend(processar_bloco_data_inferior(bloco_movimentacoes, data_do_bloco, rubricas_alvo))
                bloco_movimentacoes = []
                data_do_bloco = None
            i += 1
            continue
        
        rubrica_detectada = detectar_rubrica(linha_up, rubricas_alvo)
        
        # Se encontra data, atualiza a data do bloco
        if match_data:
            data_do_bloco = match_data.group(1)
        
        # Adiciona movimento ao bloco se tem rubrica ou valor
        if rubrica_detectada or match_valor:
            bloco_movimentacoes.append({
                "linha_original": linha,
                "linha_upper": linha_up,
                "rubrica": rubrica_detectada,
                "valor": match_valor.group(1) if match_valor else None,
                "tem_data": bool(match_data)
            })
        
        # Linha divisória = finaliza bloco
        if eh_linha_divisoria and bloco_movimentacoes:
            resultados.extend(processar_bloco_data_inferior(bloco_movimentacoes, data_do_bloco, rubricas_alvo))
            bloco_movimentacoes = []
            data_do_bloco = None
        
        i += 1
    
    # Processa bloco final se existir
    if bloco_movimentacoes:
        resultados.extend(processar_bloco_data_inferior(bloco_movimentacoes, data_do_bloco, rubricas_alvo))
    
    return resultados


def detectar_rubrica(linha_upper, rubricas_alvo):
    """
    Detecta qual rubrica está presente na linha.
    Retorna o nome da primeira rubrica encontrada.
    """
    if "%" in linha_upper:
        return None
    
    for nome in rubricas_alvo:
        if re.search(RUBRICAS_MESTRE[nome], linha_upper):
            return nome
    
    return None


def processar_bloco_data_inferior(bloco, data_final, rubricas_alvo):
    """
    Processa um bloco de movimentações no formato DATA INFERIOR.
    
    Lógica:
    1. Identifica todas as rubricas no bloco
    2. Coleta valores correspondentes
    3. Associa TODAS as movimentações à data_final (última data do período)
    """
    resultados = []
    
    if not data_final:
        return resultados
    
    for item in bloco:
        if item["rubrica"]:  # Tem rubrica identificada
            valor = item["valor"]
            if valor:
                resultados.append({
                    "DATA": data_final,
                    "CATEGORIA": item["rubrica"],
                    "VALOR": valor,
                    "HISTÓRICO": item["linha_original"][:80],
                    "TIPO": "DATA_INFERIOR"
                })
    
    return resultados


# --- 4. FUNÇÃO PARA GERAR PLANILHA DE CÁLCULOS ---
def gerar_excel_calculos(df, rubrica_nome):
    df = df.copy()
    
    def fix_date(d):
        p = d.split('/')
        if len(p[2]) == 2:
            p[2] = "20" + p[2]
        return "/".join(p)
    
    df['DT'] = pd.to_datetime(df['DATA'].apply(fix_date), format='%d/%m/%Y')
    df['ANO'] = df['DT'].dt.year
    df['MES_NUM'] = df['DT'].dt.month
    
    # Agrupar e somar valores do mesmo mês/ano
    agrupado = df.groupby(['ANO', 'MES_NUM'])['V_NUM'].sum().reset_index()
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Tabela de Cálculos"
    
    # Estilos
    font_header = Font(bold=True, size=11)
    font_title = Font(bold=True, size=12)
    fill_blue = PatternFill(start_color="BDD7EE", end_color="BDD7EE", fill_type="solid")
    fill_peach = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid")
    border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
    align_center = Alignment(horizontal='center', vertical='center')
    
    # Cabeçalho
    ws.merge_cells('A1:E1')
    ws['A1'] = f"VALORES DESCONTADOS INDEVIDAMENTE - \"{rubrica_nome}\""
    ws['A1'].font = font_title
    ws['A1'].fill = fill_blue
    ws['A1'].alignment = align_center
    
    meses_nomes = ["JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO", 
                   "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"]
    
    ws['A2'] = "MESES"
    ws['A2'].font = font_header
    ws['A2'].alignment = align_center
    
    anos = sorted(agrupado['ANO'].unique())
    if not anos:
        anos = [datetime.now().year]
    
    for idx, ano in enumerate(anos):
        col = idx + 2
        ws.cell(row=2, column=col, value=ano).font = font_header
        ws.cell(row=2, column=col).alignment = align_center
        ws.cell(row=2, column=col).fill = fill_blue
    
    # Preencher Valores
    for m_idx, mes in enumerate(meses_nomes):
        row = m_idx + 3
        ws.cell(row=row, column=1, value=mes).font = font_header
        ws.cell(row=row, column=1).fill = fill_blue
        
        for a_idx, ano in enumerate(anos):
            col = a_idx + 2
            val = agrupado[(agrupado['ANO'] == ano) & (agrupado['MES_NUM'] == m_idx + 1)]['V_NUM'].sum()
            if val > 0:
                cell = ws.cell(row=row, column=col, value=val)
                cell.number_format = '"R$ " #,##0.00'
            ws.cell(row=row, column=col).fill = fill_peach
            ws.cell(row=row, column=col).border = border

    # Fórmulas: VALOR ANUAL
    row_anual = 15
    ws.cell(row=row_anual, column=1, value="VALOR ANUAL:").font = font_header
    ws.cell(row=row_anual, column=1).fill = fill_blue
    
    for idx, ano in enumerate(anos):
        col = idx + 2
        col_letter = get_column_letter(col)
        formula = f"=SUM({col_letter}3:{col_letter}14)"
        cell = ws.cell(row=row_anual, column=col, value=formula)
        cell.number_format = '"R$ " #,##0.00'
        cell.font = font_header
        cell.fill = fill_peach
        cell.border = border

    # Fórmula: VALOR TOTAL
    row_total = 16
    ws.cell(row=row_total, column=1, value="VALOR TOTAL:").font = font_header
    ws.cell(row=row_total, column=1).fill = fill_blue
    
    last_col_letter = get_column_letter(len(anos) + 1)
    formula_total = f"=SUM(B{row_anual}:{last_col_letter}{row_anual})"
    ws.merge_cells(start_row=row_total, start_column=2, end_row=row_total, end_column=len(anos)+1)
    cell_total = ws.cell(row=row_total, column=2, value=formula_total)
    cell_total.number_format = '"R$ " #,##0.00'
    cell_total.font = font_header
    cell_total.alignment = Alignment(horizontal='right')
    
    # Fórmula: VALOR EM DOBRO (Art. 42 CDC)
    row_dobro = 17
    ws.merge_cells(start_row=row_dobro, start_column=1, end_row=row_dobro+1, end_column=1)
    ws.cell(row=row_dobro, column=1, value="VALOR EM DOBRO ART. 42 DO CDC").font = font_header
    ws.cell(row=row_dobro, column=1).alignment = Alignment(wrap_text=True, horizontal='center', vertical='center')
    ws.cell(row=row_dobro, column=1).fill = fill_blue
    
    ws.merge_cells(start_row=row_dobro, start_column=2, end_row=row_dobro+1, end_column=len(anos)+1)
    formula_dobro = f"=B{row_total}*2"
    cell_dobro = ws.cell(row=row_dobro, column=2, value=formula_dobro)
    cell_dobro.number_format = '"R$ " #,##0.00'
    cell_dobro.font = font_header
    cell_dobro.alignment = Alignment(horizontal='right', vertical='center')
    cell_dobro.fill = fill_peach

    ws.column_dimensions['A'].width = 25
    for i in range(2, len(anos) + 2):
        ws.column_dimensions[get_column_letter(i)].width = 15

    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()


# --- 5. DASHBOARD ---
st.markdown('<h1 class="main-title">Consultoria de Ativos</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Auditoria Técnica Especializada - Edson Medeiros</p>', unsafe_allow_html=True)

# --- SELEÇÃO DE FORMATO DE DATA ---
st.markdown('<h3 style="color:#BFAF83; margin-top:20px;">📅 Formato do Extrato Bancário</h3>', unsafe_allow_html=True)

col_formato = st.columns(2)

with col_formato[0]:
    if st.button("📍 DATA SUPERIOR (ANEXO 1)", use_container_width=True):
        st.session_state.formato = "DATA_SUPERIOR"

with col_formato[1]:
    if st.button("📍 DATA INFERIOR (ANEXO 2)", use_container_width=True):
        st.session_state.formato = "DATA_INFERIOR"

# Inicializa formato na sessão
if 'formato' not in st.session_state:
    st.session_state.formato = None

# Exibe informação do formato selecionado
if st.session_state.formato:
    if st.session_state.formato == "DATA_SUPERIOR":
        st.markdown("""
        <div class="info-card">
        <strong>✅ Modo: DATA SUPERIOR</strong><br>
        📌 Data aparece ao lado da primeira movimentação<br>
        📌 Todas as movimentações abaixo até a próxima linha divisória pertencem àquela data<br>
        📌 O robô coleta o valor exato de cada rubrica identificada
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="info-card">
        <strong>✅ Modo: DATA INFERIOR</strong><br>
        📌 Movimentações aparecem sem data ao lado<br>
        📌 Data aparece apenas na última movimentação do período<br>
        📌 Todas as movimentações sem data pertencem à última data identificada
        </div>
        """, unsafe_allow_html=True)

# --- SELEÇÃO DE RUBRICAS ---
if st.session_state.formato:
    st.sidebar.markdown("### 🔍 RUBRICAS DE AUDITORIA")
    if 'sel_all' not in st.session_state:
        st.session_state.sel_all = True

    col_b1, col_b2 = st.sidebar.columns(2)
    if col_b1.button("Marcar Todas"):
        st.session_state.sel_all = True
    if col_b2.button("Desmarcar Todas"):
        st.session_state.sel_all = False

    selecionadas = []
    for r in RUBRICAS_MESTRE.keys():
        if st.sidebar.checkbox(r, value=st.session_state.sel_all, key=f"check_{r}"):
            selecionadas.append(r)

    upload = st.file_uploader("📂 ARRASTE O EXTRATO BANCÁRIO (PDF)", type=["pdf"])

    if upload:
        with st.spinner(f"Analisando extrato no formato {st.session_state.formato}..."):
            # Executa auditoria baseado no formato selecionado
            if st.session_state.formato == "DATA_SUPERIOR":
                dados = realizar_auditoria_data_superior(upload, selecionadas)
            else:
                dados = realizar_auditoria_data_inferior(upload, selecionadas)
            
            if dados:
                df = pd.DataFrame(dados)
                df['V_NUM'] = df['VALOR'].str.replace('.', '', regex=False).str.replace(',', '.', regex=False).astype(float)
                
                # Ordenação Cronológica Real
                def fix_date(d):
                    p = d.split('/')
                    if len(p[2]) == 2:
                        p[2] = "20" + p[2]
                    return "/".join(p)
                
                df['DT_O'] = pd.to_datetime(df['DATA'].apply(fix_date), format='%d/%m/%Y', errors='coerce')
                df = df.sort_values('DT_O', ascending=True)
                
                total_geral = df['V_NUM'].sum()
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f'<div class="metric-card"><h4>TOTAL RECUPERÁVEL</h4><h2 style="color:#BFAF83;">R$ {total_geral:,.2f}</h2></div>', unsafe_allow_html=True)
                with c2:
                    st.markdown(f'<div class="metric-card"><h4>LANÇAMENTOS</h4><h2 style="color:#BFAF83;">{len(df)}</h2></div>', unsafe_allow_html=True)
                
                st.markdown('<h2 style="color:#BFAF83; text-align:center; margin-top:30px;">📥 Baixar Tabelas de Cálculos</h2>', unsafe_allow_html=True)
                st.write("Clique nos botões abaixo para baixar a planilha de cada rubrica com fórmulas automáticas.")
                
                cats = df['CATEGORIA'].unique()
                cols = st.columns(2)
                for idx, cat in enumerate(cats):
                    df_cat = df[df['CATEGORIA'] == cat]
                    excel_file = gerar_excel_calculos(df_cat, cat)
                    col_idx = idx % 2
                    with cols[col_idx]:
                        st.download_button(
                            label=f"📊 {cat}",
                            data=excel_file,
                            file_name=f"Tabela_Calculos_{cat.replace(' ', '_')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                
                st.markdown('<h3 style="color:#BFAF83; text-align:center; margin-top:30px;">📋 Lista Detalhada</h3>', unsafe_allow_html=True)
                st.dataframe(df[['DATA', 'CATEGORIA', 'VALOR', 'TIPO', 'HISTÓRICO']], use_container_width=True)
            else:
                st.info("Nenhum débito encontrado com as rubricas selecionadas.")
else:
    st.warning("⚠️ Por favor, selecione o formato do extrato acima para continuar.")

st.markdown("<br><br><p style='text-align:right; font-family:serif; font-style:italic; color:#BFAF83;'>Edson Medeiros</p>", unsafe_allow_html=True)
