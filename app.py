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
    st.error("Erro: A biblioteca 'openpyxl' não está instalada. Adicione 'openpyxl' no requirements.txt.")

# --- 1. CONFIGURAÇÃO E ESTILO ---
st.set_page_config(page_title="Edson Medeiros | Consultoria de Ativos", layout="wide", page_icon="⚖️")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;600&display=swap');
    .stApp { background-color: #0E1117; color: #FFFFFF; font-family: 'Inter', sans-serif; }
    .main-title { font-family: 'Playfair Display', serif; font-size: 3rem; color: #BFAF83; text-align: center; margin-bottom: 0; }
    .sub-title { text-align: center; color: #64748B; letter-spacing: 2px; text-transform: uppercase; font-size: 0.9rem; margin-bottom: 40px; }
    .metric-card { background: rgba(255,255,255,0.05); border: 1px solid #BFAF83; border-radius: 10px; padding: 20px; text-align: center; }
    div[data-testid="stFileUploader"] { border: 2px dashed #BFAF83; border-radius: 10px; padding: 10px; }
    .stButton > button { background-color: #BFAF83; color: #0E1117; font-weight: 600; border: none; border-radius: 6px; }
    .stButton > button:hover { background-color: #a89d74; color: #0E1117; }
    .stDownloadButton > button { background-color: transparent; color: #BFAF83; border: 1px solid #BFAF83; border-radius: 6px; }
    .stDownloadButton > button:hover { background-color: #BFAF83; color: #0E1117; }
    section[data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #30363D; }
</style>
""", unsafe_allow_html=True)

# --- 2. RUBRICAS MESTRE (exatamente como solicitado) ---
RUBRICAS_MESTRE = {
    "CESTA":                    r"\bCESTA\b",
    "PACOTE":                   r"\bPACOTE\b",
    "MORA DE OPERAÇÃO":         r"MORA DE OPERA[ÇC][ÃA]O|MORA DE OPERACAO",
    "MORA CREDITO PESSOAL":     r"MORA CREDITO PESSOAL|MORA CR[EÉ]D(ITO)?\s*PESS(OAL)?",
    "MORA OPERACAO DE CREDITO": r"MORA OPERA[ÇC][ÃA]O DE CR[EÉ]DITO|MORA OPER(ACAO)?\s*(DE)?\s*CRED(ITO)?",
    "BX":                       r"\bBX\b",
    "PARCELA CREDITO PESSOAL":  r"PARCELA CREDITO PESSOAL|PARC(ELA)?\s*CRED(ITO)?\s*PESS(OAL)?",
    "GASTOS CARTAO DE CREDITO": r"GASTOS CART[ÃA]O DE CR[EÉ]DITO|CART[ÃA]O DE CR[EÉ]DITO|GASTOS CART[ÃA]O",
    "SEGURO":                   r"\bSEGURO\b|\bSEGURADORA\b|\bSEG\b",
    "ADIANT":                   r"\bADIANT(AMENTO)?\b|\bADIANTAMENTO DEPOSITANTE\b",
    "APLIC":                    r"\bAPLICA[ÇC][ÃA]O\b|\bAPLIC\b",
    "ENCARGOS":                 r"\bENCARGOS?\b|\bENC LIMITE\b|\bLIMITE DE CRED\b",
    "ANUIDADE":                 r"\bANUIDADE\b|\bCART[ÃA]O CREDITO ANUIDADE\b",
    "OPERACOES VENCIDAS":       r"OPERA[ÇC][ÕO]ES VENCIDAS",
    "DIV. EM ATRASO":           r"DIV\.?\s*EM ATRASO|D[IÍ]VIDA\s*EM\s*ATRASO",
}

# Termos que indicam que a linha NÃO é um débito indevido
TERMOS_EXCLUSAO = r"\bTRANSF(ERENCIA)?\b|\bSALDO\b|\bSDO\b|\bSALARIO\b|\bSAL[AÁ]RIO\b"

# Padrões de separação de bloco (linhas divisórias típicas de extratos)
PADRAO_SEPARADOR = r"^[-=*_.]{5,}$|SALDO\s+ANTERIOR|SALDO\s+DO\s+DIA|TOTAL\s+DO\s+DIA"

# --- 3. FUNÇÕES AUXILIARES ---
def _fix_date(d: str) -> str:
    """Normaliza datas de 2 dígitos para 4 (ex: 17 → 2017)."""
    p = d.split('/')
    if len(p) == 3 and len(p[2]) == 2:
        p[2] = "20" + p[2]
    return "/".join(p)

def _extrair_valor(linha: str):
    """Extrai o valor monetário brasileiro da linha, ignorando percentuais."""
    m = re.search(r"(\d{1,3}(?:\.\d{3})*,\d{2})(?!\s*%)", linha)
    return m.group(1) if m else None

def _extrair_data(linha: str):
    """Extrai data no formato DD/MM/AA ou DD/MM/AAAA."""
    m = re.search(r"\b(\d{2}/\d{2}/\d{2,4})\b", linha)
    return m.group(1) if m else None

def _e_linha_exclusao(linha: str) -> bool:
    return bool(re.search(TERMOS_EXCLUSAO, linha))

def _e_separador(linha: str) -> bool:
    return bool(re.search(PADRAO_SEPARADOR, linha))

# --- 4. MOTOR DE AUDITORIA — LÓGICA DATA INFERIOR ---
#
# FUNCIONAMENTO:
# O extrato tem blocos separados por linhas divisórias ou pela própria data.
# Dentro de cada bloco, as rubricas e valores aparecem ANTES da data.
# Quando o robô encontra uma data, ela pertence a TODAS as rubricas
# acumuladas no bloco ACIMA dela — nunca à linha onde está.
#
# Fluxo por linha:
#   1. Se for separador → sela bloco atual com última data conhecida e limpa
#   2. Se for exclusão  → descarta itens pendentes do bloco
#   3. Se tiver rubrica → adiciona ao bloco (com valor se houver, senão PENDENTE)
#   4. Se tiver só valor e bloco não vazio → associa ao último item pendente
#   5. Se tiver data    → sela o bloco atual com essa data e limpa
#
def realizar_auditoria(arquivo, rubricas_alvo: list) -> list:
    resultados = []

    with pdfplumber.open(arquivo) as pdf:
        total_pages = len(pdf.pages)
        progress = st.progress(0, text="Iniciando leitura do PDF...")

        for n_pag, page in enumerate(pdf.pages):
            progress.progress(
                (n_pag + 1) / total_pages,
                text=f"Processando página {n_pag + 1} de {total_pages}..."
            )

            texto = page.extract_text(x_tolerance=3, y_tolerance=3)
            if not texto:
                continue

            # Bloco acumulador: lista de dicts {CATEGORIA, VALOR, HISTÓRICO}
            bloco: list[dict] = []

            for linha in texto.split('\n'):
                linha_up = linha.upper().strip()
                if not linha_up:
                    continue

                data_linha  = _extrair_data(linha_up)
                valor_linha = _extrair_valor(linha_up)

                # ── PASSO 1: Separador de bloco ──────────────────────────────
                # Ex: "----", "SALDO DO DIA", etc.
                # Descarta itens ainda PENDENTE e limpa (sem data = não selamos)
                if _e_separador(linha_up):
                    bloco = []
                    continue

                # ── PASSO 2: Termos de exclusão ──────────────────────────────
                # A linha indica transferência, salário, saldo — não é débito
                if _e_linha_exclusao(linha_up):
                    # Remove apenas os que ainda estão sem data (PENDENTE de valor)
                    bloco = [i for i in bloco if i["VALOR"] != "PENDENTE"]
                    continue

                # ── PASSO 3: Detecção de Rubrica ─────────────────────────────
                # Ignora linhas com "%" (juros/taxas em percentual)
                rubrica = None
                if "%" not in linha_up:
                    for nome in rubricas_alvo:
                        if re.search(RUBRICAS_MESTRE[nome], linha_up):
                            rubrica = nome
                            break

                if rubrica:
                    bloco.append({
                        "CATEGORIA": rubrica,
                        "VALOR":     valor_linha if valor_linha else "PENDENTE",
                        "HISTÓRICO": linha_up[:100],
                    })
                    # Se a mesma linha trouxe data junto, selamos imediatamente
                    # (caso de extratos com data na mesma linha da rubrica)
                    if data_linha and valor_linha:
                        item = bloco[-1]
                        item["DATA"] = data_linha
                        resultados.append(item)
                        bloco.pop()
                    continue  # próxima linha

                # ── PASSO 4: Valor solto (sem rubrica na mesma linha) ─────────
                # Associa ao último item do bloco que ainda está PENDENTE de valor
                if valor_linha and bloco:
                    for item in reversed(bloco):
                        if item["VALOR"] == "PENDENTE":
                            item["VALOR"] = valor_linha
                            break

                # ── PASSO 5: DATA INFERIOR ───────────────────────────────────
                # A data encontrada é a referência de TODOS os itens acumulados
                # no bloco acima dela. Selamos e limpamos o bloco.
                if data_linha and bloco:
                    itens_selados = []
                    for item in bloco:
                        if item["VALOR"] != "PENDENTE":   # só sela se tem valor
                            item["DATA"] = data_linha
                            resultados.append(item)
                        # itens ainda PENDENTE de valor são descartados
                    bloco = []

        progress.empty()

    return resultados

# --- 5. GERAÇÃO DE EXCEL ---
def gerar_excel_calculos(df: pd.DataFrame, rubrica_nome: str) -> bytes:
    df = df.copy()
    df['DT']      = pd.to_datetime(df['DATA'].apply(_fix_date), format='%d/%m/%Y', errors='coerce')
    df['ANO']     = df['DT'].dt.year.astype('Int64')
    df['MES_NUM'] = df['DT'].dt.month.astype('Int64')

    agrupado = df.groupby(['ANO', 'MES_NUM'])['V_NUM'].sum().reset_index()

    wb = Workbook()
    ws = wb.active
    ws.title = "Tabela de Cálculos"

    font_header  = Font(bold=True, size=11)
    font_title   = Font(bold=True, size=12)
    fill_blue    = PatternFill(start_color="BDD7EE", end_color="BDD7EE", fill_type="solid")
    fill_peach   = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid")
    thin_border  = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'),  bottom=Side(style='thin')
    )
    align_center = Alignment(horizontal='center', vertical='center')

    anos = sorted(agrupado['ANO'].dropna().unique().astype(int))
    if not anos:
        anos = [datetime.now().year]
    n_anos = len(anos)

    # Título
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=n_anos + 1)
    c = ws.cell(row=1, column=1, value=f'VALORES DESCONTADOS INDEVIDAMENTE - "{rubrica_nome}"')
    c.font, c.fill, c.alignment = font_title, fill_blue, align_center

    # Cabeçalhos de ano
    ws.cell(row=2, column=1, value="MESES").font = font_header
    ws.cell(row=2, column=1).alignment = align_center
    ws.cell(row=2, column=1).fill = fill_blue
    for idx, ano in enumerate(anos):
        c = ws.cell(row=2, column=idx + 2, value=ano)
        c.font, c.alignment, c.fill = font_header, align_center, fill_blue

    # Meses
    meses_nomes = ["JANEIRO","FEVEREIRO","MARÇO","ABRIL","MAIO","JUNHO",
                   "JULHO","AGOSTO","SETEMBRO","OUTUBRO","NOVEMBRO","DEZEMBRO"]
    for m_idx, mes in enumerate(meses_nomes):
        row = m_idx + 3
        c = ws.cell(row=row, column=1, value=mes)
        c.font, c.fill, c.border, c.alignment = font_header, fill_blue, thin_border, align_center
        for a_idx, ano in enumerate(anos):
            col = a_idx + 2
            val = agrupado[
                (agrupado['ANO'] == ano) & (agrupado['MES_NUM'] == m_idx + 1)
            ]['V_NUM'].sum()
            c = ws.cell(row=row, column=col, value=float(val) if val > 0 else None)
            if val > 0:
                c.number_format = '"R$ " #,##0.00'
            c.fill, c.border = fill_peach, thin_border

    last_col = get_column_letter(n_anos + 1)

    # Valor Anual
    row_anual = 15
    c = ws.cell(row=row_anual, column=1, value="VALOR ANUAL:")
    c.font, c.fill, c.border = font_header, fill_blue, thin_border
    for idx in range(n_anos):
        col_l = get_column_letter(idx + 2)
        c = ws.cell(row=row_anual, column=idx + 2, value=f"=SUM({col_l}3:{col_l}14)")
        c.number_format = '"R$ " #,##0.00'
        c.font, c.fill, c.border = font_header, fill_peach, thin_border

    # Valor Total
    row_total = 16
    ws.cell(row=row_total, column=1, value="VALOR TOTAL:").font = font_header
    ws.cell(row=row_total, column=1).fill = fill_blue
    ws.merge_cells(start_row=row_total, start_column=2, end_row=row_total, end_column=n_anos + 1)
    c = ws.cell(row=row_total, column=2, value=f"=SUM(B{row_anual}:{last_col}{row_anual})")
    c.number_format = '"R$ " #,##0.00'
    c.font, c.alignment = font_header, Alignment(horizontal='right')

    # Valor em Dobro (Art. 42 CDC)
    row_dobro = 17
    ws.merge_cells(start_row=row_dobro, start_column=1, end_row=row_dobro + 1, end_column=1)
    c = ws.cell(row=row_dobro, column=1, value="VALOR EM DOBRO\nART. 42 DO CDC")
    c.font = font_header
    c.fill = fill_blue
    c.alignment = Alignment(wrap_text=True, horizontal='center', vertical='center')
    ws.merge_cells(start_row=row_dobro, start_column=2, end_row=row_dobro + 1, end_column=n_anos + 1)
    c = ws.cell(row=row_dobro, column=2, value=f"=B{row_total}*2")
    c.number_format = '"R$ " #,##0.00'
    c.font = font_header
    c.fill = fill_peach
    c.alignment = Alignment(horizontal='right', vertical='center')

    ws.column_dimensions['A'].width = 28
    for i in range(2, n_anos + 2):
        ws.column_dimensions[get_column_letter(i)].width = 16

    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()

# --- 6. DASHBOARD ---
st.markdown('<h1 class="main-title">Consultoria de Ativos</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Auditoria Técnica Especializada — Edson Medeiros</p>', unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────────────────────────
st.sidebar.markdown("### 🔍 RUBRICAS DE AUDITORIA")

col_b1, col_b2 = st.sidebar.columns(2)
if col_b1.button("✅ Marcar Todas", use_container_width=True):
    for r in RUBRICAS_MESTRE:
        st.session_state[f"chk_{r}"] = True
if col_b2.button("❌ Desmarcar", use_container_width=True):
    for r in RUBRICAS_MESTRE:
        st.session_state[f"chk_{r}"] = False

st.sidebar.markdown("---")

selecionadas = []
for r in RUBRICAS_MESTRE:
    if f"chk_{r}" not in st.session_state:
        st.session_state[f"chk_{r}"] = True
    val = st.sidebar.checkbox(r, value=st.session_state[f"chk_{r}"], key=f"chk_{r}")
    if val:
        selecionadas.append(r)

st.sidebar.markdown("---")
st.sidebar.markdown(f"**{len(selecionadas)}** rubrica(s) ativa(s)")

# ── Upload ────────────────────────────────────────────────────────────────────
upload = st.file_uploader("📂  ARRASTE O EXTRATO BANCÁRIO (PDF)", type=["pdf"])

if upload:
    if not selecionadas:
        st.warning("⚠️ Selecione pelo menos uma rubrica na barra lateral.")
    else:
        with st.spinner("Analisando o extrato..."):
            dados = realizar_auditoria(upload, selecionadas)

        if dados:
            df = pd.DataFrame(dados)
            df['V_NUM'] = (
                df['VALOR']
                .str.replace('.', '', regex=False)
                .str.replace(',', '.', regex=False)
                .astype(float)
            )
            df['DT_O'] = pd.to_datetime(df['DATA'].apply(_fix_date), format='%d/%m/%Y', errors='coerce')
            df = df.sort_values('DT_O').reset_index(drop=True)

            total_geral   = df['V_NUM'].sum()
            total_dobro   = total_geral * 2
            n_lancamentos = len(df)
            n_categorias  = df['CATEGORIA'].nunique()

            # Métricas
            c1, c2, c3, c4 = st.columns(4)
            for col, titulo, valor in zip(
                [c1, c2, c3, c4],
                ["💰 TOTAL RECUPERÁVEL", "⚖️ VALOR EM DOBRO", "📌 LANÇAMENTOS", "🗂️ CATEGORIAS"],
                [f"R$ {total_geral:,.2f}", f"R$ {total_dobro:,.2f}", str(n_lancamentos), str(n_categorias)]
            ):
                with col:
                    st.markdown(
                        f'<div class="metric-card"><h4>{titulo}</h4>'
                        f'<h2 style="color:#BFAF83;">{valor}</h2></div>',
                        unsafe_allow_html=True
                    )

            st.markdown("<br>", unsafe_allow_html=True)

            # Downloads
            st.markdown(
                '<h2 style="color:#BFAF83; text-align:center; margin-top:20px;">📥 Baixar Tabelas de Cálculos</h2>',
                unsafe_allow_html=True
            )
            st.write("Clique para baixar a planilha Excel de cada rubrica com fórmulas automáticas e cálculo do Art. 42 CDC.")

            cats = df['CATEGORIA'].unique()
            cols_dl = st.columns(min(len(cats), 3))
            for i, cat in enumerate(cats):
                df_cat     = df[df['CATEGORIA'] == cat]
                excel_file = gerar_excel_calculos(df_cat, cat)
                total_cat  = df_cat['V_NUM'].sum()
                with cols_dl[i % 3]:
                    st.download_button(
                        label=f"📊 {cat}\nR$ {total_cat:,.2f}",
                        data=excel_file,
                        file_name=f"Tabela_{cat.replace(' ', '_')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )

            # Tabela detalhada
            st.markdown(
                '<h3 style="color:#BFAF83; text-align:center; margin-top:30px;">📋 Lista Detalhada</h3>',
                unsafe_allow_html=True
            )
            filtro_cat = st.selectbox("Filtrar por categoria:", ["Todas"] + list(df['CATEGORIA'].unique()))
            df_view = df if filtro_cat == "Todas" else df[df['CATEGORIA'] == filtro_cat]

            st.dataframe(
                df_view[['DATA', 'CATEGORIA', 'VALOR', 'HISTÓRICO']].rename(columns={
                    'DATA': 'Data', 'CATEGORIA': 'Categoria',
                    'VALOR': 'Valor (R$)', 'HISTÓRICO': 'Histórico'
                }),
                use_container_width=True,
                hide_index=True,
            )

        else:
            st.info("ℹ️ Nenhum débito encontrado. Verifique se o PDF contém extratos legíveis.")

st.markdown(
    "<br><br><p style='text-align:right; font-family:serif; font-style:italic; color:#BFAF83;'>Edson Medeiros</p>",
    unsafe_allow_html=True
)
