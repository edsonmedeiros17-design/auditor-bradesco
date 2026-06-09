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

def _extrair_valor_debito(linha_up):
    """Extrai o valor de débito/crédito da linha, ignorando o saldo.

    O extrato Bradesco tem sempre duas colunas numéricas no final:
      ...  DÉBITO  SALDO
    Pegamos o penúltimo valor (débito). Se houver apenas um, é o débito.
    Valores seguidos de % são ignorados (taxas de juros, não montantes).
    """
    todos = re.findall(r'\d{1,3}(?:\.\d{3})*,\d{2}(?!\s*%)', linha_up)
    if not todos:
        return None
    return todos[-2] if len(todos) >= 2 else todos[0]


def _extrair_perto_da_rubrica(linha_up, pos_rubrica):
    """Extrai a DATA e o VALOR pertencentes à rubrica em linhas FUNDIDAS.

    PROBLEMA QUE RESOLVE:
    Às vezes o pdfplumber junta dois lançamentos numa única linha de texto:
      "03/01/2020 IOF S/ UTILIZACAO LIMITE 8118726 0,11 11,38
       08/01/2020 ENCARGOS LIMITE DE CRED 8118726 0,95 12,33"
    Pegar a PRIMEIRA data/valor da linha daria 03/01/2020 e 0,11 (do IOF),
    associando-os erroneamente ao ENCARGOS.

    SOLUÇÃO:
    A data e o valor corretos do lançamento da rubrica são os que aparecem
    PRÓXIMOS à posição da rubrica no texto:
      - DATA  → a última data que aparece ANTES (à esquerda) do nome da rubrica.
                No exemplo, 08/01/2020 vem logo antes de "ENCARGOS".
      - VALOR → o primeiro par de valores que aparece DEPOIS (à direita) da rubrica.
                No exemplo, 0,95 / 12,33 vêm depois de "ENCARGOS LIMITE DE CRED";
                pega-se o penúltimo (débito) = 0,95.

    Retorna (data, valor). Cada um pode ser None se não houver candidato no lado certo.
    """
    # ── DATA: última ocorrência à ESQUERDA da rubrica ───────────────────────
    data_final = None
    for m in re.finditer(r"\d{2}/\d{2}/\d{2,4}", linha_up):
        if m.start() < pos_rubrica:
            data_final = m.group(0)   # continua atualizando → fica com a mais próxima à esquerda
        else:
            break

    # ── VALOR: valores à DIREITA da rubrica ─────────────────────────────────
    trecho_dir = linha_up[pos_rubrica:]
    vals_dir = re.findall(r'\d{1,3}(?:\.\d{3})*,\d{2}(?!\s*%)', trecho_dir)
    if vals_dir:
        # penúltimo = débito (último é saldo); se só houver um, é o débito
        valor_final = vals_dir[-2] if len(vals_dir) >= 2 else vals_dir[0]
    else:
        valor_final = None

    return data_final, valor_final


