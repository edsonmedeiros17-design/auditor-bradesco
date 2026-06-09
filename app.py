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
    # "TARIFA BANCARIA / CESTA B.EXPRESSO4" — o nome real no extrato está na sublinha
    "CESTA": r"\bCESTA\b",

    # "PACOTE DE SERVICOS" ou "PACOTE SERVICOS"
    "PACOTE": r"\bPACOTE\b",

    # "MORA DE OPERACAO" / "MORA OPERACAO"
    "MORA DE OPERAÇÃO": r"MORA\s+DE\s+OPERA[CÇ]AO|MORA\s+OPERA[CÇ]AO\b",

    # "MORA CREDITO PESSOAL" / "MORA CRED PESS" / "MORA CP"
    "MORA CREDITO PESSOAL": r"MORA\s+CREDITO\s+PESSOAL|MORA\s+CRED\s+PESS|MORA\s+CP\b",

    # "MORA OPERACAO DE CREDITO" / "MORA OPER CRED"
    "MORA OPERACAO DE CREDITO": r"MORA\s+OPERA[CÇ]AO\s+DE\s+CREDITO|MORA\s+OPER\s+CRED",

    # "BX" isolado — word boundary para não pegar "BXA" ou "COBRA"
    "BX": r"\bBX\b",

    # "PARCELA CREDITO PESSOAL" / "PARC CRED PESS" / "PARCELA CP"
    "PARCELA CREDITO PESSOAL": r"PARCELA\s+CREDITO\s+PESSOAL|PARC\s+CRED\s+PESS|PARCELA\s+CP\b",

    # "GASTOS CARTAO DE CREDITO" / "CARTAO DE CREDITO" / "FATURA CARTAO"
    # NÃO inclui "CARTAO CREDITO ANUIDADE" (já capturado em ANUIDADE)
    "GASTOS CARTAO DE CREDITO": r"GASTOS\s+CART[AÃ]O|FATURA\s+CART[AÃ]O|CART[AÃ]O\s+DE\s+CREDITO(?!\s+ANUIDADE)",

    # "SEGURO" / "SEG " / "SEGURADORA" — word boundary para não pegar "SAQUE"
    "SEGURO": r"\bSEGURO\b|\bSEGURADORA\b|\bSEG\s",

    # "ADIANT" / "ADIANTAMENTO"
    "ADIANT": r"\bADIANT|\bADIANTAMENTO\b",

    # "APLICACAO" / "APLIC" isolado
    "APLIC": r"\bAPLICA[CÇ]AO\b|\bAPLIC\b",

    # "ENCARGOS" / "ENCARGO" / "ENCARGOS LIMITE DE CRED" / "IOF" não — só encargo mesmo
    "ENCARGOS": r"\bENCARGOS?\b|\bENC\s+LIMITE\b|\bLIMITE\s+DE\s+CRED\b",

    # "CARTAO CREDITO ANUIDADE" / "ANUIDADE" — verificado ANTES de GASTOS CARTAO
    "ANUIDADE": r"\bANUIDADE\b|CART[AÃ]O\s+CREDITO\s+ANUIDADE",

    # "OPERACOES VENCIDAS" / "OPERAÇÕES VENCIDAS"
    "OPERACOES VENCIDAS": r"OPERA[CÇ][OÕ]ES\s+VENCIDAS",

    # "DIV. EM ATRASO" / "DIVIDA EM ATRASO"
    "DIV. EM ATRASO": r"DIV\.?\s+EM\s+ATRASO|DIVIDA\s+EM\s+ATRASO",
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

def _extrair_debito(texto_up):
    """Penúltimo valor numérico = débito (último = saldo)."""
    vals = re.findall(r'\d{1,3}(?:\.\d{3})*,\d{2}(?!\s*%)', texto_up)
    if not vals: return None
    return vals[-2] if len(vals) >= 2 else vals[0]

def _detectar_rubrica(texto_up, rubricas_alvo):
    """Retorna o nome da rubrica detectada, ou None."""
    if "%" in texto_up: return None
    for nome in rubricas_alvo:
        if re.search(RUBRICAS_MESTRE[nome], texto_up): return nome
    return None

CABECALHOS_PREFIXOS = [
    'BRADESCO CELULAR', 'DATA:', 'NOME:', 'EXTRATO DE:',
    'DATA HISTÓRICO', 'DATA HISTORICO', 'FOLHA:', 'TOTAL'
]

def _eh_cabecalho(texto_up):
    return any(texto_up.startswith(p.upper()) for p in CABECALHOS_PREFIXOS)

