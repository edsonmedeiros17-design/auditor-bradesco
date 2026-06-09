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
st.set_page_config(page_title="Edson Medeiros | Consultoria e Compliance", layout="wide", page_icon="⚖️")

st.markdown("""
<style>
    /* ── TIPOGRAFIA ───────────────────────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400;1,600&family=Inter:wght@300;400;500;600&display=swap');

    /* ── RESET E BASE ─────────────────────────────────────────────────────────── */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        -webkit-font-smoothing: antialiased;
    }
    .stApp {
        background-color: #101418;
        color: #E8DCC8;
    }

    /* ── HEADER PRINCIPAL ─────────────────────────────────────────────────────── */
    .em-header-wrap {
        text-align: center;
        padding: 52px 0 36px;
        position: relative;
    }
    .em-header-wrap::before,
    .em-header-wrap::after {
        content: '';
        position: absolute;
        top: 50%;
        width: calc(50% - 220px);
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(197,165,102,0.45));
    }
    .em-header-wrap::before { left: 0; transform: translateY(-50%) scaleX(-1); }
    .em-header-wrap::after  { right: 0; transform: translateY(-50%); }

    .em-eyebrow {
        font-family: 'Inter', sans-serif;
        font-size: 0.62rem;
        font-weight: 500;
        letter-spacing: 5px;
        text-transform: uppercase;
        color: #C5A566;
        margin-bottom: 8px;
        opacity: 0.85;
    }
    .em-name {
        font-family: 'Cormorant Garamond', serif;
        font-size: 3.6rem;
        font-weight: 600;
        line-height: 1.0;
        color: #E8DCC8;
        letter-spacing: 0.5px;
        margin: 0;
    }
    .em-name span {
        color: #C5A566;
    }
    .em-subtitle {
        font-family: 'Cormorant Garamond', serif;
        font-size: 1.0rem;
        font-weight: 400;
        font-style: italic;
        color: rgba(197,165,102,0.7);
        letter-spacing: 3px;
        margin-top: 6px;
        text-transform: uppercase;
    }
    .em-ornament {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 14px;
        margin-top: 22px;
    }
    .em-ornament-line {
        width: 80px;
        height: 1px;
        background: linear-gradient(90deg, transparent, #C5A566);
    }
    .em-ornament-line.rev {
        background: linear-gradient(90deg, #C5A566, transparent);
    }
    .em-ornament-diamond {
        color: #C5A566;
        font-size: 0.6rem;
        opacity: 0.9;
    }

    /* ── DIVISOR DE SEÇÃO ─────────────────────────────────────────────────────── */
    .em-divider {
        display: flex;
        align-items: center;
        gap: 12px;
        margin: 32px 0 24px;
    }
    .em-divider-line {
        flex: 1;
        height: 1px;
        background: rgba(197,165,102,0.2);
    }
    .em-divider-label {
        font-family: 'Inter', sans-serif;
        font-size: 0.58rem;
        font-weight: 600;
        letter-spacing: 4px;
        text-transform: uppercase;
        color: rgba(197,165,102,0.6);
        white-space: nowrap;
    }

    /* ── UPLOAD ZONE ──────────────────────────────────────────────────────────── */
    [data-testid="stFileUploader"] {
        border: 1px solid rgba(197,165,102,0.3) !important;
        border-radius: 0 !important;
        background: rgba(197,165,102,0.03) !important;
        padding: 4px !important;
        transition: border-color 0.3s ease;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: rgba(197,165,102,0.6) !important;
    }
    [data-testid="stFileUploadDropzone"] {
        background: transparent !important;
        border: 1px dashed rgba(197,165,102,0.35) !important;
        border-radius: 0 !important;
        padding: 28px !important;
    }
    [data-testid="stFileUploaderDropzoneInstructions"] span,
    [data-testid="stFileUploaderDropzoneInstructions"] small {
        color: rgba(197,165,102,0.7) !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.82rem !important;
        letter-spacing: 0.5px;
    }
    [data-testid="stFileUploadDropzone"] button {
        background: transparent !important;
        border: 1px solid rgba(197,165,102,0.5) !important;
        color: #C5A566 !important;
        border-radius: 0 !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.75rem !important;
        letter-spacing: 1.5px !important;
        text-transform: uppercase !important;
        padding: 6px 18px !important;
        transition: all 0.2s ease;
    }
    [data-testid="stFileUploadDropzone"] button:hover {
        background: rgba(197,165,102,0.1) !important;
    }

    /* ── CARDS DE MÉTRICAS ────────────────────────────────────────────────────── */
    .metric-card {
        background: #1C2128;
        border-top: 2px solid #C5A566;
        border-left: 1px solid rgba(197,165,102,0.15);
        border-right: 1px solid rgba(197,165,102,0.15);
        border-bottom: 1px solid rgba(197,165,102,0.15);
        border-radius: 0;
        padding: 28px 24px;
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, #C5A566, transparent);
    }
    .metric-card h4 {
        font-family: 'Inter', sans-serif;
        font-size: 0.62rem;
        font-weight: 600;
        letter-spacing: 3.5px;
        text-transform: uppercase;
        color: rgba(197,165,102,0.65);
        margin: 0 0 12px 0;
    }
    .metric-card h2 {
        font-family: 'Cormorant Garamond', serif;
        font-size: 2.6rem;
        font-weight: 600;
        color: #C5A566;
        margin: 0;
        line-height: 1;
    }

    /* ── SEÇÃO DE DOWNLOADS ───────────────────────────────────────────────────── */
    .em-section-title {
        font-family: 'Cormorant Garamond', serif;
        font-size: 1.5rem;
        font-weight: 500;
        color: #E8DCC8;
        letter-spacing: 1px;
        text-align: center;
        margin: 0;
    }
    .em-section-note {
        font-family: 'Inter', sans-serif;
        font-size: 0.78rem;
        color: rgba(232,220,200,0.45);
        text-align: center;
        letter-spacing: 0.3px;
        margin-top: 4px;
        margin-bottom: 20px;
    }

    /* ── BOTÕES DE DOWNLOAD ───────────────────────────────────────────────────── */
    [data-testid="stDownloadButton"] > button {
        background: transparent !important;
        border: 1px solid rgba(197,165,102,0.4) !important;
        color: rgba(197,165,102,0.85) !important;
        border-radius: 0 !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.72rem !important;
        font-weight: 500 !important;
        letter-spacing: 1.8px !important;
        text-transform: uppercase !important;
        padding: 8px 20px !important;
        transition: all 0.25s ease;
        width: 100% !important;
    }
    [data-testid="stDownloadButton"] > button:hover {
        background: rgba(197,165,102,0.08) !important;
        border-color: #C5A566 !important;
        color: #C5A566 !important;
        box-shadow: 0 0 18px rgba(197,165,102,0.08) !important;
    }

    /* ── DATAFRAME ────────────────────────────────────────────────────────────── */
    [data-testid="stDataFrame"] {
        border: 1px solid rgba(197,165,102,0.2) !important;
        border-radius: 0 !important;
    }
    [data-testid="stDataFrame"] th {
        background: #1C2128 !important;
        color: rgba(197,165,102,0.8) !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.68rem !important;
        font-weight: 600 !important;
        letter-spacing: 2.5px !important;
        text-transform: uppercase !important;
        border-bottom: 1px solid rgba(197,165,102,0.25) !important;
    }
    [data-testid="stDataFrame"] td {
        font-family: 'Inter', sans-serif !important;
        font-size: 0.8rem !important;
        color: #E8DCC8 !important;
        border-color: rgba(197,165,102,0.08) !important;
    }

    /* ── SPINNER ──────────────────────────────────────────────────────────────── */
    [data-testid="stSpinner"] p {
        color: rgba(197,165,102,0.7) !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.8rem !important;
        letter-spacing: 1px;
    }

    /* ── INFO BOX ─────────────────────────────────────────────────────────────── */
    [data-testid="stAlert"] {
        background: rgba(197,165,102,0.06) !important;
        border: 1px solid rgba(197,165,102,0.3) !important;
        border-radius: 0 !important;
        color: rgba(197,165,102,0.8) !important;
    }

    /* ── SIDEBAR — BASE ───────────────────────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: #0A0D10;
        border-right: 1px solid rgba(197,165,102,0.14);
    }
    [data-testid="stSidebar"] > div:first-child { padding-top: 0; }

    /* ── SIDEBAR HEADER ─────────────────────────────────────────────────────── */
    .sb-header {
        padding: 22px 16px 16px;
        border-bottom: 1px solid rgba(197,165,102,0.12);
        margin-bottom: 0;
    }
    .sb-eyebrow {
        font-family: 'Inter', sans-serif;
        font-size: 0.55rem;
        font-weight: 600;
        letter-spacing: 3.5px;
        text-transform: uppercase;
        color: rgba(197,165,102,0.5);
        margin-bottom: 3px;
    }
    .sb-title {
        font-family: 'Cormorant Garamond', serif;
        font-size: 1.15rem;
        font-weight: 600;
        color: #E8DCC8;
        letter-spacing: 0.5px;
        margin: 0;
        line-height: 1.2;
    }
    .sb-title span { color: #C5A566; }

    /* ── CONTROLES MARCAR/DESMARCAR ─────────────────────────────────────────── */
    .sb-controls {
        display: flex;
        gap: 0;
        margin: 12px 16px 8px;
        border: 1px solid rgba(197,165,102,0.18);
    }
    [data-testid="stSidebar"] .stButton > button {
        border-radius: 0 !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.60rem !important;
        font-weight: 600 !important;
        letter-spacing: 2px !important;
        text-transform: uppercase !important;
        padding: 6px 0 !important;
        width: 100% !important;
        transition: all 0.2s ease !important;
        border: none !important;
    }
    [data-testid="stSidebar"] .stButton:nth-of-type(1) > button {
        background: rgba(197,165,102,0.1) !important;
        color: #C5A566 !important;
        border-right: 1px solid rgba(197,165,102,0.18) !important;
    }
    [data-testid="stSidebar"] .stButton:nth-of-type(1) > button:hover {
        background: rgba(197,165,102,0.2) !important;
        color: #D4B87A !important;
    }
    [data-testid="stSidebar"] .stButton:nth-of-type(2) > button {
        background: transparent !important;
        color: rgba(232,220,200,0.28) !important;
    }
    [data-testid="stSidebar"] .stButton:nth-of-type(2) > button:hover {
        background: rgba(255,255,255,0.04) !important;
        color: rgba(232,220,200,0.55) !important;
    }

    /* ── LISTA DE RUBRICAS ───────────────────────────────────────────────────── */
    [data-testid="stSidebar"] .stCheckbox {
        margin: 0 !important;
        padding: 0 !important;
        position: relative !important;
    }
    [data-testid="stSidebar"] .stCheckbox > label > div:first-child {
        display: none !important;
    }
    [data-testid="stSidebar"] .stCheckbox > label {
        display: flex !important;
        align-items: center !important;
        gap: 0 !important;
        width: 100% !important;
        padding: 8px 16px !important;
        margin: 0 !important;
        cursor: pointer !important;
        position: relative !important;
        border-left: 2px solid transparent !important;
        transition: all 0.18s ease !important;
        background: transparent !important;
    }
    [data-testid="stSidebar"] .stCheckbox > label:hover {
        background: rgba(197,165,102,0.05) !important;
        border-left-color: rgba(197,165,102,0.3) !important;
    }
    [data-testid="stSidebar"] .stCheckbox > label > div:last-child,
    [data-testid="stSidebar"] .stCheckbox > label > span {
        font-family: 'Inter', sans-serif !important;
        font-size: 0.73rem !important;
        font-weight: 400 !important;
        color: rgba(232,220,200,0.38) !important;
        letter-spacing: 0.8px !important;
        text-transform: uppercase !important;
        line-height: 1 !important;
    }
    [data-testid="stSidebar"] input[type="checkbox"]:checked ~ div,
    [data-testid="stSidebar"] input[type="checkbox"]:checked + div + div {
        color: #C5A566 !important;
    }
    [data-testid="stSidebar"] .stCheckbox:has(input:checked) > label {
        border-left-color: #C5A566 !important;
        background: rgba(197,165,102,0.06) !important;
    }
    [data-testid="stSidebar"] .stCheckbox:has(input:checked) > label > div:last-child,
    [data-testid="stSidebar"] .stCheckbox:has(input:checked) > label > span {
        color: #C5A566 !important;
        font-weight: 500 !important;
    }

    /* ── SEPARADOR ANTES DO CONTADOR ─────────────────────────────────────────── */
    .sidebar-divider {
        border: none;
        border-top: 1px solid rgba(197,165,102,0.10);
        margin: 8px 0 0;
    }

    /* ── CONTADOR ────────────────────────────────────────────────────────────── */
    .rubrica-count {
        padding: 8px 16px 14px;
        font-size: 0.58rem;
        font-family: 'Inter', sans-serif;
        letter-spacing: 2px;
        text-transform: uppercase;
    }

    /* ── FOOTER DE CONTATO ────────────────────────────────────────────────────── */
    .em-footer {
        margin-top: 60px;
        padding-top: 28px;
        border-top: 1px solid rgba(197,165,102,0.18);
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 10px;
    }
    .em-footer-name {
        font-family: 'Cormorant Garamond', serif;
        font-size: 1.25rem;
        font-weight: 600;
        font-style: italic;
        color: #C5A566;
        letter-spacing: 1px;
    }
    .em-footer-contacts {
        display: flex;
        gap: 24px;
        flex-wrap: wrap;
        justify-content: center;
    }
    .em-footer-contact {
        font-family: 'Inter', sans-serif;
        font-size: 0.72rem;
        color: rgba(197,165,102,0.55);
        letter-spacing: 1px;
    }
    .em-footer-contact a {
        color: rgba(197,165,102,0.55);
        text-decoration: none;
        transition: color 0.2s;
    }
    .em-footer-contact a:hover { color: #C5A566; }
    .em-whatsapp-btn {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: transparent;
        border: 1px solid rgba(197,165,102,0.45);
        color: #C5A566;
        font-family: 'Inter', sans-serif;
        font-size: 0.70rem;
        font-weight: 600;
        letter-spacing: 2px;
        text-transform: uppercase;
        padding: 9px 22px;
        text-decoration: none;
        transition: all 0.25s ease;
        cursor: pointer;
        margin-top: 6px;
    }
    .em-whatsapp-btn:hover {
        background: rgba(197,165,102,0.1);
        border-color: #C5A566;
        color: #C5A566;
        text-decoration: none;
    }

    /* ── SCROLLBAR ────────────────────────────────────────────────────────────── */
    ::-webkit-scrollbar { width: 4px; height: 4px; }
    ::-webkit-scrollbar-track { background: #101418; }
    ::-webkit-scrollbar-thumb { background: rgba(197,165,102,0.3); border-radius: 0; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(197,165,102,0.55); }
</style>
""", unsafe_allow_html=True)

