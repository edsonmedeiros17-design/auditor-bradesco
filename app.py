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
    /* ── IMPORTS ──────────────────────────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400;1,600&family=Inter:wght@300;400;500;600&display=swap');

    /* ── VARIÁVEIS ────────────────────────────────────────────────────────────── */
    :root {
        --p:  #060A0D;
        --p2: #0D1117;
        --p3: #141B22;
        --g:  #C5A566;
        --g2: #D4B87A;
        --c:  #E8DCC8;
        --cm: rgba(232,220,200,0.55);
        --cl: rgba(232,220,200,0.22);
        --gl: rgba(197,165,102,0.18);
        --serif: 'Cormorant Garamond', Georgia, serif;
        --sans:  'Inter', system-ui, sans-serif;
    }

    /* ── BASE ─────────────────────────────────────────────────────────────────── */
    html, body, [class*="css"] {
        font-family: var(--sans);
        -webkit-font-smoothing: antialiased;
    }
    .stApp {
        background: var(--p);
        color: var(--c);
        /* Grade de pontos animada */
        background-image: radial-gradient(circle, rgba(197,165,102,0.05) 1px, transparent 1px);
        background-size: 32px 32px;
    }

    /* ── ANIMAÇÕES GLOBAIS ────────────────────────────────────────────────────── */
    @keyframes fadeSlideUp {
        from { opacity: 0; transform: translateY(28px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes shimmer {
        0%   { background-position: -400px 0; }
        100% { background-position: 400px 0; }
    }
    @keyframes borderGlow {
        0%, 100% { opacity: 0.3; }
        50%       { opacity: 1; }
    }
    @keyframes dashDraw {
        from { stroke-dashoffset: 800; }
        to   { stroke-dashoffset: 0; }
    }
    @keyframes scaleIn {
        from { opacity: 0; transform: scale(0.96); }
        to   { opacity: 1; transform: scale(1); }
    }
    @keyframes pulseGold {
        0%, 100% { box-shadow: 0 0 0 0 rgba(197,165,102,0); }
        50%       { box-shadow: 0 0 20px 4px rgba(197,165,102,0.12); }
    }

    /* ── BLOCK CONTAINER ──────────────────────────────────────────────────────── */
    .block-container {
        max-width: 1080px !important;
        padding: 0 48px 80px !important;
        animation: fadeSlideUp 0.6s ease both;
    }

    /* ── HEADER / LOGOMARCA ───────────────────────────────────────────────────── */
    .em-header-wrap {
        text-align: center;
        padding: 64px 0 48px;
        position: relative;
        animation: fadeSlideUp 0.7s ease both;
    }
    .em-header-wrap::before, .em-header-wrap::after {
        content: '';
        position: absolute;
        top: 50%;
        width: calc(50% - 240px);
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(197,165,102,0.35));
        animation: borderGlow 3s ease-in-out infinite;
    }
    .em-header-wrap::before { left: 0; transform: translateY(-50%) scaleX(-1); }
    .em-header-wrap::after  { right: 0; transform: translateY(-50%); }

    .em-eyebrow {
        font-family: var(--sans);
        font-size: 0.55rem;
        font-weight: 600;
        letter-spacing: 5.5px;
        text-transform: uppercase;
        color: rgba(197,165,102,0.45);
        margin-bottom: 10px;
    }
    .em-name {
        font-family: var(--serif);
        font-size: clamp(2.8rem, 5vw, 4.2rem);
        font-weight: 600;
        line-height: 1.0;
        color: var(--c);
        letter-spacing: 0.5px;
        margin: 0;
        /* Shimmer effect no hover */
        background: linear-gradient(
            110deg,
            var(--c) 20%,
            var(--g) 40%,
            var(--c) 60%
        );
        background-size: 600px 100%;
        background-clip: text;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: shimmer 4s linear infinite;
    }
    .em-subtitle {
        font-family: var(--serif);
        font-size: 0.92rem;
        font-weight: 400;
        font-style: italic;
        color: rgba(197,165,102,0.55);
        letter-spacing: 3px;
        margin-top: 8px;
        text-transform: uppercase;
    }
    .em-ornament {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 14px;
        margin-top: 24px;
    }
    .em-ornament-line {
        width: 90px;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(197,165,102,0.5));
        animation: borderGlow 3s ease-in-out infinite;
    }
    .em-ornament-line.rev {
        background: linear-gradient(90deg, rgba(197,165,102,0.5), transparent);
    }
    .em-ornament-diamond {
        color: rgba(197,165,102,0.7);
        font-size: 0.6rem;
    }

    /* ── DIVISORES DE SEÇÃO ───────────────────────────────────────────────────── */
    .em-divider {
        display: flex;
        align-items: center;
        gap: 16px;
        margin: 40px 0 28px;
    }
    .em-divider-line {
        flex: 1;
        height: 1px;
        background: rgba(197,165,102,0.15);
    }
    .em-divider-label {
        font-family: var(--sans);
        font-size: 0.55rem;
        font-weight: 600;
        letter-spacing: 4px;
        text-transform: uppercase;
        color: rgba(197,165,102,0.45);
        white-space: nowrap;
    }
    .em-section-note {
        font-family: var(--sans);
        font-size: 0.76rem;
        color: rgba(232,220,200,0.35);
        text-align: center;
        letter-spacing: 0.3px;
        margin-top: 4px;
        margin-bottom: 24px;
    }

    /* ── UPLOAD ZONE ──────────────────────────────────────────────────────────── */
    [data-testid="stFileUploader"] {
        border: 1px solid rgba(197,165,102,0.2) !important;
        border-radius: 0 !important;
        background: rgba(197,165,102,0.02) !important;
        transition: all 0.3s ease;
        animation: scaleIn 0.5s ease both;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: rgba(197,165,102,0.5) !important;
        background: rgba(197,165,102,0.05) !important;
        box-shadow: 0 0 40px rgba(197,165,102,0.06) !important;
    }
    [data-testid="stFileUploadDropzone"] {
        background: transparent !important;
        border: 1px dashed rgba(197,165,102,0.28) !important;
        border-radius: 0 !important;
        padding: 36px !important;
        transition: all 0.3s ease;
    }
    [data-testid="stFileUploader"]:hover [data-testid="stFileUploadDropzone"] {
        border-color: rgba(197,165,102,0.55) !important;
    }
    [data-testid="stFileUploaderDropzoneInstructions"] span,
    [data-testid="stFileUploaderDropzoneInstructions"] small {
        color: rgba(197,165,102,0.6) !important;
        font-family: var(--sans) !important;
        font-size: 0.8rem !important;
        letter-spacing: 0.5px;
    }
    [data-testid="stFileUploadDropzone"] button {
        background: transparent !important;
        border: 1px solid rgba(197,165,102,0.4) !important;
        color: var(--g) !important;
        border-radius: 0 !important;
        font-family: var(--sans) !important;
        font-size: 0.68rem !important;
        font-weight: 600 !important;
        letter-spacing: 2px !important;
        text-transform: uppercase !important;
        padding: 8px 22px !important;
        transition: all 0.25s ease;
    }
    [data-testid="stFileUploadDropzone"] button:hover {
        background: rgba(197,165,102,0.1) !important;
        border-color: var(--g) !important;
    }

    /* ── METRIC CARDS ─────────────────────────────────────────────────────────── */
    .metric-card {
        background: var(--p2);
        border: 1px solid rgba(197,165,102,0.12);
        border-top: 2px solid rgba(197,165,102,0.5);
        border-radius: 0;
        padding: 36px 28px;
        text-align: center;
        position: relative;
        overflow: hidden;
        transition: all 0.35s ease;
        animation: scaleIn 0.5s ease both;
    }
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0; left: -100%; right: 100%;
        height: 2px;
        background: linear-gradient(90deg, transparent, var(--g), transparent);
        transition: all 0.6s ease;
    }
    .metric-card:hover {
        background: var(--p3);
        border-top-color: var(--g);
        transform: translateY(-3px);
        box-shadow: 0 12px 40px rgba(197,165,102,0.08);
    }
    .metric-card:hover::before {
        left: 0;
        right: 0;
    }
    .metric-card h4 {
        font-family: var(--sans);
        font-size: 0.58rem;
        font-weight: 600;
        letter-spacing: 4px;
        text-transform: uppercase;
        color: rgba(197,165,102,0.5);
        margin: 0 0 16px 0;
    }
    .metric-card h2 {
        font-family: var(--serif);
        font-size: 2.8rem;
        font-weight: 600;
        color: var(--g);
        margin: 0;
        line-height: 1;
        background: linear-gradient(135deg, var(--g), var(--g2));
        background-clip: text;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-card-sub {
        font-size: 0.68rem;
        color: rgba(197,165,102,0.35);
        letter-spacing: 1px;
        margin-top: 8px;
    }

    /* ── DOWNLOAD BUTTONS ─────────────────────────────────────────────────────── */
    [data-testid="stDownloadButton"] > button {
        background: var(--p2) !important;
        border: 1px solid rgba(197,165,102,0.2) !important;
        border-left: 3px solid rgba(197,165,102,0.4) !important;
        color: rgba(197,165,102,0.75) !important;
        border-radius: 0 !important;
        font-family: var(--sans) !important;
        font-size: 0.7rem !important;
        font-weight: 500 !important;
        letter-spacing: 1.5px !important;
        text-transform: uppercase !important;
        padding: 12px 20px !important;
        transition: all 0.25s ease !important;
        width: 100% !important;
        text-align: left !important;
        position: relative !important;
        overflow: hidden !important;
    }
    [data-testid="stDownloadButton"] > button::after {
        content: '';
        position: absolute;
        top: 0; left: -100%;
        width: 100%; height: 100%;
        background: rgba(197,165,102,0.05);
        transition: left 0.3s ease;
    }
    [data-testid="stDownloadButton"] > button:hover {
        background: var(--p3) !important;
        border-color: rgba(197,165,102,0.5) !important;
        border-left-color: var(--g) !important;
        color: var(--g) !important;
        transform: translateX(4px) !important;
        box-shadow: 0 4px 20px rgba(197,165,102,0.08) !important;
    }
    [data-testid="stDownloadButton"] > button:hover::after {
        left: 0;
    }

    /* ── DATAFRAME ────────────────────────────────────────────────────────────── */
    [data-testid="stDataFrame"] {
        border: 1px solid rgba(197,165,102,0.15) !important;
        border-radius: 0 !important;
        animation: fadeSlideUp 0.4s ease both;
    }
    [data-testid="stDataFrame"] th {
        background: var(--p2) !important;
        color: rgba(197,165,102,0.7) !important;
        font-family: var(--sans) !important;
        font-size: 0.62rem !important;
        font-weight: 600 !important;
        letter-spacing: 3px !important;
        text-transform: uppercase !important;
        border-bottom: 1px solid rgba(197,165,102,0.2) !important;
        padding: 12px 16px !important;
    }
    [data-testid="stDataFrame"] td {
        font-family: var(--sans) !important;
        font-size: 0.8rem !important;
        color: rgba(232,220,200,0.75) !important;
        border-color: rgba(197,165,102,0.07) !important;
        padding: 10px 16px !important;
        transition: background 0.15s ease;
    }
    [data-testid="stDataFrame"] tr:hover td {
        background: rgba(197,165,102,0.04) !important;
    }

    /* ── INFO / ALERT ─────────────────────────────────────────────────────────── */
    [data-testid="stAlert"] {
        background: rgba(197,165,102,0.05) !important;
        border: 1px solid rgba(197,165,102,0.2) !important;
        border-radius: 0 !important;
        color: rgba(197,165,102,0.7) !important;
        font-size: 0.82rem !important;
    }
    [data-testid="stAlert"] svg { color: var(--g) !important; }

    /* ── SPINNER ──────────────────────────────────────────────────────────────── */
    [data-testid="stSpinner"] > div {
        border-top-color: var(--g) !important;
    }
    [data-testid="stSpinner"] p {
        color: rgba(197,165,102,0.6) !important;
        font-family: var(--sans) !important;
        font-size: 0.75rem !important;
        letter-spacing: 1.5px !important;
        text-transform: uppercase !important;
    }

    /* ── SIDEBAR ──────────────────────────────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: #050810;
        border-right: 1px solid rgba(197,165,102,0.12);
    }
    [data-testid="stSidebar"] > div:first-child { padding-top: 0; }

    .sb-header {
        padding: 28px 16px 18px;
        border-bottom: 1px solid rgba(197,165,102,0.1);
        position: relative;
    }
    .sb-header::after {
        content: '';
        position: absolute;
        bottom: -1px; left: 0;
        width: 60px; height: 1px;
        background: var(--g);
        animation: borderGlow 2.5s ease-in-out infinite;
    }
    .sb-eyebrow {
        font-family: var(--sans);
        font-size: 0.5rem;
        font-weight: 600;
        letter-spacing: 4px;
        text-transform: uppercase;
        color: rgba(197,165,102,0.38);
        margin-bottom: 4px;
    }
    .sb-title {
        font-family: var(--serif);
        font-size: 1.2rem;
        font-weight: 600;
        color: var(--c);
        letter-spacing: 0.5px;
        margin: 0;
        line-height: 1.2;
    }
    .sb-title span { color: var(--g); }

    /* Botões do sidebar */
    [data-testid="stSidebar"] .stButton > button {
        border-radius: 0 !important;
        font-family: var(--sans) !important;
        font-size: 0.58rem !important;
        font-weight: 600 !important;
        letter-spacing: 2px !important;
        text-transform: uppercase !important;
        padding: 7px 0 !important;
        width: 100% !important;
        transition: all 0.2s ease !important;
        border: none !important;
    }
    [data-testid="stSidebar"] .stButton:nth-of-type(1) > button {
        background: rgba(197,165,102,0.1) !important;
        color: var(--g) !important;
        border-right: 1px solid rgba(197,165,102,0.15) !important;
    }
    [data-testid="stSidebar"] .stButton:nth-of-type(1) > button:hover {
        background: rgba(197,165,102,0.18) !important;
    }
    [data-testid="stSidebar"] .stButton:nth-of-type(2) > button {
        background: transparent !important;
        color: rgba(232,220,200,0.25) !important;
    }
    [data-testid="stSidebar"] .stButton:nth-of-type(2) > button:hover {
        color: rgba(232,220,200,0.55) !important;
        background: rgba(255,255,255,0.03) !important;
    }

    /* Checkboxes */
    [data-testid="stSidebar"] .stCheckbox { margin: 0 !important; padding: 0 !important; }
    [data-testid="stSidebar"] .stCheckbox > label > div:first-child { display: none !important; }
    [data-testid="stSidebar"] .stCheckbox > label {
        display: flex !important;
        align-items: center !important;
        width: 100% !important;
        padding: 9px 16px !important;
        margin: 0 !important;
        cursor: pointer !important;
        border-left: 2px solid transparent !important;
        transition: all 0.18s ease !important;
        background: transparent !important;
    }
    [data-testid="stSidebar"] .stCheckbox > label:hover {
        background: rgba(197,165,102,0.04) !important;
        border-left-color: rgba(197,165,102,0.25) !important;
    }
    [data-testid="stSidebar"] .stCheckbox > label > div:last-child,
    [data-testid="stSidebar"] .stCheckbox > label > span {
        font-family: var(--sans) !important;
        font-size: 0.71rem !important;
        font-weight: 400 !important;
        color: rgba(232,220,200,0.32) !important;
        letter-spacing: 0.9px !important;
        text-transform: uppercase !important;
        line-height: 1 !important;
    }
    [data-testid="stSidebar"] .stCheckbox:has(input:checked) > label {
        border-left-color: var(--g) !important;
        background: rgba(197,165,102,0.06) !important;
    }
    [data-testid="stSidebar"] .stCheckbox:has(input:checked) > label > div:last-child,
    [data-testid="stSidebar"] .stCheckbox:has(input:checked) > label > span {
        color: var(--g) !important;
        font-weight: 500 !important;
    }

    .sidebar-divider {
        border: none;
        border-top: 1px solid rgba(197,165,102,0.08);
        margin: 6px 0 0;
    }
    .rubrica-count {
        padding: 8px 16px 16px;
        font-size: 0.56rem;
        font-family: var(--sans);
        letter-spacing: 2px;
        text-transform: uppercase;
    }

    /* ── FOOTER ───────────────────────────────────────────────────────────────── */
    .em-footer {
        margin-top: 80px;
        padding: 40px 0 20px;
        border-top: 1px solid rgba(197,165,102,0.12);
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 14px;
        position: relative;
    }
    .em-footer::before {
        content: '';
        position: absolute;
        top: -1px; left: 50%; transform: translateX(-50%);
        width: 120px; height: 1px;
        background: var(--g);
        animation: borderGlow 3s ease-in-out infinite;
    }
    .em-footer-name {
        font-family: var(--serif);
        font-size: 1.4rem;
        font-weight: 600;
        font-style: italic;
        color: var(--g);
        letter-spacing: 1.5px;
    }
    .em-footer-contacts {
        display: flex;
        gap: 28px;
        flex-wrap: wrap;
        justify-content: center;
    }
    .em-footer-contact {
        font-family: var(--sans);
        font-size: 0.7rem;
        color: rgba(197,165,102,0.45);
        letter-spacing: 1px;
    }
    .em-footer-contact a {
        color: rgba(197,165,102,0.45);
        text-decoration: none;
        transition: color 0.2s;
    }
    .em-footer-contact a:hover { color: var(--g); }
    .em-whatsapp-btn {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        background: transparent;
        border: 1px solid rgba(197,165,102,0.35);
        color: rgba(197,165,102,0.7);
        font-family: var(--sans);
        font-size: 0.65rem;
        font-weight: 600;
        letter-spacing: 2.5px;
        text-transform: uppercase;
        padding: 10px 28px;
        text-decoration: none;
        transition: all 0.25s ease;
        cursor: pointer;
        margin-top: 4px;
        position: relative;
        overflow: hidden;
    }
    .em-whatsapp-btn::before {
        content: '';
        position: absolute;
        top: 0; left: -100%;
        width: 100%; height: 100%;
        background: rgba(197,165,102,0.07);
        transition: left 0.3s ease;
    }
    .em-whatsapp-btn:hover {
        border-color: var(--g);
        color: var(--g);
        text-decoration: none;
    }
    .em-whatsapp-btn:hover::before { left: 0; }

    /* ── SCROLLBAR ────────────────────────────────────────────────────────────── */
    ::-webkit-scrollbar { width: 3px; height: 3px; }
    ::-webkit-scrollbar-track { background: var(--p); }
    ::-webkit-scrollbar-thumb { background: rgba(197,165,102,0.25); border-radius: 0; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(197,165,102,0.5); }

    /* ── HEADER NATIVO ────────────────────────────────────────────────────────── */
    header[data-testid="stHeader"] {
        background: rgba(6,10,13,0.95) !important;
        border-bottom: 1px solid rgba(197,165,102,0.08) !important;
        backdrop-filter: blur(12px) !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 1b. LÓGICA DE LOGIN ---
def _check_login(email: str, senha: str) -> bool:
    return email.strip() == "edson.senabr@gmail.com" and senha == "Edsonsena14"

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:

    # ── CSS: transforma o stApp inteiro na tela de login ──────────────────────
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;0,700;1,400&family=Inter:wght@400;500;600&display=swap');

    /* Esconde toda a UI padrão do Streamlit */
    header, footer,
    [data-testid="stSidebar"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"] { display: none !important; }

    /* Fundo da tela */
    .stApp {
        background: #060A0D !important;
        background-image:
            radial-gradient(circle, rgba(197,165,102,0.055) 1px, transparent 1px) !important;
        background-size: 30px 30px !important;
    }
    /* Vinheta sobre a grade */
    .stApp::after {
        content: '';
        position: fixed;
        inset: 0;
        background: radial-gradient(ellipse at 50% 50%,
            transparent 30%, rgba(6,10,13,0.78) 100%);
        pointer-events: none;
        z-index: 0;
    }

    /* Container principal: centraliza verticalmente */
    .block-container {
        max-width: 480px !important;
        padding: 0 24px !important;
        margin: 0 auto !important;
        position: relative;
        z-index: 1;
        /* Centralização vertical aproximada */
        padding-top: max(60px, 10vh) !important;
    }

    /* ── LOGOMARCA ────────────────────────────────────────────────────────── */
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

    /* ── ORNAMENTO ───────────────────────────────────────────────────────── */
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

    /* ── NOME DO ROBÔ ────────────────────────────────────────────────────── */
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

    /* ── BOAS-VINDAS ─────────────────────────────────────────────────────── */
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

    /* ── FORMULÁRIO — inputs ─────────────────────────────────────────────── */
    /* Wrapper do form sem bordas padrão */
    [data-testid="stForm"] {
        background: rgba(197,165,102,0.03) !important;
        border: 1px solid rgba(197,165,102,0.16) !important;
        border-radius: 0 !important;
        padding: 0 !important;
    }
    /* Inputs: linha inferior apenas, sem caixa */
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
    /* Labels dos inputs */
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
    /* Esconde o asterisco de "required" */
    [data-testid="stForm"] label span { display: none !important; }

    /* ── BOTÃO SUBMISSÃO ─────────────────────────────────────────────────── */
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

    /* ── ALERTA DE ERRO ──────────────────────────────────────────────────── */
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
    /* Esconde ícone padrão do alerta */
    [data-testid="stAlert"] svg { display: none !important; }

    /* ── SPINNER ─────────────────────────────────────────────────────────── */
    [data-testid="stSpinner"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

    # ── CONTEÚDO VISUAL (logomarca + robô + boas-vindas) ──────────────────────
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

    # ── FORMULÁRIO DE LOGIN ────────────────────────────────────────────────────
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

    # "BRADESCO VIDA E PREVIDENCIA" / "VIDA E PREVIDENCIA" / "APORTE VGBL" / "PAGTO BRADESCO VIDA"
    "BRADESCO VIDA E PREVIDENCIA": r"BRADESCO\s+VIDA|VIDA\s+E\s+PREVID[EÊ]NCIA|APORTE\s+VGBL|PAGTO.*VIDA",

    # "TITULO DE CAPITALIZACAO" / variações com acento
    "TITULO DE CAPITALIZACAO": r"T[IÍ]TULO\s+DE\s+CAPITALIZ|\bCAPITALIZ[AÇ]",

    # "AUTO RE" — seguro automóvel / renovação automática
    "AUTO RE": r"\bAUTO\s+RE\b|\bAUTORE\b",
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

                # ── EXTRAÇÃO DE DÉBITO POR POSIÇÃO X ──────────────────────────────
                # O extrato Bradesco tem 3 colunas numéricas:
                #   Crédito (R$) → X ≈ 385–440  (valores AZUIS — entradas, estornos)
                #   Débito  (R$) → X ≈ 451–515  (valores VERMELHOS — saídas indevidas)
                #   Saldo   (R$) → X ≈ 516–570  (saldo acumulado)
                #
                # REGRA: só capturar valores na coluna Débito (X entre 445 e 520).
                # Valores na coluna Crédito (X < 445) são entradas/estornos → ignorar.
                # Isso evita capturar créditos (ex: "ENCARGOS LIMITE CREDITO 800,00")
                # que o motor confundia como débito por serem o penúltimo valor da linha.
                #
                # Limites calibrados a partir do cabeçalho real do PDF:
                #   "Crédito (R$)" X=385   "Débito (R$)" X=451   "Saldo (R$)" X=519
                X_DEBITO_MIN = 445   # início da coluna Débito
                X_DEBITO_MAX = 520   # fim da coluna Débito (antes do Saldo)

                valor_debito = None
                for w in grupo_s:
                    if X_DEBITO_MIN <= w['x0'] <= X_DEBITO_MAX:
                        m = re.search(r'(\d{1,3}(?:\.\d{3})*,\d{2})(?!\s*%)', w['text'])
                        if m:
                            valor_debito = m.group(1)
                            break  # pega o primeiro valor válido na coluna Débito

                linhas.append({
                    'texto':    texto_up,
                    'data_col': data_col,
                    'valor':    valor_debito,
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
                        # Exclusão com data (ex: 21/01/2022 TRANSF SALDO):
                        # 1. Sela os pendentes do grupo ANTERIOR com esta data —
                        #    ela é a "data inferior" para o bloco que veio antes.
                        #    Ex: MORA/ENCARGOS após o 14/01 TRANSF devem receber
                        #        21/01/2022 (data do próximo TRANSF), não 24/01/2022.
                        # 2. Mantém apos_excl=True para os próximos lançamentos
                        #    sem data (eles pertencem ao novo grupo e aguardam
                        #    a próxima data inferior — não herdam 21/01/2022).
                        if pendentes:
                            for p in pendentes:
                                p['DATA'] = linha['data_col']
                                resultados.append(p)
                            pendentes = []
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
                # ATENÇÃO: só usar a próxima linha como fonte de valor se ela NÃO é
                # um lançamento completo (data_col + valor + rubrica), pois nesse caso
                # o loop principal já a capturará no Caso A — usar aqui geraria duplicata.
                if not valor_final:
                    for k in range(idx + 1, min(len(linhas), idx + 4)):
                        prox = linhas[k]
                        if re.search(TERMOS_EXCLUSAO, prox['texto']): break
                        if _detectar_rubrica(prox['texto'], rubricas_alvo): break
                        if "%" in prox['texto'] and not prox['data_col']: continue
                        if prox['valor']:
                            # Bloqueia se a próxima linha tem data_col + valor:
                            # ela é um lançamento completo → será capturada pelo Caso A.
                            # Usar ela aqui duplicaria o registro.
                            if prox['data_col']:
                                break
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

    # ── DEDUPLICAÇÃO FINAL ────────────────────────────────────────────────────
    # Remove registros com DATA + CATEGORIA + VALOR + HISTÓRICO idênticos.
    # Preserva lançamentos legítimos com mesma categoria e valor em datas
    # diferentes (ex: ANUIDADE cobrada todo mês) ou mesmo dia mas doctos distintos.
    vistos = set()
    unicos = []
    for r in resultados:
        chave = (r['DATA'], r['CATEGORIA'], r['VALOR'], r.get('HISTÓRICO','')[:40])
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
    <div class="em-eyebrow">Sistema de Auditoria Bancária &nbsp;·&nbsp; Assessoria Jurídica</div>
    <h1 class="em-name">Edson Medeiros</h1>
    <div class="em-subtitle">Consultorias &amp; Compliance</div>
    <div class="em-ornament">
        <div class="em-ornament-line rev"></div>
        <div class="em-ornament-diamond">◆</div>
        <div class="em-ornament-line"></div>
    </div>
</div>
""", unsafe_allow_html=True)

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
st.sidebar.markdown("""
<div class="sb-header">
    <div class="sb-eyebrow">Painel de Controle</div>
    <div class="sb-title">Rubricas de <span>Auditoria</span></div>
</div>
""", unsafe_allow_html=True)

# Botões Marcar / Desmarcar — aplicam imediatamente o estado individual
col_b1, col_b2 = st.sidebar.columns(2)

if col_b1.button("✦ Marcar Todas", key="btn_marcar"):
    for r in RUBRICAS_MESTRE.keys():
        st.session_state[f"check_{r}"] = True

if col_b2.button("✕ Desmarcar", key="btn_desmarcar"):
    for r in RUBRICAS_MESTRE.keys():
        st.session_state[f"check_{r}"] = False

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

# Divisor de seção
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
            total_dobro = total_geral * 2
            cats_unicas = df['CATEGORIA'].nunique()
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(
                    f'''<div class="metric-card">
                        <h4>Total Recuperável</h4>
                        <h2>R$ {total_geral:,.2f}</h2>
                        <div class="metric-card-sub">Valor identificado</div>
                    </div>''',
                    unsafe_allow_html=True
                )
            with c2:
                st.markdown(
                    f'''<div class="metric-card">
                        <h4>Lançamentos</h4>
                        <h2>{len(df)}</h2>
                        <div class="metric-card-sub">Débitos indevidos</div>
                    </div>''',
                    unsafe_allow_html=True
                )
            with c3:
                st.markdown(
                    f'''<div class="metric-card">
                        <h4>Rubricas</h4>
                        <h2>{cats_unicas}</h2>
                        <div class="metric-card-sub">Categorias encontradas</div>
                    </div>''',
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
            cols_dl = st.columns(2)
            for idx_cat, cat in enumerate(cats):
                df_cat     = df[df['CATEGORIA'] == cat]
                excel_file = gerar_excel_calculos(df_cat, cat)
                total_cat  = df_cat['V_NUM'].sum()
                with cols_dl[idx_cat % 2]:
                    st.download_button(
                        label=f"◆  {cat}  ·  R$ {total_cat:,.2f}",
                        data=excel_file,
                        file_name=f"Tabela_{cat.replace(' ', '_')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"dl_{cat}"
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
