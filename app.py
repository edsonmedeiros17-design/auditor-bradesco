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
    .debug-box { background: rgba(50, 150, 200, 0.1); border: 1px solid #3296C8; border-radius: 8px; padding: 15px; margin: 10px 0; font-size: 10px; max-height: 600px; overflow-y: auto; }
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

# --- 4. PROCESSADOR COM ESTRATÉGIA POR RUBRICA ---

class ProcessadorExtratoSeguro:
    """
    Processa extratos com estratégia específica por rubrica.
    
    REGRAS CRÍTICAS:
    - CESTA: SEMPRE pega data e valor DA MESMA LINHA
    - Outras: podem herdar data de contexto ou da linha anterior se necessário
    """
    
    @staticmethod
    def extrair_data_segura(texto: str) -> Optional[str]:
        """Extrai data com validação total."""
        pattern = r'\b(\d{2}/\d{2}/\d{2,4})\b'
        match = re.search(pattern, texto)
        
        if not match:
            return None
        
        data_str = match.group(1)
        partes = data_str.split('/')
        
        if len(partes) != 3:
            return None
        
        try:
            dia, mes, ano = partes
            dia_int = int(dia)
            mes_int = int(mes)
            ano_int = int(ano)
            
            if not (1 <= dia_int <= 31 and 1 <= mes_int <= 12):
                return None
            
            if ano_int < 100:
                ano_int = 2000 + ano_int
            
            try:
                datetime(ano_int, mes_int, dia_int)
            except ValueError:
                return None
            
            return f"{dia}/{mes}/{str(ano_int)}"
        except:
            return None
    
    @staticmethod
    def extrair_valor_seguro(texto: str) -> Optional[str]:
        """Extrai valor brasileiro com validação."""
        # Padrão: 1,23 | 1.234,56 | 1.234.567,89
        pattern = r'\b(\d{1,3}(?:\.\d{3})*,\d{2})\b'
        
        matches = re.finditer(pattern, texto)
        
        for match in matches:
            valor = match.group(1)
            
            # Valida que NÃO é porcentagem
            pos_final = match.end()
            if pos_final < len(texto):
                prox_chars = texto[pos_final:pos_final+3].strip()
                if prox_chars.startswith('%'):
                    continue
            
            return valor
        
        return None
    
    @staticmethod
    def detectar_rubrica(texto: str, rubricas_alvo: List[str]) -> Optional[str]:
        """Detecta rubrica presente na linha."""
        texto_up = texto.upper().strip()
        
        if "%" in texto_up:
            return None
        
        for nome_rubrica in rubricas_alvo:
            regex_rubrica = RUBRICAS_MESTRE[nome_rubrica]
            if re.search(regex_rubrica, texto_up):
                return nome_rubrica
        
        return None


class AnalisadorExtratoOtimizado:
    """
    Analisador otimizado que trata CESTA com lógica especial.
    
    LÓGICA CESTA:
    - Sempre pega DATA da MESMA LINHA onde CESTA foi encontrada
    - Sempre pega VALOR da MESMA LINHA onde CESTA foi encontrada
    - NUNCA herda dados de outras linhas
    """
    
    def __init__(self, rubricas_alvo: List[str], modo: str = "DATA_SUPERIOR"):
        self.rubricas_alvo = rubricas_alvo
        self.modo = modo
        self.log = []
        self.resultados = []
    
    def adicionar_log(self, msg: str):
        """Adiciona mensagem ao log."""
        self.log.append(msg)
    
    def processar_pdf(self, arquivo) -> List[Dict]:
        """
        Processa PDF com estratégia de leitura por modo.
        """
        if self.modo == "DATA_SUPERIOR":
            return self._processar_data_superior(arquivo)
        else:
            return self._processar_data_inferior(arquivo)
    
    def _processar_data_superior(self, arquivo) -> List[Dict]:
        """
        MODO DATA SUPERIOR: Data aparece no topo/início.
        """
        try:
            with pdfplumber.open(arquivo) as pdf:
                contexto_data = None
                
                for num_pagina, page in enumerate(pdf.pages):
                    texto = page.extract_text(x_tolerance=2, y_tolerance=2)
                    if not texto:
                        self.adicionar_log(f"[PÁG {num_pagina + 1}] Vazia")
                        continue
                    
                    linhas = texto.split('\n')
                    self.adicionar_log(f"\n[PÁG {num_pagina + 1}] {len(linhas)} linhas")
                    
                    for idx_linha, linha in enumerate(linhas):
                        linha_stripped = linha.strip()
                        
                        if not linha_stripped:
                            continue
                        
                        # ===== PASSO 1: Procura DATA =====
                        data_encontrada = ProcessadorExtratoSeguro.extrair_data_segura(linha_stripped)
                        if data_encontrada:
                            contexto_data = data_encontrada
                            self.adicionar_log(f"  [L{idx_linha}] 📅 DATA CONTEXTO: {contexto_data}")
                            continue
                        
                        # ===== PASSO 2: Verifica EXCLUSÃO =====
                        if re.search(TERMOS_EXCLUSAO, linha_stripped.upper()):
                            self.adicionar_log(f"  [L{idx_linha}] ❌ Exclusão (limpa contexto)")
                            contexto_data = None
                            continue
                        
                        # ===== PASSO 3: Procura RUBRICA =====
                        rubrica = ProcessadorExtratoSeguro.detectar_rubrica(linha_stripped, self.rubricas_alvo)
                        if rubrica:
                            valor = ProcessadorExtratoSeguro.extrair_valor_seguro(linha_stripped)
                            
                            # ===== LÓGICA ESPECIAL PARA CESTA =====
                            if rubrica == "CESTA":
                                # CESTA SEMPRE pega dados da MESMA LINHA
                                if valor:
                                    self.adicionar_log(f"  [L{idx_linha}] 🎁 CESTA (MESMO ROW) | VALOR: {valor} | DATA: {contexto_data}")
                                    self.resultados.append({
                                        "PÁGINA": num_pagina + 1,
                                        "LINHA": idx_linha,
                                        "RUBRICA": rubrica,
                                        "VALOR": valor,
                                        "DATA": contexto_data if contexto_data else "SEM_DATA",
                                        "TEXTO": linha_stripped[:80],
                                        "ESTRATEGIA": "CESTA_SAME_ROW"
                                    })
                                else:
                                    self.adicionar_log(f"  [L{idx_linha}] ⚠️ CESTA SEM VALOR NA MESMA LINHA - IGNORANDO")
                            
                            # ===== LÓGICA PADRÃO PARA OUTRAS RUBRICAS =====
                            else:
                                if not valor and idx_linha + 1 < len(linhas):
                                    proxima = linhas[idx_linha + 1].strip()
                                    valor_prox = ProcessadorExtratoSeguro.extrair_valor_seguro(proxima)
                                    if valor_prox:
                                        valor = valor_prox
                                        self.adicionar_log(f"  [L{idx_linha}] ✅ {rubrica} | VALOR (próx L): {valor} | DATA: {contexto_data}")
                                        self.resultados.append({
                                            "PÁGINA": num_pagina + 1,
                                            "LINHA": idx_linha,
                                            "RUBRICA": rubrica,
                                            "VALOR": valor,
                                            "DATA": contexto_data if contexto_data else "SEM_DATA",
                                            "TEXTO": linha_stripped[:80],
                                            "ESTRATEGIA": "PROX_LINE"
                                        })
                                        continue
                                
                                if valor:
                                    self.adicionar_log(f"  [L{idx_linha}] ✅ {rubrica} | VALOR: {valor} | DATA: {contexto_data}")
                                    self.resultados.append({
                                        "PÁGINA": num_pagina + 1,
                                        "LINHA": idx_linha,
                                        "RUBRICA": rubrica,
                                        "VALOR": valor,
                                        "DATA": contexto_data if contexto_data else "SEM_DATA",
                                        "TEXTO": linha_stripped[:80],
                                        "ESTRATEGIA": "SAME_LINE"
                                    })
                                else:
                                    self.adicionar_log(f"  [L{idx_linha}] ⚠️ {rubrica} SEM VALOR")
                
                self.adicionar_log(f"\n[RESUMO] {len(self.resultados)} registros encontrados")
        
        except Exception as e:
            self.adicionar_log(f"ERRO: {str(e)}")
            st.error(f"❌ Erro ao processar: {str(e)}")
        
        return self.resultados
    
    def _processar_data_inferior(self, arquivo) -> List[Dict]:
        """
        MODO DATA INFERIOR: Data aparece abaixo das rubricas.
        """
        try:
            with pdfplumber.open(arquivo) as pdf:
                buffer_rubricas = []
                ultima_data = None
                
                for num_pagina, page in enumerate(pdf.pages):
                    texto = page.extract_text(x_tolerance=2, y_tolerance=2)
                    if not texto:
                        self.adicionar_log(f"[PÁG {num_pagina + 1}] Vazia")
                        continue
                    
                    linhas = texto.split('\n')
                    self.adicionar_log(f"\n[PÁG {num_pagina + 1}] {len(linhas)} linhas")
                    
                    for idx_linha, linha in enumerate(linhas):
                        linha_stripped = linha.strip()
                        
                        if not linha_stripped:
                            continue
                        
                        # ===== PASSO 1: Procura DATA (DATA INFERIOR) =====
                        data_encontrada = ProcessadorExtratoSeguro.extrair_data_segura(linha_stripped)
                        if data_encontrada:
                            ultima_data = data_encontrada
                            self.adicionar_log(f"  [L{idx_linha}] 📅 DATA INFERIOR: {ultima_data}")
                            
                            # Sela o buffer com esta data
                            if buffer_rubricas:
                                self.adicionar_log(f"    → Selando {len(buffer_rubricas)} registros")
                                for rubrica, valor, texto, linha_idx in buffer_rubricas:
                                    # ===== LÓGICA ESPECIAL PARA CESTA =====
                                    if rubrica == "CESTA":
                                        # CESTA: se não tem valor, tenta extrair da linha da data
                                        if valor == "SEM_VALOR":
                                            valor_tentativa = ProcessadorExtratoSeguro.extrair_valor_seguro(linha_stripped)
                                            if valor_tentativa:
                                                valor = valor_tentativa
                                        
                                        self.adicionar_log(f"      🎁 CESTA | VALOR: {valor} | DATA: {ultima_data}")
                                    else:
                                        self.adicionar_log(f"      ✅ {rubrica} | VALOR: {valor} | DATA: {ultima_data}")
                                    
                                    self.resultados.append({
                                        "PÁGINA": num_pagina + 1,
                                        "LINHA": linha_idx,
                                        "RUBRICA": rubrica,
                                        "VALOR": valor,
                                        "DATA": ultima_data,
                                        "TEXTO": texto[:80],
                                        "ESTRATEGIA": "BUFFER_SEAL"
                                    })
                                
                                buffer_rubricas = []
                            
                            # Verifica se tem rubrica na mesma linha da data
                            rubrica = ProcessadorExtratoSeguro.detectar_rubrica(linha_stripped, self.rubricas_alvo)
                            if rubrica:
                                valor = ProcessadorExtratoSeguro.extrair_valor_seguro(linha_stripped)
                                if not valor and idx_linha + 1 < len(linhas):
                                    valor = ProcessadorExtratoSeguro.extrair_valor_seguro(linhas[idx_linha + 1])
                                
                                self.adicionar_log(f"  [L{idx_linha}] ✅ {rubrica} NA DATA | VALOR: {valor}")
                                self.resultados.append({
                                    "PÁGINA": num_pagina + 1,
                                    "LINHA": idx_linha,
                                    "RUBRICA": rubrica,
                                    "VALOR": valor if valor else "SEM_VALOR",
                                    "DATA": ultima_data,
                                    "TEXTO": linha_stripped[:80],
                                    "ESTRATEGIA": "DATA_SAME_LINE"
                                })
                            
                            continue
                        
                        # ===== PASSO 2: Verifica EXCLUSÃO =====
                        if re.search(TERMOS_EXCLUSAO, linha_stripped.upper()):
                            buffer_rubricas = []
                            self.adicionar_log(f"  [L{idx_linha}] ❌ Exclusão (limpa buffer)")
                            continue
                        
                        # ===== PASSO 3: Procura RUBRICA para BUFFER =====
                        rubrica = ProcessadorExtratoSeguro.detectar_rubrica(linha_stripped, self.rubricas_alvo)
                        if rubrica:
                            valor = ProcessadorExtratoSeguro.extrair_valor_seguro(linha_stripped)
                            
                            # ===== LÓGICA ESPECIAL PARA CESTA =====
                            if rubrica == "CESTA":
                                # CESTA: SEMPRE pega valor da mesma linha
                                # Se não encontrar na mesma linha, não adiciona ao buffer
                                if valor:
                                    buffer_rubricas.append((rubrica, valor, linha_stripped, idx_linha))
                                    self.adicionar_log(f"  [L{idx_linha}] 🎁 BUFFER CESTA | VALOR: {valor}")
                                else:
                                    self.adicionar_log(f"  [L{idx_linha}] ⚠️ CESTA SEM VALOR - IGNORANDO")
                            else:
                                # Outras rubricas podem ir para buffer sem valor
                                buffer_rubricas.append((rubrica, valor if valor else "SEM_VALOR", linha_stripped, idx_linha))
                                self.adicionar_log(f"  [L{idx_linha}] → BUFFER {rubrica} | VALOR: {valor if valor else 'SEM_VALOR'}")
                
                # Processa buffer final
                if buffer_rubricas:
                    self.adicionar_log(f"\n[FIM PDF] Selando {len(buffer_rubricas)} registros finais")
                    for rubrica, valor, texto, linha_idx in buffer_rubricas:
                        self.resultados.append({
                            "PÁGINA": "?",
                            "LINHA": linha_idx,
                            "RUBRICA": rubrica,
                            "VALOR": valor,
                            "DATA": ultima_data if ultima_data else "SEM_DATA",
                            "TEXTO": texto[:80],
                            "ESTRATEGIA": "BUFFER_FINAL"
                        })
                        self.adicionar_log(f"  ✅ {rubrica} | VALOR: {valor}")
                
                self.adicionar_log(f"\n[RESUMO] {len(self.resultados)} registros encontrados")
        
        except Exception as e:
            self.adicionar_log(f"ERRO: {str(e)}")
            st.error(f"❌ Erro ao processar: {str(e)}")
        
        return self.resultados


def converter_valor_para_float(valor_str: str) -> float:
    """Conversão segura para float."""
    if not valor_str or valor_str in ["SEM_VALOR", "SEM_DATA"]:
        return 0.0
    
    try:
        valor_str = str(valor_str).strip()
        if '%' in valor_str:
            return 0.0
        
        valor_str = valor_str.replace('.', '').replace(',', '.')
        valor = float(valor_str)
        
        return valor if valor > 0 else 0.0
    except:
        return 0.0


def gerar_excel_calculos(df: pd.DataFrame, rubrica_nome: str) -> Optional[bytes]:
    """Gera Excel."""
    if df.empty:
        return None
    
    try:
        df = df.copy()
        df['V_NUM'] = df['VALOR'].apply(converter_valor_para_float)
        df = df[df['V_NUM'] > 0]
        
        if df.empty:
            return None
        
        df['DT'] = pd.to_datetime(df['DATA'], format='%d/%m/%Y', errors='coerce')
        df = df.dropna(subset=['DT'])
        
        if df.empty:
            return None
        
        df['ANO'] = df['DT'].dt.year.astype(int)
        df['MES_NUM'] = df['DT'].dt.month.astype(int)
        
        agrupado = df.groupby(['ANO', 'MES_NUM'])['V_NUM'].sum().reset_index()
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Cálculos"
        
        font_header = Font(bold=True, size=11, color="FFFFFF")
        font_title = Font(bold=True, size=12, color="FFFFFF")
        fill_blue = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
        fill_peach = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid")
        fill_total = PatternFill(start_color="92D050", end_color="92D050", fill_type="solid")
        border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
        align_right = Alignment(horizontal='right', vertical='center')
        align_center = Alignment(horizontal='center', vertical='center')
        
        ws.merge_cells('A1:E1')
        cell = ws['A1']
        cell.value = f"VALORES DESCONTADOS - \"{rubrica_nome}\""
        cell.font = font_title
        cell.fill = fill_blue
        cell.alignment = align_center
        
        meses_nomes = ["JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO",
                       "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"]
        
        ws['A2'] = "MESES"
        ws['A2'].font = font_header
        ws['A2'].fill = fill_blue
        
        anos = sorted(agrupado['ANO'].unique())
        if not anos:
            anos = [datetime.now().year]
        
        for idx, ano in enumerate(anos):
            col = idx + 2
            cell = ws.cell(row=2, column=col, value=int(ano))
            cell.font = font_header
            cell.fill = fill_blue
            cell.alignment = align_center
        
        for m_idx, mes in enumerate(meses_nomes):
            row = m_idx + 3
            cell_mes = ws.cell(row=row, column=1, value=mes)
            cell_mes.font = font_header
            cell_mes.fill = fill_blue
            
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
        
        row_anual = 15
        cell_label = ws.cell(row=row_anual, column=1, value="VALOR ANUAL:")
        cell_label.font = font_header
        cell_label.fill = fill_blue
        
        for idx, ano in enumerate(anos):
            col = idx + 2
            col_letter = get_column_letter(col)
            cell = ws.cell(row=row_anual, column=col, value=f"=SUM({col_letter}3:{col_letter}14)")
            cell.number_format = '"R$ " #,##0.00'
            cell.font = font_header
            cell.fill = fill_total
            cell.alignment = align_right
        
        row_total = 16
        ws.cell(row=row_total, column=1, value="VALOR TOTAL:").font = font_header
        ws.cell(row=row_total, column=1).fill = fill_blue
        
        last_col_letter = get_column_letter(len(anos) + 1)
        ws.merge_cells(start_row=row_total, start_column=2, end_row=row_total, end_column=len(anos)+1)
        cell_total = ws.cell(row=row_total, column=2, value=f"=SUM(B{row_anual}:{last_col_letter}{row_anual})")
        cell_total.number_format = '"R$ " #,##0.00'
        cell_total.font = font_header
        cell_total.fill = fill_total
        cell_total.alignment = align_right
        
        row_dobro = 17
        ws.merge_cells(start_row=row_dobro, start_column=1, end_row=row_dobro+1, end_column=1)
        cell_dobro = ws.cell(row=row_dobro, column=1, value="DOBRO\nART. 42")
        cell_dobro.font = font_header
        cell_dobro.fill = fill_blue
        cell_dobro.alignment = Alignment(wrap_text=True, horizontal='center', vertical='center')
        
        ws.merge_cells(start_row=row_dobro, start_column=2, end_row=row_dobro+1, end_column=len(anos)+1)
        cell_dobro2 = ws.cell(row=row_dobro, column=2, value=f"=B{row_total}*2")
        cell_dobro2.number_format = '"R$ " #,##0.00'
        cell_dobro2.font = font_header
        cell_dobro2.fill = fill_total
        cell_dobro2.alignment = align_right
        
        ws.column_dimensions['A'].width = 25
        for i in range(2, len(anos) + 2):
            ws.column_dimensions[get_column_letter(i)].width = 15
        
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output.getvalue()
    
    except Exception as e:
        st.error(f"❌ Erro Excel: {str(e)}")
        return None


# --- 8. DASHBOARD ---
st.markdown('<h1 class="main-title">⚖️ Consultoria de Ativos</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">🔬 Auditoria Precisa - Lógica CESTA Corrigida</p>', unsafe_allow_html=True)

st.sidebar.markdown("### ⚙️ CONFIGURAÇÃO")

modo_leitura = st.sidebar.radio(
    "Formato do extrato:",
    options=["DATA_SUPERIOR", "DATA_INFERIOR"],
    format_func=lambda x: "📅 Data Superior (ANEXO 1)" if x == "DATA_SUPERIOR" else "📅 Data Inferior (ANEXO 2)",
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 RUBRICAS")

col_b1, col_b2 = st.sidebar.columns(2)
with col_b1:
    if st.button("✅ Marcar Todas", use_container_width=True):
        for r in RUBRICAS_MESTRE.keys():
            st.session_state.rubricas_selecionadas[r] = True
        st.rerun()

with col_b2:
    if st.button("❌ Desmarcar Todas", use_container_width=True):
        for r in RUBRICAS_MESTRE.keys():
            st.session_state.rubricas_selecionadas[r] = False
        st.rerun()

st.sidebar.markdown("")

selecionadas = []
for r in RUBRICAS_MESTRE.keys():
    checked = st.sidebar.checkbox(r, value=st.session_state.rubricas_selecionadas.get(r, True), key=f"check_{r}")
    st.session_state.rubricas_selecionadas[r] = checked
    if checked:
        selecionadas.append(r)

st.sidebar.markdown("---")
st.session_state.debug_mode = st.sidebar.checkbox("🐛 Debug", value=st.session_state.debug_mode)

upload = st.file_uploader("📂 PDF DO EXTRATO", type=["pdf"])

if upload:
    with st.spinner("⚡ Analisando..."):
        analisador = AnalisadorExtratoOtimizado(selecionadas, modo_leitura)
        dados = analisador.processar_pdf(upload)
        st.session_state.log_debug = analisador.log
        
        if dados:
            df = pd.DataFrame(dados)
            
            # Filtra válidos
            df['V_NUM'] = df['VALOR'].apply(converter_valor_para_float)
            df_valido = df[(df['V_NUM'] > 0) & (df['DATA'] != "SEM_DATA")].copy()
            
            if df_valido.empty:
                st.error("❌ Nenhum valor válido!")
            else:
                df_valido['DT'] = pd.to_datetime(df_valido['DATA'], format='%d/%m/%Y', errors='coerce')
                df_valido = df_valido.dropna(subset=['DT']).sort_values('DT')
                
                total = df_valido['V_NUM'].sum()
                
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown(f'<div class="metric-card"><h4>💰 TOTAL</h4><h2 style="color:#BFAF83;">R$ {total:,.2f}</h2></div>', unsafe_allow_html=True)
                with c2:
                    st.markdown(f'<div class="metric-card"><h4>📝 LANÇAMENTOS</h4><h2 style="color:#BFAF83;">{len(df_valido)}</h2></div>', unsafe_allow_html=True)
                with c3:
                    st.markdown(f'<div class="metric-card"><h4>💼 RUBRICAS</h4><h2 style="color:#BFAF83;">{df_valido["RUBRICA"].nunique()}</h2></div>', unsafe_allow_html=True)
                
                st.markdown('<h2 style="color:#BFAF83; text-align:center; margin-top:30px;">📥 Downloads</h2>', unsafe_allow_html=True)
                
                cats = sorted(df_valido['RUBRICA'].unique())
                cols = st.columns(min(3, len(cats)))
                
                for idx, cat in enumerate(cats):
                    df_cat = df_valido[df_valido['RUBRICA'] == cat]
                    excel = gerar_excel_calculos(df_cat, cat)
                    if excel:
                        with cols[idx % len(cols)]:
                            st.download_button(f"📊 {cat}", excel, f"Tabela_{cat.replace(' ', '_')}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
                
                st.markdown('<h3 style="color:#BFAF83; text-align:center; margin-top:30px;">📋 Extrato</h3>', unsafe_allow_html=True)
                
                df_exib = df_valido[['DATA', 'RUBRICA', 'VALOR', 'TEXTO']].copy()
                df_exib.columns = ['DATA', 'RUBRICA', 'VALOR (R$)', 'HISTÓRICO']
                st.dataframe(df_exib, use_container_width=True, hide_index=True)
                
                if st.session_state.debug_mode:
                    st.markdown("---")
                    st.markdown("### 🐛 LOG DETALHADO")
                    log_text = "\n".join(st.session_state.log_debug)
                    st.markdown(f'<div class="debug-box"><pre>{log_text}</pre></div>', unsafe_allow_html=True)
        else:
            st.error("❌ Nenhum dado!")

st.markdown("<br><br><p style='text-align:right; font-family:serif; font-style:italic; color:#BFAF83;'>🥇 Melhor Programador - Edson Medeiros</p>", unsafe_allow_html=True)