# --- 1b. LÓGICA DE LOGIN ---
def _check_login(email: str, senha: str) -> bool:
    return email.strip() == "edson.senabr@gmail.com" and senha == "Edsonsena14"

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;0,700;1,400&family=Inter:wght@400;500;600&display=swap');

    header, footer,
    [data-testid="stSidebar"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"] { display: none !important; }

    .stApp {
        background: #060A0D !important;
        background-image:
            radial-gradient(circle, rgba(197,165,102,0.055) 1px, transparent 1px) !important;
        background-size: 30px 30px !important;
    }
    .stApp::after {
        content: '';
        position: fixed;
        inset: 0;
        background: radial-gradient(ellipse at 50% 50%,
            transparent 30%, rgba(6,10,13,0.78) 100%);
        pointer-events: none;
        z-index: 0;
    }

    .block-container {
        max-width: 480px !important;
        padding: 0 24px !important;
        margin: 0 auto !important;
        position: relative;
        z-index: 1;
        padding-top: max(60px, 10vh) !important;
    }

    .lx-logo {
        text-align: center;
        margin-bottom: 10px;
    }
    .lx-eyebrow {
        font-family: 'Inter', sans-serif;
        font-size: 0.52rem;
        font-weight: 600;
        letter-spacing: 5.5px;
        text-transform: uppercase;
        color: rgba(197,165,102,0.45);
        margin-bottom: 12px;
    }
    .lx-monogram {
        font-family: 'Cormorant Garamond', serif;
        font-size: 3.8rem;
        font-weight: 300;
        color: #C5A566;
        line-height: 1;
        letter-spacing: 8px;
        margin-bottom: 8px;
    }
    .lx-name {
        font-family: 'Cormorant Garamond', serif;
        font-size: 1.5rem;
        font-weight: 600;
        color: #E8DCC8;
        letter-spacing: 4px;
        text-transform: uppercase;
        line-height: 1;
    }
    .lx-tagline {
        font-family: 'Cormorant Garamond', serif;
        font-size: 0.8rem;
        font-style: italic;
        color: rgba(197,165,102,0.42);
        letter-spacing: 2px;
        margin-top: 5px;
    }

    .lx-ornament {
        display: flex;
        align-items: center;
        gap: 12px;
        margin: 22px 0 20px;
    }
    .lx-line {
        flex: 1;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(197,165,102,0.28));
    }
    .lx-line-rev {
        flex: 1;
        height: 1px;
        background: linear-gradient(90deg, rgba(197,165,102,0.28), transparent);
    }
    .lx-diamond { font-size: 0.45rem; color: rgba(197,165,102,0.45); }

    .lx-robot {
        text-align: center;
        margin-bottom: 14px;
    }
    .lx-robot-label {
        font-family: 'Inter', sans-serif;
        font-size: 0.50rem;
        font-weight: 600;
        letter-spacing: 4.5px;
        text-transform: uppercase;
        color: rgba(197,165,102,0.32);
        margin-bottom: 6px;
    }
    .lx-robot-title {
        font-family: 'Cormorant Garamond', serif;
        font-size: 2.6rem;
        font-weight: 300;
        color: #DDD3BE;
        letter-spacing: 5px;
        line-height: 1;
    }
    .lx-robot-x {
        font-weight: 700;
        color: #C5A566;
        font-size: 3rem;
        letter-spacing: 0;
    }

    .lx-welcome {
        font-family: 'Cormorant Garamond', serif;
        font-size: 0.92rem;
        font-style: italic;
        color: rgba(232,220,200,0.35);
        text-align: center;
        letter-spacing: 0.4px;
        line-height: 1.65;
        margin-bottom: 28px;
    }

    [data-testid="stForm"] {
        background: rgba(197,165,102,0.03) !important;
        border: 1px solid rgba(197,165,102,0.16) !important;
        border-radius: 0 !important;
        padding: 0 !important;
    }
    [data-testid="stForm"] input {
        background: transparent !important;
        border: none !important;
        border-bottom: 1px solid rgba(197,165,102,0.18) !important;
        border-radius: 0 !important;
        color: #E8DCC8 !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.85rem !important;
        letter-spacing: 0.8px !important;
        padding: 10px 20px !important;
        caret-color: #C5A566 !important;
        outline: none !important;
        box-shadow: none !important;
    }
    [data-testid="stForm"] input:focus {
        border-bottom-color: #C5A566 !important;
        box-shadow: none !important;
        outline: none !important;
    }
    [data-testid="stForm"] label {
        font-family: 'Inter', sans-serif !important;
        font-size: 0.55rem !important;
        font-weight: 600 !important;
        letter-spacing: 3.5px !important;
        text-transform: uppercase !important;
        color: rgba(197,165,102,0.42) !important;
        padding-left: 20px !important;
        padding-top: 14px !important;
        padding-bottom: 2px !important;
    }
    [data-testid="stForm"] label span { display: none !important; }

    [data-testid="stFormSubmitButton"] > button {
        width: 100% !important;
        background: transparent !important;
        border: none !important;
        border-top: 1px solid rgba(197,165,102,0.18) !important;
        border-radius: 0 !important;
        color: rgba(197,165,102,0.7) !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.62rem !important;
        font-weight: 600 !important;
        letter-spacing: 3.5px !important;
        text-transform: uppercase !important;
        padding: 14px 20px !important;
        margin-top: 0 !important;
        transition: all 0.25s ease !important;
    }
    [data-testid="stFormSubmitButton"] > button:hover {
        background: rgba(197,165,102,0.07) !important;
        color: #C5A566 !important;
        border-top-color: rgba(197,165,102,0.35) !important;
    }

    [data-testid="stAlert"] {
        background: rgba(180,60,60,0.06) !important;
        border: 1px solid rgba(180,60,60,0.25) !important;
        border-radius: 0 !important;
        color: rgba(220,100,100,0.8) !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.62rem !important;
        letter-spacing: 2px !important;
        text-transform: uppercase !important;
    }
    [data-testid="stAlert"] svg { display: none !important; }
    [data-testid="stSpinner"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="lx-logo">
        <div class="lx-eyebrow">Escritório de Assessoria Jurídica</div>
        <div class="lx-monogram">E M</div>
        <div class="lx-name">Edson Medeiros</div>
        <div class="lx-tagline">Consultorias &amp; Compliance</div>
    </div>

    <div class="lx-ornament">
        <div class="lx-line-rev"></div>
        <div class="lx-diamond">◆</div>
        <div class="lx-line"></div>
    </div>

    <div class="lx-robot">
        <div class="lx-robot-label">Sistema de Auditoria Bancária</div>
        <div class="lx-robot-title">Extrato<span class="lx-robot-x">X</span></div>
    </div>

    <p class="lx-welcome">
        Bem-vindo ao sistema de auditoria bancária inteligente.<br>
        Identifique cobranças indevidas com precisão e eficiência.
    </p>
    """, unsafe_allow_html=True)

    with st.form("login_form", clear_on_submit=False):
        _email = st.text_input(
            "E-mail",
            placeholder="seu@email.com",
            key="login_email"
        )
        _senha = st.text_input(
            "Senha",
            placeholder="••••••••••",
            type="password",
            key="login_senha"
        )
        _submitted = st.form_submit_button("◆  Acessar o Sistema")

    if _submitted:
        if _check_login(_email, _senha):
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("Credenciais inválidas — verifique e-mail e senha")

    st.stop()

# --- (USUÁRIO AUTENTICADO — APP NORMAL A PARTIR DAQUI) ---

# --- 2. RÚBRICAS ---
RUBRICAS_MESTRE = {
    "CESTA": r"\bCESTA\b",
    "PACOTE": r"\bPACOTE\b",
    "MORA DE OPERAÇÃO": r"MORA\s+DE\s+OPERA[CÇ]AO|MORA\s+OPERA[CÇ]AO\b",
    "MORA CREDITO PESSOAL": r"MORA\s+CREDITO\s+PESSOAL|MORA\s+CRED\s+PESS|MORA\s+CP\b",
    "MORA OPERACAO DE CREDITO": r"MORA\s+OPERA[CÇ]AO\s+DE\s+CREDITO|MORA\s+OPER\s+CRED",
    "BX": r"\bBX\b",
    "PARCELA CREDITO PESSOAL": r"PARCELA\s+CREDITO\s+PESSOAL|PARC\s+CRED\s+PESS|PARCELA\s+CP\b",
    "GASTOS CARTAO DE CREDITO": r"GASTOS\s+CART[AÃ]O|FATURA\s+CART[AÃ]O|CART[AÃ]O\s+DE\s+CREDITO(?!\s+ANUIDADE)",
    "SEGURO": r"\bSEGURO\b|\bSEGURADORA\b|\bSEG\s",
    "ADIANT": r"\bADIANT|\bADIANTAMENTO\b",
    "APLIC": r"\bAPLICA[CÇ]AO\b|\bAPLIC\b",
    "ENCARGOS": r"\bENCARGOS?\b|\bENC\s+LIMITE\b|\bLIMITE\s+DE\s+CRED\b",
    "ANUIDADE": r"\bANUIDADE\b|CART[AÃ]O\s+CREDITO\s+ANUIDADE",
    "OPERACOES VENCIDAS": r"OPERA[CÇ][OÕ]ES\s+VENCIDAS",
    "BRADESCO VIDA E PREVIDENCIA": r"BRADESCO\s+VIDA|VIDA\s+E\s+PREVID[EÊ]NCIA|APORTE\s+VGBL|PAGTO.*VIDA",
    "TITULO DE CAPITALIZACAO": r"T[IÍ]TULO\s+DE\s+CAPITALIZ|\bCAPITALIZ[AÇ]",
    "AUTO RE": r"\bAUTO\s+RE\b|\bAUTORE\b",
}

TERMOS_EXCLUSAO = r"TRANSF|SALDO|SDO|TRANSFERENCIA|SALARIO|EMPRESTIMO|EMPR\."

# --- 3. MOTOR ---

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

def _limpar_historico(txt):
    """
    Remove do texto da rubrica os artefatos que o pdfplumber concatena
    na mesma linha: número de docto (sequência de 7+ dígitos), valores
    monetários (ex: 69,86) e saldos (ex: 3.467,77).
    Mantém apenas o texto descritivo da rubrica.
    """
    # Remove valores monetários: 1.234,56 ou 123,45
    limpo = re.sub(r'\d{1,3}(?:\.\d{3})*,\d{2}', '', txt)
    # Remove sequências longas de dígitos (nº docto, nº contrato, etc.)
    limpo = re.sub(r'\b\d{5,}\b', '', limpo)
    # Remove espaços múltiplos resultantes
    limpo = re.sub(r'\s{2,}', ' ', limpo).strip()
    return limpo[:80]

def realizar_auditoria(arquivo, rubricas_alvo):
    resultados = []

    with pdfplumber.open(arquivo) as pdf:
        data_atual = None
        apos_excl  = False
        pendentes  = []

        for page in pdf.pages:
            words = page.extract_words(x_tolerance=3, y_tolerance=3)
            if not words:
                continue

            grupos = _agrupar_linhas_por_y(words, tolerancia_y=5)

            linhas = []
            for grupo in grupos:
                grupo_s = sorted(grupo, key=lambda w: w['x0'])
                texto_up = ' '.join(w['text'] for w in grupo_s).upper().strip()

                data_col = None
                for w in grupo_s:
                    if w['x0'] < 80:
                        m = re.search(r'(\d{2}/\d{2}/\d{2,4})', w['text'])
                        if m:
                            data_col = m.group(1)
                            break

                # ── EXTRAÇÃO DE DÉBITO POR POSIÇÃO X ──────────────────────────────
                # Coluna Débito (R$): X entre 445 e 520
                # Calibrado a partir do cabeçalho real do PDF Bradesco
                X_DEBITO_MIN = 445
                X_DEBITO_MAX = 520

                valor_debito = None
                for w in grupo_s:
                    if X_DEBITO_MIN <= w['x0'] <= X_DEBITO_MAX:
                        m = re.search(r'(\d{1,3}(?:\.\d{3})*,\d{2})(?!\s*%)', w['text'])
                        if m:
                            valor_debito = m.group(1)
                            break

                linhas.append({
                    'texto':    texto_up,
                    'data_col': data_col,
                    'valor':    valor_debito,
                })

            # ── CONTROLE DE LINHAS JÁ CONSUMIDAS COMO FONTE DE VALOR ─────────────
            # Impede que o mesmo valor de uma linha seja usado por dois registros
            # distintos (via Prioridade 2 e Prioridade 3 simultaneamente).
            consumidas_como_fonte = set()

            for idx, linha in enumerate(linhas):
                txt = linha['texto']
                eh_excl = bool(re.search(TERMOS_EXCLUSAO, txt))

                if linha['data_col']:
                    if eh_excl:
                        # ── EXCLUSÃO COM DATA (ex: TRANSF SALDO 21/01/2022) ───────────
                        # REGRA CRÍTICA: se havia pendentes aguardando data inferior,
                        # esta data de exclusão É a data inferior deles — sela agora.
                        # Depois marca apos_excl=True para os lançamentos que vierem
                        # abaixo desta exclusão (eles precisarão de uma nova data inferior).
                        if pendentes:
                            data_excl = linha['data_col']
                            for p in pendentes:
                                p['DATA'] = data_excl
                                resultados.append(p)
                            pendentes = []
                            # data_atual recebe a data da exclusão para que lançamentos
                            # sem data que não sejam rubricas-alvo não fiquem órfãos.
                            data_atual = data_excl
                        apos_excl = True
                    else:
                        data_atual = linha['data_col']
                        apos_excl  = False
                        # Sela pendentes que aguardavam esta data inferior
                        if pendentes:
                            for p in pendentes:
                                p['DATA'] = data_atual
                                resultados.append(p)
                            pendentes = []

                if not txt or _eh_cabecalho(txt):
                    continue
                if "%" in txt and not linha['data_col']:
                    continue
                if eh_excl:
                    continue

                rubrica = _detectar_rubrica(txt, rubricas_alvo)
                if not rubrica:
                    continue

                valor_final = linha['valor']

                # ── PRIORIDADE 2: linha anterior ───────────────────────────────────
                # Caso TIPO C — rubrica é sublinha de um lançamento maior
                # (ex: CESTA aparece abaixo de TARIFA BANCARIA que contém o valor)
                # Só usa se a linha anterior não foi já consumida por outro registro
                if not valor_final and idx > 0 and (idx - 1) not in consumidas_como_fonte:
                    ant      = linhas[idx - 1]
                    rub_ant  = _detectar_rubrica(ant['texto'], rubricas_alvo)
                    excl_ant = bool(re.search(TERMOS_EXCLUSAO, ant['texto']))
                    if ant['valor'] and not rub_ant and not excl_ant:
                        valor_final = ant['valor']
                        consumidas_como_fonte.add(idx - 1)

                # ── PRIORIDADE 3: próximas linhas ──────────────────────────────────
                # Caso TIPO B — valor aparece em linha(s) abaixo da rubrica
                # (ex: ENCARGOS LIMITE DE CRED com valor na linha seguinte)
                if not valor_final:
                    for k in range(idx + 1, min(len(linhas), idx + 4)):
                        if k in consumidas_como_fonte:
                            continue
                        prox = linhas[k]
                        if re.search(TERMOS_EXCLUSAO, prox['texto']): break
                        if _detectar_rubrica(prox['texto'], rubricas_alvo): break
                        if "%" in prox['texto'] and not prox['data_col']: continue
                        if prox['valor']:
                            # Bloqueia se a próxima linha tem data_col + valor:
                            # ela é um lançamento completo → será capturada pelo Caso A.
                            if prox['data_col']:
                                break
                            valor_final = prox['valor']
                            consumidas_como_fonte.add(k)
                            break

                if not valor_final:
                    continue

                historico = _limpar_historico(txt)

                if apos_excl:
                    pendentes.append({
                        'DATA':      None,
                        'CATEGORIA': rubrica,
                        'VALOR':     valor_final,
                        'HISTÓRICO': historico,
                    })
                elif data_atual:
                    resultados.append({
                        'DATA':      data_atual,
                        'CATEGORIA': rubrica,
                        'VALOR':     valor_final,
                        'HISTÓRICO': historico,
                    })

    # Flush final: pendentes que sobraram após todas as páginas
    if pendentes:
        for p in pendentes:
            if p['DATA'] is None:
                p['DATA'] = '00/00/0000'
            resultados.append(p)

    # ── DEDUPLICAÇÃO FINAL ────────────────────────────────────────────────────
    # Chave: DATA + CATEGORIA + VALOR
    # O extrato Bradesco não emite dois lançamentos idênticos (mesmo dia,
    # mesma rubrica, mesmo valor) distintos. Esta deduplicação remove qualquer
    # duplicata residual que escapou do controle por consumidas_como_fonte.
    vistos = set()
    unicos = []
    for r in resultados:
        chave = (r['DATA'], r['CATEGORIA'], r['VALOR'])
        if chave not in vistos:
            vistos.add(chave)
            unicos.append(r)
    return unicos

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
st.markdown("""
<div class="em-header-wrap">
    <div class="em-eyebrow">Assessoria Jurídica &amp; Financeira</div>
    <h1 class="em-name">Edson <span>Medeiros</span></h1>
    <div class="em-subtitle">Consultorias &amp; Compliance</div>
    <div class="em-ornament">
        <div class="em-ornament-line rev"></div>
        <div class="em-ornament-diamond">◆</div>
        <div class="em-ornament-line"></div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── SIDEBAR: painel de rubricas ──────────────────────────────────────────────

if 'sel_all' not in st.session_state:
    st.session_state.sel_all = True

for r in RUBRICAS_MESTRE.keys():
    key = f"check_{r}"
    if key not in st.session_state:
        st.session_state[key] = True

st.sidebar.markdown("""
<div class="sb-header">
    <div class="sb-eyebrow">Painel de Controle</div>
    <div class="sb-title">Rubricas de <span>Auditoria</span></div>
</div>
""", unsafe_allow_html=True)

col_b1, col_b2 = st.sidebar.columns(2)

if col_b1.button("✦ Marcar Todas", key="btn_marcar"):
    for r in RUBRICAS_MESTRE.keys():
        st.session_state[f"check_{r}"] = True

if col_b2.button("✕ Desmarcar", key="btn_desmarcar"):
    for r in RUBRICAS_MESTRE.keys():
        st.session_state[f"check_{r}"] = False

selecionadas = []
for r in RUBRICAS_MESTRE.keys():
    key = f"check_{r}"
    marcado = st.sidebar.checkbox(r, value=st.session_state[key], key=key)
    if marcado:
        selecionadas.append(r)

st.sidebar.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)
total_r   = len(RUBRICAS_MESTRE)
sel_count = len(selecionadas)
if sel_count == total_r:
    cor_count  = "#C5A566"
    status_txt = f"◆ &nbsp; Todas as {total_r} ativas"