def realizar_auditoria(arquivo, rubricas_alvo):
    resultados    = []
    cesto_sem_data = []

    # ── Memória de contexto ────────────────────────────────────────────────────
    # Mantém informações das últimas linhas para lidar com os vários formatos
    # de quebra de linha que o pdfplumber produz:
    #
    #   CENÁRIO 1 — data isolada / rubrica+valor / subtítulo(%)
    #     "08/01/2020"
    #     "ENCARGOS LIMITE DE CRED  0,95"
    #     "ENCARGO - 08,00%"
    #     → rubrica herda data da linha anterior
    #
    #   CENÁRIO 2 — tudo junto / subtítulo(%)           [já funcionava]
    #     "08/01/2020  ENCARGOS LIMITE DE CRED  0,95"
    #     "ENCARGO - 08,00%"
    #
    #   CENÁRIO 3 — data+rubrica / valor separado / subtítulo(%)
    #     "08/01/2020  ENCARGOS LIMITE DE CRED"
    #     "0,95  12,33"
    #     "ENCARGO - 08,00%"
    #     → rubrica fica PENDENTE; valor da linha seguinte (sem data, sem rubrica) a preenche
    #       antes que o subtítulo(%) seja descartado
    #
    #   CENÁRIO 4 — rubrica+valor sem data / subtítulo / data inferior [já funcionava]
    #     "ENCARGOS LIMITE DE CRED  19,31"
    #     "ENCARGO - 14,31%"
    #     "08/02/2017  SAQUE..."
    #
    #   CENÁRIO 5 — rubrica sem data/valor / subtítulo / valor / data inferior
    #     "ENCARGOS LIMITE DE CRED"
    #     "ENCARGO - 14,31%"
    #     "19,31  132,13"
    #     "08/02/2017  SAQUE..."
    #     → subtítulo(%) é ignorado mas NÃO zera o contexto da rubrica pendente;
    #       valor da linha seguinte ainda preenche o último item do cesto
    #
    #   CENÁRIO 6 — CESTA como sublinha (herda data+valor da linha acima) [já funcionava]
    #     "15/01/2020  TARIFA BANCARIA  21,60"
    #     "CESTA B.EXPRESSO4"
    #
    #   CENÁRIO 7 — rubrica+data+valor / subtítulo de texto (sem %)   [já funcionava]
    #     "20/01/2020  PARCELA CREDITO PESSOAL  385,50"
    #     "CONTR 381101278 PARC 004/005"
    #
    # Campos do contexto:
    #   data_ctx        → última data vista (None se ainda não apareceu)
    #   valor_ctx       → último valor visto em linha SEM rubrica capturada
    #   rubrica_pendente→ True se a última rubrica ainda não tem valor confirmado
    #   era_exclusao    → True se a última linha relevante era termo de exclusão
    ctx = {
        "data_ctx":          None,
        "valor_ctx":         None,
        "rubrica_pendente":  False,
        "era_exclusao":      False,
        "dist_data":         999,   # linhas processadas desde a última data vista
        "dist_valor":        999,   # linhas processadas desde o último valor visto
    }

    with pdfplumber.open(arquivo) as pdf:
        for page in pdf.pages:
            texto = page.extract_text(x_tolerance=3, y_tolerance=3)
            if not texto:
                continue

            for linha in texto.split('\n'):
                linha_up = linha.upper().strip()
                if not linha_up:
                    continue

                # ── 1. Detectar componentes da linha ─────────────────────────
                match_data  = re.search(r"(\d{2}/\d{2}/\d{2,4})", linha_up)
                valor_linha = _extrair_valor_debito(linha_up)   # penúltimo valor = débito (não saldo)
                tem_data    = match_data   is not None
                tem_valor   = valor_linha  is not None
                tem_pct     = "%" in linha_up

                # ── 2. Linha de subtítulo com % ───────────────────────────────
                # Descarta a linha mas PRESERVA o contexto intacto.
                # Isso permite que o valor da linha seguinte ainda alcance
                # uma rubrica pendente (Cenário 5).
                if tem_pct and not tem_data:
                    continue

                # ── 3. Termos de exclusão ────────────────────────────────────
                if re.search(TERMOS_EXCLUSAO, linha_up):
                    cesto_sem_data = [i for i in cesto_sem_data if i["VALOR"] != "PENDENTE"]
                    ctx = {"data_ctx": None, "valor_ctx": None,
                           "rubrica_pendente": False, "era_exclusao": True,
                           "dist_data": 999, "dist_valor": 999}
                    continue

                # ── 4. Identificar rubrica (linhas sem %) ────────────────────
                rubrica_detectada = None
                pos_rubrica       = None
                for nome in rubricas_alvo:
                    m_rub = re.search(RUBRICAS_MESTRE[nome], linha_up)
                    if m_rub:
                        rubrica_detectada = nome
                        pos_rubrica       = m_rub.start()
                        break

                # ── 5. Selar cesto_sem_data com data inferior ─────────────────
                # A data desta linha é a referência para tudo que veio antes sem data.
                # Selamos ANTES de processar o lançamento atual.
                if tem_data:
                    data_inferior = match_data.group(1)
                    prontos = [i for i in cesto_sem_data if i["VALOR"] != "PENDENTE"]
                    for item in prontos:
                        item["DATA"] = data_inferior
                    resultados.extend(prontos)
                    # Mantém apenas os ainda pendentes (aguardam valor)
                    cesto_sem_data = [i for i in cesto_sem_data if i["VALOR"] == "PENDENTE"]

                # ── 6. Processar rubrica encontrada ──────────────────────────
                if rubrica_detectada:

                    # EXTRACAO POSICIONAL (linhas fundidas):
                    # Pega a data a esquerda da rubrica e o valor a direita dela,
                    # evitando capturar a data/valor de um lancamento vizinho que
                    # o pdfplumber juntou na mesma linha (ex.: IOF + ENCARGOS).
                    data_perto, valor_perto = _extrair_perto_da_rubrica(linha_up, pos_rubrica)

                    # Valor: posicional (a direita da rubrica) -> valor da linha -> contexto
                    if valor_perto is not None:
                        valor_final = valor_perto
                    elif tem_valor:
                        valor_final = valor_linha
                    elif ctx["valor_ctx"] is not None and not ctx["rubrica_pendente"] and not ctx["era_exclusao"]:
                        valor_final = ctx["valor_ctx"]
                    else:
                        valor_final = "PENDENTE"

                    # Data: regras em ordem de prioridade.
                    #  (a) linha fundida (2+ datas): usa a data a esquerda da rubrica.
                    #  (b) linha com uma data propria: usa essa data.
                    #  (c) sublinha de descricao (ex.: CESTA): herda data E valor da
                    #      linha imediatamente acima. So vale quando a rubrica NAO tem
                    #      valor proprio (valor tambem foi herdado) — sinal de sublinha.
                    #  (d) caso contrario: sem data -> vai ao cesto e recebe a data inferior
                    #      (ex.: MORA/ENCARGOS soltos com valor proprio mas sem data).
                    n_datas       = len(re.findall(r"\d{2}/\d{2}/\d{2,4}", linha_up))
                    valor_herdado = (valor_perto is None) and (not tem_valor)
                    if tem_data and n_datas > 1 and data_perto is not None:
                        data_final = data_perto                       # (a)
                    elif tem_data:
                        data_final = match_data.group(1)              # (b)
                    elif (valor_herdado and ctx["data_ctx"] is not None
                          and ctx["dist_data"] == 0 and not ctx["era_exclusao"]):
                        data_final = ctx["data_ctx"]                  # (c) sublinha
                    else:
                        data_final = None                             # (d) data inferior

                    novo_item = {
                        "CATEGORIA": rubrica_detectada,
                        "VALOR":     valor_final,
                        "HISTÓRICO": linha_up[:80],
                    }

                    if data_final:
                        novo_item["DATA"] = data_final
                        if valor_final == "PENDENTE":
                            # C3: tem data mas valor ainda não chegou.
                            # Guarda no cesto para receber valor da próxima linha.
                            # O bloco 7a detecta que já tem DATA e promove para resultados.
                            cesto_sem_data.append(novo_item)
                        else:
                            resultados.append(novo_item)
                    else:
                        cesto_sem_data.append(novo_item)

                    # Atualiza contexto: rubrica consumida, marca se ficou pendente.
                    # dist_data/dist_valor sobem para 999 pois o dado foi consumido
                    # pela rubrica e nao deve ser herdado pela proxima linha por adjacencia.
                    ctx = {
                        "data_ctx":         match_data.group(1)  if tem_data  else ctx["data_ctx"],
                        "valor_ctx":        None,   # valor foi consumido pela rubrica
                        "rubrica_pendente": valor_final == "PENDENTE",
                        "era_exclusao":     False,
                        "dist_data":        0 if tem_data else 999,
                        "dist_valor":       999,
                    }

                else:
                    # ── 7. Linha sem rubrica ──────────────────────────────────

                    # 7a. Valor complementar: preenche o último item PENDENTE do cesto,
                    #     seja ele sem data (C2/C4) ou com data já definida (C3).
                    #     Quando o item já tem DATA, move-o direto para resultados.
                    if tem_valor and not tem_data:
                        for item in reversed(cesto_sem_data):
                            if item["VALOR"] == "PENDENTE":
                                item["VALOR"] = valor_linha
                                if "DATA" in item:
                                    # C3: rubrica já tinha data → promove agora
                                    cesto_sem_data.remove(item)
                                    resultados.append(item)
                                break
                        ctx["rubrica_pendente"] = False

                    # 7b. Atualiza contexto com data/valor desta linha.
                    # dist_data/dist_valor contam linhas processadas desde o último
                    # dado visto — usados para limitar herança a linhas adjacentes.
                    if tem_data:
                        ctx["data_ctx"]    = match_data.group(1)
                        ctx["dist_data"]   = 0
                        ctx["era_exclusao"] = False
                    else:
                        ctx["dist_data"] = ctx["dist_data"] + 1
                    if tem_valor:
                        ctx["valor_ctx"]   = valor_linha
                        ctx["dist_valor"]  = 0
                        ctx["era_exclusao"] = False
                    else:
                        ctx["dist_valor"] = ctx["dist_valor"] + 1
                    # Linha só de texto (sem data, sem valor, sem rubrica): preserva contexto

    # ── 8. Flush final ───────────────────────────────────────────────────────
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
