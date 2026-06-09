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
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;500;600&display=swap');

    /* ── Base ── */
    .stApp { background-color: #0E1117; color: #FFFFFF; font-family: 'Inter', sans-serif; }

    /* ── Títulos principais ── */
    .main-title { font-family: 'Playfair Display', serif; font-size: 3rem; color: #BFAF83; text-align: center; margin-bottom: 0; }
    .sub-title   { text-align: center; color: #64748B; letter-spacing: 2px; text-transform: uppercase; font-size: 0.9rem; margin-bottom: 40px; }

    /* ── Cards de métricas ── */
    .metric-card { background: rgba(255,255,255,0.05); border: 1px solid #BFAF83; border-radius: 10px; padding: 20px; text-align: center; }

    /* ── Sidebar: fundo e borda ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #13161F 0%, #0E1117 100%);
        border-right: 1px solid rgba(191,175,131,0.25);
    }
    [data-testid="stSidebar"] > div:first-child { padding-top: 1.5rem; }

    /* ── Título da sidebar ── */
    .sidebar-header {
        font-family: 'Playfair Display', serif;
        font-size: 1.05rem;
        color: #BFAF83;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        border-bottom: 1px solid rgba(191,175,131,0.3);
        padding-bottom: 10px;
        margin-bottom: 4px;
    }

    /* ── Contador de selecionadas ── */
    .rubrica-count {
        font-size: 0.72rem;
        color: #64748B;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-bottom: 12px;
    }

    /* ── Botões Marcar / Desmarcar ── */
    [data-testid="stSidebar"] .stButton > button {
        width: 100%;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        border-radius: 6px;
        padding: 5px 4px;
        transition: all 0.2s ease;
    }
    /* Botão "Marcar Todas" — dourado */
    [data-testid="stSidebar"] .stButton:nth-of-type(1) > button {
        background: rgba(191,175,131,0.12);
        border: 1px solid rgba(191,175,131,0.5);
        color: #BFAF83;
    }
    [data-testid="stSidebar"] .stButton:nth-of-type(1) > button:hover {
        background: rgba(191,175,131,0.25);
        border-color: #BFAF83;
    }
    /* Botão "Desmarcar Todas" — apagado */
    [data-testid="stSidebar"] .stButton:nth-of-type(2) > button {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.12);
        color: #64748B;
    }
    [data-testid="stSidebar"] .stButton:nth-of-type(2) > button:hover {
        background: rgba(255,255,255,0.08);
        border-color: rgba(255,255,255,0.25);
        color: #FFFFFF;
    }

    /* ── Checkboxes: label compacto ── */
    [data-testid="stSidebar"] .stCheckbox { margin: 0 !important; padding: 0 !important; }
    [data-testid="stSidebar"] .stCheckbox label {
        font-size: 0.80rem !important;
        font-weight: 500;
        color: #C8C4B8 !important;
        letter-spacing: 0.3px;
        padding: 3px 0 !important;
        line-height: 1.35 !important;
    }
    [data-testid="stSidebar"] .stCheckbox label:hover { color: #BFAF83 !important; }

    /* ── Checkbox tick dourado quando marcado ── */
    [data-testid="stSidebar"] input[type="checkbox"]:checked + div {
        background-color: #BFAF83 !important;
        border-color: #BFAF83 !important;
    }

    /* ── Linha divisória entre seções da sidebar ── */
    .sidebar-divider {
        border: none;
        border-top: 1px solid rgba(191,175,131,0.15);
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. RÚBRICAS ---
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

# --- 3. MOTOR — LÓGICA DATA INFERIOR ---
#
# COMO FUNCIONA O MODELO "DATA INFERIOR":
#
# No extrato Bradesco, existem dois formatos de linha:
#
#   FORMATO A — linha COM data ao lado da rubrica:
#     "15/01/2020  TARIFA BANCARIA  CESTA B.EXPRESSO4  21,60"
#     → rubrica e data estão juntas. A data pertence a esse lançamento.
#
#   FORMATO B — linha SEM data (rubrica "solta"):
#     "MORA CREDITO PESSOAL  115,62"
#     "ENCARGOS LIMITE DE CRED  19,31"
#     "08/02/2017  SAQUE DIN CORBAN CARTAO  ..."   ← próxima linha datada
#
#   No formato B, as rubricas acima não têm data própria.
#   A data que as referencia é a da PRÓXIMA linha que contiver uma data —
#   chamada aqui de "data inferior" pois aparece abaixo no extrato.
#
# SOLUÇÃO IMPLEMENTADA — dois cestos separados:
#
#   cesto_com_data   → itens capturados em linhas QUE JÁ TÊM data (formato A)
#                      são selados imediatamente com a data da própria linha.
#
#   cesto_sem_data   → itens capturados em linhas SEM data (formato B)
#                      ficam aguardando. Quando a próxima linha com data aparece,
#                      ela é usada para selar TODOS os itens pendentes do cesto_sem_data
#                      ANTES de processar o lançamento novo dessa linha datada.
#
# Assim, o motor lida corretamente com ambos os formatos no mesmo extrato.

def realizar_auditoria(arquivo, rubricas_alvo):
    resultados = []

    # Cesto para rubricas SEM data na linha (esperam a próxima data que aparecer)
    cesto_sem_data = []

    with pdfplumber.open(arquivo) as pdf:
        for page in pdf.pages:
            texto = page.extract_text(x_tolerance=3, y_tolerance=3)
            if not texto:
                continue

            linhas = texto.split('\n')
            for linha in linhas:
                linha_up = linha.upper().strip()
                if not linha_up:
                    continue

                # PASSO 1 — Detectar componentes da linha
                match_data  = re.search(r"(\d{2}/\d{2}/\d{2,4})", linha_up)
                match_valor = re.search(r"(\d{1,3}(?:\.\d{3})*,\d{2})(?!\s*%)", linha_up)
                tem_data    = match_data is not None
                tem_valor   = match_valor is not None

                # PASSO 2 — Termos de exclusão: descartar pendentes sem data e pular
                if re.search(TERMOS_EXCLUSAO, linha_up):
                    cesto_sem_data = [
                        item for item in cesto_sem_data
                        if item["VALOR"] != "PENDENTE"
                    ]
                    continue

                # PASSO 3 — Identificar rubrica (ignora linhas com %)
                rubrica_detectada = None
                if "%" not in linha_up:
                    for nome in rubricas_alvo:
                        if re.search(RUBRICAS_MESTRE[nome], linha_up):
                            rubrica_detectada = nome
                            break

                # PASSO 4 — SELAGEM DOS PENDENTES SEM DATA
                #
                # Se esta linha tem uma data, ela é a "data inferior" para todos
                # os itens do cesto_sem_data acumulados antes dela.
                # Selamos esses itens AGORA, antes de processar o lançamento atual.
                #
                # Isso garante que:
                #   - MORA e ENCARGOS (sem data) recebem a data do SAQUE logo abaixo (08/02/2017)
                #   - O próprio SAQUE (se for rubrica) ainda não entrou no cesto, então
                #     não recebe erroneamente a mesma data que os anteriores.
                if tem_data:
                    data_inferior = match_data.group(1)
                    for item in cesto_sem_data:
                        if item["VALOR"] != "PENDENTE":
                            item["DATA"] = data_inferior
                            resultados.append(item)
                    # Descarta pendentes sem valor que ficaram órfãos
                    cesto_sem_data = []

                # PASSO 5 — Processar o lançamento da linha atual
                if rubrica_detectada:
                    valor_na_linha = match_valor.group(1) if tem_valor else "PENDENTE"
                    novo_item = {
                        "CATEGORIA": rubrica_detectada,
                        "VALOR":     valor_na_linha,
                        "HISTÓRICO": linha_up[:80]
                    }

                    if tem_data:
                        # FORMATO A: data e rubrica na mesma linha → sela imediatamente
                        novo_item["DATA"] = match_data.group(1)
                        resultados.append(novo_item)
                    else:
                        # FORMATO B: sem data → acumula no cesto para receber data inferior
                        cesto_sem_data.append(novo_item)

                elif tem_valor and not tem_data and cesto_sem_data:
                    # Linha de complemento (valor na linha seguinte à rubrica sem data)
                    if cesto_sem_data[-1]["VALOR"] == "PENDENTE":
                        cesto_sem_data[-1]["VALOR"] = match_valor.group(1)

    # PASSO 6 — Flush final: itens que sobraram no cesto sem data ao fim do PDF
    for item in cesto_sem_data:
        if item["VALOR"] != "PENDENTE":
            item.setdefault("DATA", "00/00/0000")
            resultados.append(item)

    return resultados


# --- 4. GERAÇÃO DE PLANILHA ---
def fix_date(d):
    p = d.split('/')
    if len(p) == 3 and len(p[2]) == 2:
        p[2] = "20" + p[2]
    return "/".join(p)

def gerar_excel_calculos(df, rubrica_nome):
    df = df.copy()
    df['DT']      = pd.to_datetime(df['DATA'].apply(fix_date), format='%d/%m/%Y', errors='coerce')
    df['ANO']     = df['DT'].dt.year
    df['MES_NUM'] = df['DT'].dt.month

    agrupado = df.groupby(['ANO', 'MES_NUM'])['V_NUM'].sum().reset_index()

    wb = Workbook()
    ws = wb.active
    ws.title = "Tabela de Cálculos"

    font_header  = Font(bold=True, size=11)
    font_title   = Font(bold=True, size=12)
    fill_blue    = PatternFill(start_color="BDD7EE", end_color="BDD7EE", fill_type="solid")
    fill_peach   = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid")
    border       = Border(left=Side(style='thin'), right=Side(style='thin'),
                          top=Side(style='thin'),  bottom=Side(style='thin'))
    align_center = Alignment(horizontal='center', vertical='center')

    ws.merge_cells('A1:E1')
    ws['A1']           = f"VALORES DESCONTADOS INDEVIDAMENTE - \"{rubrica_nome}\""
    ws['A1'].font      = font_title
    ws['A1'].fill      = fill_blue
    ws['A1'].alignment = align_center

    meses_nomes = ["JANEIRO","FEVEREIRO","MARÇO","ABRIL","MAIO","JUNHO",
                   "JULHO","AGOSTO","SETEMBRO","OUTUBRO","NOVEMBRO","DEZEMBRO"]

    ws['A2']           = "MESES"
    ws['A2'].font      = font_header
    ws['A2'].alignment = align_center

    anos = sorted(agrupado['ANO'].dropna().astype(int).unique())
    if not anos:
        anos = [datetime.now().year]

    for idx, ano in enumerate(anos):
        col = idx + 2
        ws.cell(row=2, column=col, value=ano).font      = font_header
        ws.cell(row=2, column=col).alignment             = align_center
        ws.cell(row=2, column=col).fill                  = fill_blue

    for m_idx, mes in enumerate(meses_nomes):
        row = m_idx + 3
        ws.cell(row=row, column=1, value=mes).font = font_header
        ws.cell(row=row, column=1).fill            = fill_blue

        for a_idx, ano in enumerate(anos):
            col = a_idx + 2
            val = agrupado[
                (agrupado['ANO'] == ano) & (agrupado['MES_NUM'] == m_idx + 1)
            ]['V_NUM'].sum()
            if val > 0:
                cell = ws.cell(row=row, column=col, value=val)
                cell.number_format = '"R$ " #,##0.00'
            ws.cell(row=row, column=col).fill   = fill_peach
            ws.cell(row=row, column=col).border = border

    row_anual = 15
    ws.cell(row=row_anual, column=1, value="VALOR ANUAL:").font = font_header
    ws.cell(row=row_anual, column=1).fill = fill_blue

    for idx, ano in enumerate(anos):
        col        = idx + 2
        col_letter = get_column_letter(col)
        formula    = f"=SUM({col_letter}3:{col_letter}14)"
        cell       = ws.cell(row=row_anual, column=col, value=formula)
        cell.number_format = '"R$ " #,##0.00'
        cell.font   = font_header
        cell.fill   = fill_peach
        cell.border = border

    row_total = 16
    ws.cell(row=row_total, column=1, value="VALOR TOTAL:").font = font_header
    ws.cell(row=row_total, column=1).fill = fill_blue

    last_col_letter = get_column_letter(len(anos) + 1)
    formula_total   = f"=SUM(B{row_anual}:{last_col_letter}{row_anual})"
    ws.merge_cells(start_row=row_total, start_column=2,
                   end_row=row_total, end_column=len(anos)+1)
    cell_total                = ws.cell(row=row_total, column=2, value=formula_total)
    cell_total.number_format  = '"R$ " #,##0.00'
    cell_total.font           = font_header
    cell_total.alignment      = Alignment(horizontal='right')

    row_dobro = 17
    ws.merge_cells(start_row=row_dobro, start_column=1,
                   end_row=row_dobro+1, end_column=1)
    ws.cell(row=row_dobro, column=1, value="VALOR EM DOBRO ART. 42 DO CDC").font = font_header
    ws.cell(row=row_dobro, column=1).alignment = Alignment(
        wrap_text=True, horizontal='center', vertical='center')
    ws.cell(row=row_dobro, column=1).fill = fill_blue

    ws.merge_cells(start_row=row_dobro, start_column=2,
                   end_row=row_dobro+1, end_column=len(anos)+1)
    formula_dobro              = f"=B{row_total}*2"
    cell_dobro                 = ws.cell(row=row_dobro, column=2, value=formula_dobro)
    cell_dobro.number_format   = '"R$ " #,##0.00'
    cell_dobro.font            = font_header
    cell_dobro.alignment       = Alignment(horizontal='right', vertical='center')
    cell_dobro.fill            = fill_peach

    ws.column_dimensions['A'].width = 25
    for i in range(2, len(anos) + 2):
        ws.column_dimensions[get_column_letter(i)].width = 15

    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()


# --- 5. DASHBOARD ---
st.markdown('<h1 class="main-title">Consultoria de Ativos</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Auditoria Técnica Especializada - Edson Medeiros</p>', unsafe_allow_html=True)

# ── SIDEBAR: painel de rubricas ──────────────────────────────────────────────

# Estado inicial: todas marcadas
if 'sel_all' not in st.session_state:
    st.session_state.sel_all = True

# Inicializa o estado individual de cada rubrica (na primeira execução)
for r in RUBRICAS_MESTRE.keys():
    key = f"check_{r}"
    if key not in st.session_state:
        st.session_state[key] = True

# Cabeçalho
st.sidebar.markdown('<div class="sidebar-header">⚖ Rubricas de Auditoria</div>', unsafe_allow_html=True)

# Botões Marcar / Desmarcar — aplicam imediatamente o estado individual
col_b1, col_b2 = st.sidebar.columns(2)

if col_b1.button("✦ Marcar Todas", key="btn_marcar"):
    for r in RUBRICAS_MESTRE.keys():
        st.session_state[f"check_{r}"] = True

if col_b2.button("✕ Desmarcar", key="btn_desmarcar"):
    for r in RUBRICAS_MESTRE.keys():
        st.session_state[f"check_{r}"] = False

st.sidebar.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)

# Lista de checkboxes — cada um com seu estado individual no session_state
selecionadas = []
for r in RUBRICAS_MESTRE.keys():
    key = f"check_{r}"
    marcado = st.sidebar.checkbox(r, value=st.session_state[key], key=key)
    if marcado:
        selecionadas.append(r)

# Contador de selecionadas
st.sidebar.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)
total_r   = len(RUBRICAS_MESTRE)
sel_count = len(selecionadas)
cor_count = "#BFAF83" if sel_count == total_r else ("#E57373" if sel_count == 0 else "#81C784")
st.sidebar.markdown(
    f'<div class="rubrica-count" style="color:{cor_count};">'
    f'● {sel_count} de {total_r} rubricas ativas</div>',
    unsafe_allow_html=True
)

upload = st.file_uploader("📂 ARRASTE O EXTRATO BANCÁRIO (PDF)", type=["pdf"])

if upload:
    with st.spinner("Analisando extratos e gerando tabelas de cálculos..."):
        dados = realizar_auditoria(upload, selecionadas)
        if dados:
            df = pd.DataFrame(dados)
            df['V_NUM'] = (df['VALOR']
                           .str.replace('.', '', regex=False)
                           .str.replace(',', '.', regex=False)
                           .astype(float))

            df['DT_O'] = pd.to_datetime(
                df['DATA'].apply(fix_date), format='%d/%m/%Y', errors='coerce'
            )
            df = df.sort_values('DT_O', ascending=True)

            total_geral = df['V_NUM'].sum()
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(
                    f'<div class="metric-card"><h4>TOTAL RECUPERÁVEL</h4>'
                    f'<h2 style="color:#BFAF83;">R$ {total_geral:,.2f}</h2></div>',
                    unsafe_allow_html=True
                )
            with c2:
                st.markdown(
                    f'<div class="metric-card"><h4>LANÇAMENTOS</h4>'
                    f'<h2 style="color:#BFAF83;">{len(df)}</h2></div>',
                    unsafe_allow_html=True
                )

            st.markdown(
                '<h2 style="color:#BFAF83; text-align:center; margin-top:30px;">📥 Baixar Tabelas de Cálculos</h2>',
                unsafe_allow_html=True
            )
            st.write("Clique nos botões abaixo para baixar a planilha de cada rubrica com fórmulas automáticas.")

            cats = df['CATEGORIA'].unique()
            for cat in cats:
                df_cat     = df[df['CATEGORIA'] == cat]
                excel_file = gerar_excel_calculos(df_cat, cat)
                st.download_button(
                    label=f"📊 Baixar Tabela: {cat}",
                    data=excel_file,
                    file_name=f"Tabela_Calculos_{cat.replace(' ', '_')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            st.markdown(
                '<h3 style="color:#BFAF83; text-align:center; margin-top:30px;">📋 Lista Detalhada</h3>',
                unsafe_allow_html=True
            )
            st.dataframe(
                df[['DATA', 'CATEGORIA', 'VALOR', 'HISTÓRICO']],
                use_container_width=True
            )
        else:
            st.info("Nenhum débito encontrado com as rubricas selecionadas.")

st.markdown(
    "<br><br><p style='text-align:right; font-family:serif; font-style:italic; color:#BFAF83;'>Edson Medeiros</p>",
    unsafe_allow_html=True
)