elif sel_count == 0:
    cor_count  = "rgba(197,165,102,0.28)"
    status_txt = f"◇ &nbsp; Nenhuma selecionada"
else:
    cor_count  = "rgba(197,165,102,0.7)"
    status_txt = f"◈ &nbsp; {sel_count} de {total_r} ativas"
st.sidebar.markdown(
    f'<div class="rubrica-count" style="color:{cor_count};">{status_txt}</div>',
    unsafe_allow_html=True
)

st.markdown("""
<div class="em-divider">
    <div class="em-divider-line"></div>
    <div class="em-divider-label">Análise de Extrato</div>
    <div class="em-divider-line"></div>
</div>
""", unsafe_allow_html=True)

upload = st.file_uploader(
    "Arraste o extrato bancário em PDF ou clique para selecionar",
    type=["pdf"],
    help="Formatos suportados: PDF de extratos Bradesco"
)

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

            st.markdown("""
<div class="em-divider" style="margin-top:36px;">
    <div class="em-divider-line"></div>
    <div class="em-divider-label">Tabelas de Cálculo</div>
    <div class="em-divider-line"></div>
</div>
<div class="em-section-note">Selecione a rubrica para baixar a planilha com fórmulas automáticas</div>
""", unsafe_allow_html=True)

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

            st.markdown("""
<div class="em-divider" style="margin-top:36px;">
    <div class="em-divider-line"></div>
    <div class="em-divider-label">Lançamentos Identificados</div>
    <div class="em-divider-line"></div>
</div>
""", unsafe_allow_html=True)
            st.dataframe(
                df[['DATA', 'CATEGORIA', 'VALOR', 'HISTÓRICO']],
                use_container_width=True
            )
        else:
            st.info("Nenhum débito encontrado com as rubricas selecionadas.")

st.markdown("""
<div class="em-footer">
    <div class="em-ornament">
        <div class="em-ornament-line rev"></div>
        <div class="em-ornament-diamond">◆</div>
        <div class="em-ornament-line"></div>
    </div>
    <div class="em-footer-name">Edson Medeiros</div>
    <div class="em-footer-contacts">
        <span class="em-footer-contact">
            <a href="https://wa.me/5592995087379" target="_blank">☎ (92) 99508-7379</a>
        </span>
        <span class="em-footer-contact" style="color:rgba(197,165,102,0.2);">|</span>
        <span class="em-footer-contact">
            <a href="mailto:edson.senabr@gmail.com">✉ edson.senabr@gmail.com</a>
        </span>
    </div>
    <a class="em-whatsapp-btn"
       href="https://wa.me/5592995087379?text=Olá%2C%20gostaria%20de%20agendar%20uma%20consulta%20com%20o%20Dr.%20Edson%20Medeiros."
       target="_blank">
        ◆ &nbsp; Agendar Consulta via WhatsApp
    </a>
</div>
""", unsafe_allow_html=True)