def _agrupar_linhas_por_y(words, tolerancia_y=5):
    """Agrupa palavras em linhas pela proximidade vertical (Y)."""
    if not words: return []
    linhas = [[words[0]]]
    for w in words[1:]:
        if abs(w['top'] - linhas[-1][0]['top']) <= tolerancia_y:
            linhas[-1].append(w)
        else:
            linhas.append([w])
    return linhas

# ── MOTOR POR COORDENADAS ─────────────────────────────────────────────────────
#
# PRINCÍPIO FUNDAMENTAL do extrato Bradesco:
#
# O extrato tem uma coluna "Data" à esquerda (X < 80px). Uma data nessa coluna
# cobre TODOS os lançamentos abaixo até a próxima data na coluna Data.
# Ou seja: lançamentos sem data na coluna Data pertencem ao mesmo dia da
# última data que apareceu nessa coluna.
#
# Exemplo visual (pág7, jan/2021):
#   Coluna Data    Coluna Histórico          Débito
#   29/01/2021     TRANSF SALDO C/SAL P/CC
#                  MORA CREDITO PESSOAL      289,14   ← sem data = 29/01/2021
#                  ENCARGOS LIMITE DE CRED     6,81   ← sem data = 29/01/2021
#                  TARIFA BANCARIA / CESTA    27,70   ← sem data = 29/01/2021
#   01/02/2021     SAQUE DIN CORBAN           45,00
#
# O motor por texto tinha dificuldade em distinguir qual data pertencia a qual
# lançamento. O motor por coordenadas resolve isso definitivamente ao usar
# a posição X para identificar a coluna Data e a posição Y para agrupar linhas.
#
# Busca de valor (3 prioridades):
#   1. Própria linha da rubrica
#   2. Linha anterior (TIPO C — CESTA sublinha de TARIFA BANCARIA)
#   3. Próximas linhas (TIPO B — ENCARGOS/PARCELA com dados abaixo)

