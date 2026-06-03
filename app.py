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

# --- 3. MOTOR COM LÓGICA DE DATA INFERIOR (MODELO ANEXO 2) ---
def realizar_auditoria(arquivo, rubricas_alvo):
    resultados = []
    cesto_acumulador = []
    last_known_date = None
    last_known_value = None
    
    with pdfplumber.open(arquivo) as pdf:
        for page in pdf.pages:
            texto = page.extract_text(x_tolerance=3, y_tolerance=3) # Reverte a tolerância Y para o padrão original
            if not texto: continue
            
            linhas = texto.split('\n')
            for linha in linhas:
                linha_up = linha.upper().strip()
                if not linha_up: continue

                # 1. Identifica Data e Valor
                current_match_data = re.search(r"(\d{2}/\d{2}/\d{2,4})", linha_up)
                current_match_valor = re.search(r"(\d{1,3}(?:\.\d{3})*,\d{2})(?!\s*%)", linha_up)

                # Atualiza last_known_date e last_known_value para a próxima iteração, se encontrados na linha atual
                if current_match_data:
                    last_known_date = current_match_data.group(1)
                if current_match_valor:
                    last_known_value = current_match_valor.group(1)
                
                # 2. Reset por Termos de Exclusão
                if re.search(TERMOS_EXCLUSAO, linha_up):
                    cesto_acumulador = [item for item in cesto_acumulador if item["VALOR"] != "PENDENTE"]
                    last_known_date = None # Reseta a data conhecida ao encontrar um termo de exclusão
                    last_known_value = None # Reseta o valor conhecido
                    continue 

                # 3. Busca Rubrica
                rubrica_detectada = None
                if "%" not in linha_up:
                    for nome in rubricas_alvo:
                        if re.search(RUBRICAS_MESTRE[nome], linha_up):
                            rubrica_detectada = nome
                            break
                
                # 4. Lógica de Captura (Acúmulo)
                if rubrica_detectada:
                    if rubrica_detectada == "CESTA":
                        # Lógica especial para CESTA: herda data e valor da linha anterior se não estiverem na linha atual
                        valor_para_rubrica = current_match_valor.group(1) if current_match_valor else last_known_value if last_known_value else "PENDENTE"
                        data_para_rubrica = current_match_data.group(1) if current_match_data else last_known_date if last_known_date else "PENDENTE"
                    else:
                        # Lógica padrão para outras rubricas: prioriza data/valor da linha atual
                        valor_para_rubrica = current_match_valor.group(1) if current_match_valor else "PENDENTE"
                        data_para_rubrica = current_match_data.group(1) if current_match_data else "PENDENTE"

                    cesto_acumulador.append({
                        "CATEGORIA": rubrica_detectada,
                        "VALOR": valor_para_rubrica,
                        "HISTÓRICO": linha_up[:80],
                        "DATA": data_para_rubrica
                    })
                    # Reseta last_known_date e last_known_value apenas se a rubrica encontrada não for CESTA
                    # Para CESTA, eles são consumidos na atribuição, mas podem ser úteis para a próxima linha se houver outra CESTA
                    if rubrica_detectada != "CESTA":
                        last_known_date = None
                        last_known_value = None
                
                elif current_match_valor and cesto_acumulador:
                    # Associa o valor à última rubrica pendente no cesto
                    if cesto_acumulador[-1]["VALOR"] == "PENDENTE":
                        cesto_acumulador[-1]["VALOR"] = current_match_valor.group(1)

                # 5. SELAGEM POR DATA INFERIOR (ANEXO 2)
                # Se uma data é encontrada, sela os itens acumulados com essa data.
                if current_match_data:
                    data_encontrada = current_match_data.group(1)
                    if cesto_acumulador:
                        for item in cesto_acumulador:
                            if item["VALOR"] != "PENDENTE" and item["DATA"] == "PENDENTE":
                                item["DATA"] = data_encontrada
                            resultados.append(item)
                        cesto_acumulador = []
                    # last_known_date e last_known_value são resetados após a selagem para evitar herança indevida para o próximo bloco de transações.

    return resultados

