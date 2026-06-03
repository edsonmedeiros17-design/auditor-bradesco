import streamlit as st
import pdfplumber
import pandas as pd
import re
from datetime import datetime
import io
from typing import List, Dict, Optional, Tuple

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from openpyxl.utils import get_column_letter
except ImportError:
    st.error("Erro: openpyxl não instalada")

st.set_page_config(page_title="Edson Medeiros | Consultoria de Ativos", layout="wide", page_icon="⚖️")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;600&display=swap');
    .stApp { background-color: #0E1117; color: #FFFFFF; font-family: 'Inter', sans-serif; }
    .main-title { font-family: 'Playfair Display', serif; font-size: 3rem; color: #BFAF83; text-align: center; margin-bottom: 0; }
    .sub-title { text-align: center; color: #64748B; letter-spacing: 2px; text-transform: uppercase; font-size: 0.9rem; margin-bottom: 40px; }
    .metric-card { background: rgba(255,255,255,0.05); border: 1px solid #BFAF83; border-radius: 10px; padding: 20px; text-align: center; }
    .debug-box { background: rgba(50, 150, 200, 0.1); border: 1px solid #3296C8; border-radius: 8px; padding: 15px; margin: 10px 0; font-size: 9px; max-height: 800px; overflow-y: auto; font-family: monospace; }
    .success { color: #00FF00; }
    .error { color: #FF0000; }
    .warning { color: #FFFF00; }
</style>
""", unsafe_allow_html=True)

# === RÚBRICAS COM MÚLTIPLAS VARIAÇÕES ===
RUBRICAS_MESTRE = {
    "CESTA": [
        r"CESTA",
        r"CESTA\s+[A-Z]",
        r"CESTA\s+[A-Z0-9\s\.]+"
    ],
    "PACOTE": [
        r"PACOTE",
        r"PACOTE\s+[A-Z]"
    ],
    "MORA DE OPERAÇÃO": [
        r"MORA\s+DE\s+OPERAÇÃO",
        r"MORA\s+OPERACAO",
        r"MORA\s+OPER"
    ],
    "MORA CREDITO PESSOAL": [
        r"MORA\s+CREDITO\s+PESSOAL",
        r"MORA\s+CRED\s+PESS",
        r"MORA.*CREDITO.*PESSOAL"
    ],
    "MORA OPERACAO DE CREDITO": [
        r"MORA\s+OPERACAO\s+DE\s+CREDITO",
        r"MORA\s+OPER\s+CRED",
        r"MORA.*OPERACAO.*CREDITO"
    ],
    "BX": [
        r"\bBX\b",
        r"BX\s+[0-9]"
    ],
    "PARCELA CREDITO PESSOAL": [
        r"PARCELA\s+CREDITO\s+PESSOAL",
        r"PARC\s+CRED\s+PESS",
        r"PARC\s+[0-9]",
        r"PARCELA.*CREDITO.*PESSOAL"
    ],
    "GASTOS CARTAO DE CREDITO": [
        r"GASTOS\s+CARTAO\s+DE\s+CREDITO",
        r"CARTAO\s+DE\s+CREDITO",
        r"GASTOS\s+CARTAO",
        r"CARTAO.*CREDITO"
    ],
    "SEGURO": [
        r"SEGURO",
        r"SEGURADORA",
        r"SEG\b"
    ],
    "ADIANT": [
        r"ADIANT",
        r"ADIANTAMENTO",
        r"ADIANT\s+[A-Z]"
    ],
    "APLIC": [
        r"APLICACAO",
        r"APLIC\b",
        r"APLIC\s+[A-Z]"
    ],
    "ENCARGOS": [
        r"ENCARGOS",
        r"ENCARGO",
        r"ENC\s+LIMITE",
        r"LIMITE\s+DE\s+CRED",
        r"ENCARGO\s+[0-9]"
    ],
    "ANUIDADE": [
        r"ANUIDADE",
        r"CARTAO\s+CREDITO\s+ANUIDADE",
        r"ANUIDADE\s+[A-Z]"
    ],
    "OPERACOES VENCIDAS": [
        r"OPERACOES\s+VENCIDAS",
        r"OPERAÇÕES\s+VENCIDAS",
        r"OPER\s+VENCIDAS"
    ],
    "DIV. EM ATRASO": [
        r"DIV\.\s+EM\s+ATRASO",
        r"DIVIDA\s+EM\s+ATRASO",
        r"DIV\s+EM\s+ATRASO"
    ]
}

TERMOS_EXCLUSAO = r"TRANSF|SALDO|SDO|TRANSFERENCIA|SALARIO|DEPOSITO|CREDITO\s+DEPOSITO|CREDITO\s+JUROS"

if 'rubricas_selecionadas' not in st.session_state:
    st.session_state.rubricas_selecionadas = {r: True for r in RUBRICAS_MESTRE.keys()}
if 'debug_mode' not in st.session_state:
    st.session_state.debug_mode = False
if 'log_debug' not in st.session_state:
    st.session_state.log_debug = []


# === PROCESSADOR ULTRA-PRECISO ===
class ProcessadorExtratoMestre:
    """
    Processador MASTER para extratos bancários.
    Estratégia: BUSCA AGRESSIVA mas INTELIGENTE
    """
    
    @staticmethod
    def limpar_linha(texto: str) -> str:
        """Remove espaços extras mantendo a estrutura."""
        return ' '.join(texto.split())
    
    @staticmethod
    def extrair_data_precisa(texto: str) -> Optional[str]:
        """Extrai data com PRECISÃO MÁXIMA."""
        # Padrão: dd/mm/yyyy ou dd/mm/yy com limites de palavra
        pattern = r'\b(\d{2}/\d{2}/\d{2,4})\b'
        match = re.search(pattern, texto)
        
        if not match:
            return None
        
        data_str = match.group(1)
        partes = data_str.split('/')
        
        try:
            dia, mes, ano = partes
            dia_int = int(dia)
            mes_int = int(mes)
            ano_int = int(ano)
            
            # Valida valores
            if not (1 <= dia_int <= 31 and 1 <= mes_int <= 12):
                return None
            
            # Adiciona século
            if ano_int < 100:
                ano_int = 2000 + ano_int
            
            # Valida data real
            datetime(ano_int, mes_int, dia_int)
            
            return f"{dia}/{mes}/{str(ano_int)}"
        except:
            return None
    
    @staticmethod
    def extrair_valor_preciso(texto: str) -> Optional[str]:
        """Extrai valor monetário com PRECISÃO MÁXIMA."""
        # Padrão brasileiro: 1,23 | 1.234,56 | 1.234.567,89
        pattern = r'\b(\d{1,3}(?:\.\d{3})*,\d{2})\b'
        
        matches = list(re.finditer(pattern, texto))
        
        if not matches:
            return None
        
        # Filtra porcentagens e pega o ÚLTIMO valor (geralmente coluna de débito)
        valores_validos = []
        for match in matches:
            valor = match.group(1)
            pos_final = match.end()
            
            # Verifica contexto após o valor
            if pos_final < len(texto):
                prox_chars = texto[pos_final:pos_final+3]
                if '%' in prox_chars:
                    continue
            
            valores_validos.append(valor)
        
        if not valores_validos:
            return None
        
        # Retorna último valor (coluna de débito)
        return valores_validos[-1]
    
    @staticmethod
    def detectar_rubrica_agressiva(texto: str, rubricas_alvo: List[str]) -> Optional[str]:
        """
        Detecta rubrica com BUSCA AGRESSIVA.
        - Tenta cada variação de padrão
        - Ignora % (são taxas, não débitos)
        """
        texto_up = ProcessadorExtratoMestre.limpar_linha(texto).upper()
        
        # Não processa porcentagens (são informativas, não débitos)
        if '%' in texto_up and len(texto) < 100:
            return None
        
        # Tenta encontrar QUALQUER rubrica
        for nome_rubrica in rubricas_alvo:
            padroes = RUBRICAS_MESTRE[nome_rubrica]
            
            for padrao in padroes:
                if re.search(padrao, texto_up):
                    return nome_rubrica
        
        return None
    
    @staticmethod
    def eh_linha_separadora(texto: str) -> bool:
        """Detecta linhas separadoras (apenas dashes)."""
        texto_clean = texto.strip()
        return all(c in '-_= ' for c in texto_clean) and len(texto_clean) > 3
    
    @staticmethod
    def eh_linha_cabecalho(texto: str) -> bool:
        """Detecta linha de cabeçalho da tabela."""
        palavras_cabecalho = ['Data', 'Histórico', 'Docto', 'Débito', 'Crédito', 'Saldo']
        return any(palavra in texto for palavra in palavras_cabecalho)


class AnalisadorExtratoMestre:
    """
    Analisador MASTER com lógica robusta.
    """
    
    def __init__(self, rubricas_alvo: List[str]):
        self.rubricas_alvo = rubricas_alvo
        self.log = []
        self.resultados = []
    
    def adicionar_log(self, msg: str, tipo: str = "info"):
        """Adiciona log com tipo."""
        self.log.append(msg)
    
    def processar_pdf(self, arquivo) -> List[Dict]:
        """
        Processa PDF com estratégia de leitura completa.
        """
        try:
            with pdfplumber.open(arquivo) as pdf:
                contexto_data = None
                linhas_buffer = []
                
                for num_pagina, page in enumerate(pdf.pages):
                    # Extrai texto com pdfplumber
                    texto = page.extract_text(x_tolerance=2, y_tolerance=2)
                    if not texto:
                        self.adicionar_log(f"[PÁG {num_pagina + 1}] Vazia", "warning")
                        continue
                    
                    linhas = texto.split('\n')
                    self.adicionar_log(f"\n[PÁG {num_pagina + 1}] {len(linhas)} linhas extraídas", "info")
                    
                    for idx, linha in enumerate(linhas):
                        linha_limpa = ProcessadorExtratoMestre.limpar_linha(linha)
                        
                        if not linha_limpa or len(linha_limpa) < 3:
                            continue
                        
                        # Ignora cabeçalho e separadores
                        if ProcessadorExtratoMestre.eh_linha_cabecalho(linha_limpa):
                            self.adicionar_log(f"  [L{idx}] ← Cabeçalho", "warning")
                            continue
                        
                        if ProcessadorExtratoMestre.eh_linha_separadora(linha_limpa):
                            self.adicionar_log(f"  [L{idx}] ← Separador", "warning")
                            continue
                        
                        # ===== ETAPA 1: PROCURA DATA =====
                        data_encontrada = ProcessadorExtratoMestre.extrair_data_precisa(linha_limpa)
                        
                        if data_encontrada:
                            # Se tinha buffer, processa antes
                            if linhas_buffer:
                                self._processar_buffer(linhas_buffer, contexto_data, num_pagina)
                                linhas_buffer = []
                            
                            contexto_data = data_encontrada
                            self.adicionar_log(f"  [L{idx}] 📅 DATA: {contexto_data}", "info")
                            continue
                        
                        # ===== ETAPA 2: VERIFICA EXCLUSÃO =====
                        if re.search(TERMOS_EXCLUSAO, linha_limpa.upper()):
                            self.adicionar_log(f"  [L{idx}] ❌ Exclusão detectada", "warning")
                            contexto_data = None
                            linhas_buffer = []
                            continue
                        
                        # ===== ETAPA 3: ACUMULA LINHAS NO BUFFER =====
                        linhas_buffer.append((idx, linha_limpa, num_pagina))
                    
                    # Processa buffer final da página
                    if linhas_buffer:
                        self._processar_buffer(linhas_buffer, contexto_data, num_pagina)
                        linhas_buffer = []
                
                self.adicionar_log(f"\n✅ PROCESSAMENTO CONCLUÍDO: {len(self.resultados)} registros extraídos", "info")
        
        except Exception as e:
            self.adicionar_log(f"🔴 ERRO CRÍTICO: {str(e)}", "error")
            st.error(f"❌ Erro: {str(e)}")
        
        return self.resultados
    
    def _processar_buffer(self, linhas_buffer: List[Tuple], data_contexto: str, pagina: int):
        """Processa buffer acumulado de linhas."""
        
        # Tenta encontrar QUALQUER rubrica no buffer
        for idx, linha, pag in linhas_buffer:
            rubrica = ProcessadorExtratoMestre.detectar_rubrica_agressiva(linha, self.rubricas_alvo)
            
            if rubrica:
                # Tenta extrair valor dessa linha
                valor = ProcessadorExtratoMestre.extrair_valor_preciso(linha)
                
                # Se não encontrou valor nessa linha, procura nas proximidades
                if not valor and linhas_buffer:
                    for idx2, linha2, _ in linhas_buffer:
                        valor_temp = ProcessadorExtratoMestre.extrair_valor_preciso(linha2)
                        if valor_temp:
                            valor = valor_temp
                            break
                
                if valor:
                    self.adicionar_log(f"  [L{idx}] ✅ {rubrica} | VALOR: {valor} | DATA: {data_contexto}", "info")
                    self.resultados.append({
                        "PÁGINA": pag + 1,
                        "LINHA": idx,
                        "RUBRICA": rubrica,
                        "VALOR": valor,
                        "DATA": data_contexto if data_contexto else "SEM_DATA",
                        "TEXTO": linha[:100]
                    })
                else:
                    self.adicionar_log(f"  [L{idx}] ⚠️  {rubrica} encontrada mas SEM VALOR", "warning")


def converter_valor_para_float(valor_str: str) -> float:
    """Converte seguro para float."""
    if not valor_str or valor_str == "SEM_DATA":
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
        
        ws.merge_cells('A1:E1')
        ws['A1'] = f"VALORES - {rubrica_nome}"
        ws['A1'].font = font_title
        ws['A1'].fill = fill_blue
        ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
        
        meses = ["JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"]
        
        ws['A2'] = "MÊS"
        ws['A2'].font = font_header
        ws['A2'].fill = fill_blue
        
        anos = sorted(agrupado['ANO'].unique())
        if not anos:
            anos = [datetime.now().year]
        
        for idx, ano in enumerate(anos):
            col = idx + 2
            ws.cell(row=2, column=col, value=int(ano)).font = font_header
            ws.cell(row=2, column=col).fill = fill_blue
            ws.cell(row=2, column=col).alignment = Alignment(horizontal='center')
        
        for m_idx, mes in enumerate(meses):
            row = m_idx + 3
            ws.cell(row=row, column=1, value=mes).font = font_header
            ws.cell(row=row, column=1).fill = fill_blue
            
            for a_idx, ano in enumerate(anos):
                col = a_idx + 2
                val = agrupado[(agrupado['ANO'] == ano) & (agrupado['MES_NUM'] == m_idx + 1)]['V_NUM'].sum()
                
                cell = ws.cell(row=row, column=col)
                if val > 0:
                    cell.value = val
                    cell.number_format = '"R$ " #,##0.00'
                
                cell.fill = fill_peach
                cell.border = border
                cell.alignment = Alignment(horizontal='right')
        
        row_anual = 15
        ws.cell(row=row_anual, column=1, value="ANUAL").font = font_header
        ws.cell(row=row_anual, column=1).fill = fill_blue
        
        for idx, ano in enumerate(anos):
            col = idx + 2
            col_letter = get_column_letter(col)
            ws.cell(row=row_anual, column=col, value=f"=SUM({col_letter}3:{col_letter}14)")
            ws.cell(row=row_anual, column=col).number_format = '"R$ " #,##0.00'
            ws.cell(row=row_anual, column=col).font = font_header
            ws.cell(row=row_anual, column=col).fill = fill_total
        
        row_total = 16
        ws.cell(row=row_total, column=1, value="TOTAL").font = font_header
        ws.cell(row=row_total, column=1).fill = fill_blue
        
        last_col = get_column_letter(len(anos) + 1)
        ws.merge_cells(start_row=row_total, start_column=2, end_row=row_total, end_column=len(anos)+1)
        ws.cell(row=row_total, column=2, value=f"=SUM(B{row_anual}:{last_col}{row_anual})")
        ws.cell(row=row_total, column=2).number_format = '"R$ " #,##0.00'
        ws.cell(row=row_total, column=2).font = font_header
        ws.cell(row=row_total, column=2).fill = fill_total
        
        ws.column_dimensions['A'].width = 15
        for i in range(2, len(anos) + 2):
            ws.column_dimensions[get_column_letter(i)].width = 15
        
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output.getvalue()
    except Exception as e:
        return None


# === DASHBOARD ===
st.markdown('<h1 class="main-title">⚖️ Consultoria de Ativos</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">🔬 Auditoria com Busca Agressiva Inteligente</p>', unsafe_allow_html=True)

st.sidebar.markdown("### ⚙️ CONFIGURAÇÃO")

modo = st.sidebar.radio("Formato:", ["DATA_SUPERIOR", "DATA_INFERIOR"], format_func=lambda x: "📅 " + x.replace("_", " "))

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 RUBRICAS")

col_b1, col_b2 = st.sidebar.columns(2)
with col_b1:
    if st.button("✅ TODAS", use_container_width=True):
        for r in RUBRICAS_MESTRE.keys():
            st.session_state.rubricas_selecionadas[r] = True
        st.rerun()

with col_b2:
    if st.button("❌ NENHUMA", use_container_width=True):
        for r in RUBRICAS_MESTRE.keys():
            st.session_state.rubricas_selecionadas[r] = False
        st.rerun()

st.sidebar.markdown("")

selecionadas = []
for r in sorted(RUBRICAS_MESTRE.keys()):
    if st.sidebar.checkbox(r, value=st.session_state.rubricas_selecionadas.get(r, True), key=f"rb_{r}"):
        selecionadas.append(r)
        st.session_state.rubricas_selecionadas[r] = True
    else:
        st.session_state.rubricas_selecionadas[r] = False

st.sidebar.markdown("---")
st.session_state.debug_mode = st.sidebar.checkbox("🐛 DEBUG", value=st.session_state.debug_mode)

upload = st.file_uploader("📂 PDF", type=["pdf"])

if upload:
    with st.spinner("⚡ PROCESSANDO..."):
        analisador = AnalisadorExtratoMestre(selecionadas)
        dados = analisador.processar_pdf(upload)
        st.session_state.log_debug = analisador.log
        
        if dados:
            df = pd.DataFrame(dados)
            df['V_NUM'] = df['VALOR'].apply(converter_valor_para_float)
            df_valido = df[(df['V_NUM'] > 0) & (df['DATA'] != "SEM_DATA")].copy()
            
            if df_valido.empty:
                st.error("❌ Nenhum valor encontrado!")
            else:
                df_valido['DT'] = pd.to_datetime(df_valido['DATA'], format='%d/%m/%Y', errors='coerce')
                df_valido = df_valido.dropna(subset=['DT']).sort_values('DT')
                
                total = df_valido['V_NUM'].sum()
                
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown(f'<div class="metric-card"><h4>💰 TOTAL</h4><h2 style="color:#BFAF83;">R$ {total:,.2f}</h2></div>', unsafe_allow_html=True)
                with c2:
                    st.markdown(f'<div class="metric-card"><h4>📝 QTDE</h4><h2 style="color:#BFAF83;">{len(df_valido)}</h2></div>', unsafe_allow_html=True)
                with c3:
                    st.markdown(f'<div class="metric-card"><h4>💼 TIPOS</h4><h2 style="color:#BFAF83;">{df_valido["RUBRICA"].nunique()}</h2></div>', unsafe_allow_html=True)
                
                st.markdown('<h2 style="color:#BFAF83; text-align:center; margin-top:30px;">📥 Downloads</h2>', unsafe_allow_html=True)
                
                cats = sorted(df_valido['RUBRICA'].unique())
                cols = st.columns(min(4, len(cats)))
                
                for idx, cat in enumerate(cats):
                    df_cat = df_valido[df_valido['RUBRICA'] == cat]
                    excel = gerar_excel_calculos(df_cat, cat)
                    if excel:
                        with cols[idx % len(cols)]:
                            st.download_button(f"📊 {cat}", excel, f"{cat.replace(' ', '_')}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
                
                st.markdown('<h3 style="color:#BFAF83; text-align:center; margin-top:30px;">📋 Dados</h3>', unsafe_allow_html=True)
                
                df_exib = df_valido[['DATA', 'RUBRICA', 'VALOR', 'TEXTO']].copy()
                df_exib.columns = ['DATA', 'RUBRICA', 'VALOR', 'DESCRIÇÃO']
                st.dataframe(df_exib, use_container_width=True, hide_index=True)
                
                if st.session_state.debug_mode:
                    st.markdown("---")
                    st.markdown("### 🐛 LOG")
                    log_text = "\n".join(st.session_state.log_debug)
                    st.markdown(f'<div class="debug-box">{log_text}</div>', unsafe_allow_html=True)
        else:
            st.warning("⚠️ Nenhum registro extraído")

st.markdown("<br><br><p style='text-align:right; font-family:serif; font-style:italic; color:#BFAF83;'>Edson Medeiros</p>", unsafe_allow_html=True)