def realizar_auditoria(arquivo, rubricas_alvo):
    resultados = []

    with pdfplumber.open(arquivo) as pdf:
        # Variáveis compartilhadas entre páginas (pendentes podem atravessar fim de página)
        data_atual = None
        apos_excl  = False
        pendentes  = []

        for page in pdf.pages:
            words = page.extract_words(x_tolerance=3, y_tolerance=3)
            if not words:
                continue

            # Agrupar palavras em linhas por proximidade Y
            grupos = _agrupar_linhas_por_y(words, tolerancia_y=5)

            # Construir lista de linhas com metadados
            linhas = []
            for grupo in grupos:
                grupo_s = sorted(grupo, key=lambda w: w['x0'])
                texto_up = ' '.join(w['text'] for w in grupo_s).upper().strip()

                # Detecta data na coluna Data (X < 80px)
                data_col = None
                for w in grupo_s:
                    if w['x0'] < 80:
                        m = re.search(r'(\d{2}/\d{2}/\d{2,4})', w['text'])
                        if m:
                            data_col = m.group(1)
                            break

                linhas.append({
                    'texto':    texto_up,
                    'data_col': data_col,
                    'valor':    _extrair_debito(texto_up),
                })

            # ── RASTREADOR DE DATA — LÓGICA DATA INFERIOR ────────────────────────
            # REGRA FUNDAMENTAL do extrato Bradesco:
            # A coluna "Data" (X < 80px) só aparece quando muda o dia.
            # Lançamentos sem data na coluna pertencem ao mesmo dia da última data vista.
            #
            # PORÉM: linhas de EXCLUSÃO (TRANSF/SALDO) com data na coluna NÃO transferem
            # essa data para os lançamentos seguintes. Os lançamentos sem data que aparecem
            # APÓS um bloco de exclusão pertencem ao grupo do dia seguinte (data inferior).
            #
            # Exemplo pág7:
            #   29/01/2021  TRANSF SALDO ...   ← exclusão, sua data é 29/01
            #               MORA CREDITO       ← sem data na coluna → data inferior
            #               ENCARGOS LIMITE    ← sem data na coluna → data inferior
            #               TARIFA/CESTA       ← sem data na coluna → data inferior
            #   01/02/2021  SAQUE DIN ...      ← ESTA é a data inferior que sela o grupo
            #
            # Solução: data_atual só é atualizada por linhas NÃO-exclusão.
            # Quando a linha atual é de exclusão, sua data é registrada em
            # data_excl_pendente mas NÃO altera data_atual.
            # Rubricas que ficam "penduradas" (sem data_atual válida) recebem
            # a data da próxima linha datada não-exclusão (buscada por lookahead).

            # ── RASTREADOR DE DATA — LÓGICA DATA INFERIOR ────────────────────────
            # REGRA DO EXTRATO BRADESCO:
            # A coluna "Data" (X < 80px) aparece na linha do primeiro lançamento
            # de cada dia. Todos os lançamentos abaixo SEM data na coluna pertencem
            # ao mesmo dia — até aparecer uma nova data na coluna.
            #
            # EXCEÇÃO CRÍTICA — TRANSF SALDO (lançamento de exclusão):
            # Quando TRANSF aparece com data na coluna, os lançamentos seguintes
            # SEM data na coluna (MORA, ENCARGOS, CESTA, etc.) NÃO pertencem à
            # data do TRANSF. Eles pertencem ao dia cujo lançamento aparece logo
            # ABAIXO, na próxima linha COM data na coluna — a "data inferior".
            #
            # Exemplo pág7:
            #   29/01/2021  TRANSF SALDO → SUA data é 29/01 (exclusão, ignorada)
            #               MORA CREDITO → sem data → aguarda data inferior
            #               ENCARGOS     → sem data → aguarda data inferior
            #               CESTA        → sem data → aguarda data inferior
            #   01/02/2021  SAQUE DIN    → esta é a data inferior → sela as 3 acima
            #
            # IMPLEMENTAÇÃO:
            # - data_atual: rastreia a data do grupo de lançamentos em andamento
            # - apos_excl: True quando acabou de passar por uma exclusão COM DATA
            #   (indica que os próximos sem data devem aguardar a data inferior)
            # - pendentes: rubricas que aguardam data inferior
            #
            # Quando apos_excl=True e aparece nova linha com data na coluna (não exclusão),
            # essa data é a "data inferior" → sela os pendentes E vira a nova data_atual.

            # data_atual, apos_excl, pendentes são compartilhados entre páginas

            for idx, linha in enumerate(linhas):
                txt = linha['texto']

                eh_excl = bool(re.search(TERMOS_EXCLUSAO, txt))

                if linha['data_col']:
                    if eh_excl:
                        # Exclusão com data: marca que os próximos sem data
                        # devem aguardar a data inferior, não herdar data_atual
                        apos_excl = True
                        # data_atual NÃO é alterada — permanece do lançamento anterior
                    else:
                        # Lançamento normal com data na coluna
                        data_atual = linha['data_col']
                        apos_excl  = False
                        # Sela pendentes que aguardavam esta data inferior
                        if pendentes:
                            for p in pendentes:
                                p['DATA'] = data_atual
                                resultados.append(p)
                            pendentes = []

                # Pula cabeçalhos, linhas vazias, subtítulos com %, exclusões
                if not txt or _eh_cabecalho(txt):
                    continue
                if "%" in txt and not linha['data_col']:
                    continue
                if eh_excl:
                    continue

                rubrica = _detectar_rubrica(txt, rubricas_alvo)
                if not rubrica:
                    continue

                # Busca de valor (3 prioridades)
                valor_final = linha['valor']

                # Prioridade 2: linha anterior (TIPO C — CESTA sublinha de TARIFA)
                if not valor_final and idx > 0:
                    ant      = linhas[idx - 1]
                    rub_ant  = _detectar_rubrica(ant['texto'], rubricas_alvo)
                    excl_ant = bool(re.search(TERMOS_EXCLUSAO, ant['texto']))
                    if ant['valor'] and not rub_ant and not excl_ant:
                        valor_final = ant['valor']

                # Prioridade 3: próximas linhas (TIPO B — ENCARGOS, PARCELA)
                if not valor_final:
                    for k in range(idx + 1, min(len(linhas), idx + 4)):
                        prox = linhas[k]
                        if re.search(TERMOS_EXCLUSAO, prox['texto']): break
                        if _detectar_rubrica(prox['texto'], rubricas_alvo): break
                        if "%" in prox['texto'] and not prox['data_col']: continue
                        if prox['valor']:
                            valor_final = prox['valor']
                            break

                if not valor_final:
                    continue

                # Determinar data do registro:
                # Se apos_excl=True (viemos de um bloco TRANSF+data): pendentes
                # Se apos_excl=False e data_atual disponível: usa data_atual direto
                if apos_excl:
                    # Aguarda a data inferior (próxima linha normal com data na coluna)
                    pendentes.append({
                        'DATA':      None,
                        'CATEGORIA': rubrica,
                        'VALOR':     valor_final,
                        'HISTÓRICO': txt[:80],
                    })
                elif data_atual:
                    resultados.append({
                        'DATA':      data_atual,
                        'CATEGORIA': rubrica,
                        'VALOR':     valor_final,
                        'HISTÓRICO': txt[:80],
                    })

            # Pendentes ao fim de página: mantém para a próxima página
            # (a data inferior pode estar na primeira linha da página seguinte)

    # Flush final: pendentes que sobraram após todas as páginas
    if pendentes:
        for p in pendentes:
            if p['DATA'] is None:
                p['DATA'] = '00/00/0000'
            resultados.append(p)

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