# --- 4. FUNÇÃO PARA GERAR PLANILHA DE CÁLCULOS (MODELO ANEXO 1, 3, 5) ---
def gerar_excel_calculos(df, rubrica_nome):
    df = df.copy()
    def fix_date(d):
        p = d.split('/')
        if len(p[2]) == 2: p[2] = "20" + p[2]
        return "/".join(p)
    
    df['DT'] = pd.to_datetime(df['DATA'].apply(fix_date), format='%d/%m/%Y')
    df['ANO'] = df['DT'].dt.year
    df['MES_NUM'] = df['DT'].dt.month
    
    # Agrupar e somar valores do mesmo mês/ano (Exemplo 05/2021)
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
    if not anos: anos = [datetime.now().year] # Fallback
    
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

    # Fórmulas: VALOR ANUAL (Soma da Coluna)
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

    # Fórmula: VALOR TOTAL (Soma dos Totais Anuais)
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
    
    # Fórmula: VALOR EM DOBRO (Total * 2)
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

st.sidebar.markdown("### 🔍 RUBRICAS DE AUDITORIA")
if 'sel_all' not in st.session_state: st.session_state.sel_all = True

col_b1, col_b2 = st.sidebar.columns(2)
if col_b1.button("Marcar Todas"): st.session_state.sel_all = True
if col_b2.button("Desmarcar Todas"): st.session_state.sel_all = False

selecionadas = []
for r in RUBRICAS_MESTRE.keys():
    if st.sidebar.checkbox(r, value=st.session_state.sel_all, key=f"check_{r}"):
        selecionadas.append(r)

upload = st.file_uploader("📂 ARRASTE O EXTRATO BANCÁRIO (PDF)", type=["pdf"])

if upload:
    with st.spinner("Analisando extratos e gerando tabelas de cálculos..."):
        dados = realizar_auditoria(upload, selecionadas)
        if dados:
            df = pd.DataFrame(dados)
            df['V_NUM'] = df['VALOR'].str.replace('.','', regex=False).str.replace(',','.', regex=False).astype(float)
            
            # Ordenação Cronológica Real
            def fix_date(d):
                p = d.split('/')
                if len(p[2]) == 2: p[2] = "20" + p[2]
                return "/".join(p)
            df['DT_O'] = pd.to_datetime(df['DATA'].apply(fix_date), format='%d/%m/%Y', errors='coerce')
            df = df.sort_values('DT_O', ascending=True)
            
            total_geral = df['V_NUM'].sum()
            c1, c2 = st.columns(2)
            with c1: st.markdown(f'<div class="metric-card"><h4>TOTAL RECUPERÁVEL</h4><h2 style="color:#BFAF83;">R$ {total_geral:,.2f}</h2></div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="metric-card"><h4>LANÇAMENTOS</h4><h2 style="color:#BFAF83;">{len(df)}</h2></div>', unsafe_allow_html=True)
            
            st.markdown('<h2 style="color:#BFAF83; text-align:center; margin-top:30px;">📥 Baixar Tabelas de Cálculos</h2>', unsafe_allow_html=True)
            st.write("Clique nos botões abaixo para baixar a planilha de cada rubrica com fórmulas automáticas.")
            
            cats = df['CATEGORIA'].unique()
            for cat in cats:
                df_cat = df[df['CATEGORIA'] == cat]
                excel_file = gerar_excel_calculos(df_cat, cat)
                st.download_button(
                    label=f"📊 Baixar Tabela: {cat}",
                    data=excel_file,
                    file_name=f"Tabela_Calculos_{cat.replace(' ', '_')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            
            st.markdown('<h3 style="color:#BFAF83; text-align:center; margin-top:30px;">📋 Lista Detalhada</h3>', unsafe_allow_html=True)
            st.dataframe(df[['DATA', 'CATEGORIA', 'VALOR', 'HISTÓRICO']], use_container_width=True)
        else:
            st.info("Nenhum débito encontrado com as rubricas selecionadas.")

st.markdown("<br><br><p style='text-align:right; font-family:serif; font-style:italic; color:#BFAF83;'>Edson Medeiros</p>", unsafe_allow_html=True)
