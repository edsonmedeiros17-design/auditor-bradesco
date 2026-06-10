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
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400;1,600&family=Inter:wght@300;400;500;600&display=swap');

/* ═══ VARIÁVEIS ════════════════════════════════════════════════════════════ */
:root {
    --p:     #050810;
    --p2:    #0A0F18;
    --p3:    #111823;
    --p4:    #19222F;
    --g:     #C5A566;
    --g2:    #D4B87A;
    --g3:    #A8883E;
    --c:     #EDE5D4;
    --cm:    rgba(237,229,212,0.55);
    --cl:    rgba(237,229,212,0.20);
    --gl:    rgba(197,165,102,0.15);
    --gm:    rgba(197,165,102,0.08);
    --serif: 'Cormorant Garamond', Georgia, serif;
    --sans:  'Inter', system-ui, sans-serif;
    --r-sm:  10px;
    --r-md:  16px;
    --r-lg:  24px;
    --r-xl:  32px;
}

/* ═══ RESET BASE ══════════════════════════════════════════════════════════ */
html, body, [class*="css"] {
    font-family: var(--sans);
    -webkit-font-smoothing: antialiased;
    text-rendering: optimizeLegibility;
}

/* ═══ FUNDO EM CAMADAS ════════════════════════════════════════════════════ */
.stApp {
    background: var(--p);
    color: var(--c);
    /* Camada 1: grade de pontos */
    background-image:
        radial-gradient(circle, rgba(197,165,102,0.055) 1px, transparent 1px);
    background-size: 28px 28px;
}
/* Camada 2: luz dourada central — injetada via pseudo-elemento no body */
body::before {
    content: '';
    position: fixed;
    top: -30vh; left: 50%;
    transform: translateX(-50%);
    width: 80vw; height: 80vh;
    background: radial-gradient(ellipse,
        rgba(197,165,102,0.055) 0%,
        transparent 65%);
    pointer-events: none;
    z-index: 0;
}

/* ═══ ANIMAÇÕES ═══════════════════════════════════════════════════════════ */
@keyframes fadeUp {
    from { opacity:0; transform:translateY(32px); }
    to   { opacity:1; transform:translateY(0); }
}
@keyframes fadeIn {
    from { opacity:0; }
    to   { opacity:1; }
}
@keyframes shimmerText {
    0%   { background-position: -500px 0; }
    100% { background-position: 500px 0; }
}
@keyframes pulseRing {
    0%,100% { opacity:0.25; transform:scale(1); }
    50%      { opacity:0.7;  transform:scale(1.05); }
}
@keyframes glow {
    0%,100% { opacity:0.3; }
    50%      { opacity:0.85; }
}
@keyframes spin {
    to { transform: rotate(360deg); }
}
@keyframes barFill {
    from { width: 0; }
    to   { width: var(--bar-w, 60%); }
}
@keyframes floatY {
    0%,100% { transform: translateY(0); }
    50%      { transform: translateY(-5px); }
}
@keyframes revealLine {
    from { scaleX: 0; }
    to   { scaleX: 1; }
}

/* ═══ CONTAINER ═══════════════════════════════════════════════════════════ */
.block-container {
    max-width: 1100px !important;
    padding: 0 40px 100px !important;
    position: relative; z-index: 1;
    animation: fadeUp 0.7s cubic-bezier(.22,1,.36,1) both;
}

/* ═══ HEADER ═══════════════════════════════════════════════════════════════ */
.em-header-wrap {
    text-align: center;
    padding: 72px 0 52px;
    position: relative;
    animation: fadeUp 0.8s cubic-bezier(.22,1,.36,1) both;
}
/* Linhas laterais com animação */
.em-header-wrap::before, .em-header-wrap::after {
    content: '';
    position: absolute;
    top: 50%;
    width: calc(50% - 260px);
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(197,165,102,0.4));
    animation: glow 3.5s ease-in-out infinite;
}
.em-header-wrap::before { left: 0; transform: translateY(-50%) scaleX(-1); }
.em-header-wrap::after  { right: 0; transform: translateY(-50%); }

/* Monograma — círculo dourado acima do nome */
.em-monogram {
    display: inline-flex;
    align-items: center; justify-content: center;
    width: 52px; height: 52px;
    border-radius: 50%;
    border: 1px solid rgba(197,165,102,0.35);
    margin-bottom: 16px;
    position: relative;
    animation: floatY 4s ease-in-out infinite;
}
.em-monogram::before {
    content: '';
    position: absolute; inset: -5px;
    border-radius: 50%;
    border: 1px solid rgba(197,165,102,0.12);
    animation: pulseRing 3s ease-in-out infinite;
}
.em-monogram-text {
    font-family: var(--serif);
    font-size: 1.1rem; font-weight: 600;
    color: var(--g); letter-spacing: 3px;
}

.em-eyebrow {
    font-family: var(--sans);
    font-size: 0.68rem; font-weight: 600;
    letter-spacing: 5px; text-transform: uppercase;
    color: rgba(197,165,102,0.42);
    margin-bottom: 12px;
}
.em-name {
    font-family: var(--serif);
    font-size: clamp(3rem, 5.5vw, 4.8rem);
    font-weight: 600; line-height: 1.0;
    letter-spacing: 1px; margin: 0;
    background: linear-gradient(110deg,
        #EDE5D4 15%, #C5A566 40%, #D4B87A 55%, #EDE5D4 75%);
    background-size: 600px 100%;
    background-clip: text; -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: shimmerText 5s linear infinite;
}
.em-subtitle {
    font-family: var(--serif);
    font-size: 0.9rem; font-style: italic;
    color: rgba(197,165,102,0.5);
    letter-spacing: 3.5px; margin-top: 10px;
    text-transform: uppercase;
}
.em-badge-row {
    display: flex; align-items: center; justify-content: center;
    gap: 20px; margin-top: 22px;
}
.em-badge {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 6px 16px;
    border: 1px solid rgba(197,165,102,0.18);
    border-radius: 100px;
    font-size: 0.7rem; font-weight: 600; letter-spacing: 1.5px;
    text-transform: uppercase; color: rgba(197,165,102,0.5);
}
.em-badge-dot {
    width: 5px; height: 5px; border-radius: 50%;
    background: var(--g); opacity: 0.6;
    animation: glow 2s ease-in-out infinite;
}
.em-ornament {
    display: flex; align-items: center; justify-content: center;
    gap: 14px; margin-top: 24px;
}
.em-ornament-line {
    width: 80px; height: 1px;
    background: linear-gradient(90deg, transparent, rgba(197,165,102,0.45));
    animation: glow 3s ease-in-out infinite;
}
.em-ornament-line.rev {
    background: linear-gradient(90deg, rgba(197,165,102,0.45), transparent);
}
.em-ornament-diamond { color: rgba(197,165,102,0.65); font-size: 0.55rem; }

/* ═══ DIVISORES ═══════════════════════════════════════════════════════════ */
.em-divider {
    display: flex; align-items: center; gap: 16px;
    margin: 44px 0 30px;
}
.em-divider-line {
    flex: 1; height: 1px;
    background: linear-gradient(90deg,
        rgba(197,165,102,0.05), rgba(197,165,102,0.2), rgba(197,165,102,0.05));
}
.em-divider-pill {
    display: flex; align-items: center; gap: 8px;
    padding: 5px 16px;
    border: 1px solid rgba(197,165,102,0.18);
    border-radius: 100px;
    background: rgba(197,165,102,0.04);
}
.em-divider-label {
    font-size: 0.68rem; font-weight: 600;
    letter-spacing: 3.5px; text-transform: uppercase;
    color: rgba(197,165,102,0.45); white-space: nowrap;
}
.em-divider-num {
    font-family: var(--serif);
    font-size: 0.75rem; color: rgba(197,165,102,0.35);
}
.em-section-note {
    font-size: 0.88rem; color: rgba(237,229,212,0.3);
    text-align: center; letter-spacing: 0.3px;
    margin: 4px 0 28px; line-height: 1.6;
}

/* ═══ UPLOAD ZONE ══════════════════════════════════════════════════════════ */
.upload-wrap {
    border-radius: var(--r-lg);
    border: 1px solid rgba(197,165,102,0.18);
    background: linear-gradient(145deg,
        rgba(197,165,102,0.04) 0%,
        rgba(10,15,24,0.8) 100%);
    padding: 4px;
    transition: all 0.4s cubic-bezier(.22,1,.36,1);
    animation: fadeUp 0.5s cubic-bezier(.22,1,.36,1) both;
}
.upload-wrap:hover {
    border-color: rgba(197,165,102,0.45);
    box-shadow: 0 0 60px rgba(197,165,102,0.07),
                inset 0 1px 0 rgba(197,165,102,0.08);
}
[data-testid="stFileUploader"] {
    border-radius: var(--r-md) !important;
    border: none !important;
    background: transparent !important;
}
[data-testid="stFileUploadDropzone"] {
    background: transparent !important;
    border: 1px dashed rgba(197,165,102,0.25) !important;
    border-radius: var(--r-md) !important;
    padding: 44px !important;
    transition: all 0.3s ease;
}
[data-testid="stFileUploader"]:hover [data-testid="stFileUploadDropzone"] {
    border-color: rgba(197,165,102,0.5) !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] span,
[data-testid="stFileUploaderDropzoneInstructions"] small {
    color: rgba(197,165,102,0.55) !important;
    font-family: var(--sans) !important;
    font-size: 0.9rem !important; letter-spacing: 0.5px;
}
[data-testid="stFileUploadDropzone"] button {
    background: rgba(197,165,102,0.07) !important;
    border: 1px solid rgba(197,165,102,0.35) !important;
    color: var(--g) !important;
    border-radius: var(--r-sm) !important;
    font-family: var(--sans) !important;
    font-size: 0.66rem !important; font-weight: 600 !important;
    letter-spacing: 2px !important; text-transform: uppercase !important;
    padding: 9px 24px !important;
    transition: all 0.25s ease;
}
[data-testid="stFileUploadDropzone"] button:hover {
    background: rgba(197,165,102,0.14) !important;
    border-color: var(--g) !important;
    transform: translateY(-1px) !important;
}

/* Tutorial de upload */
.upload-tutorial {
    display: flex; gap: 24px; justify-content: center;
    flex-wrap: wrap;
    padding: 20px 0 4px;
}
.upload-step {
    display: flex; align-items: center; gap: 8px;
}
.upload-step-n {
    width: 22px; height: 22px;
    border-radius: 50%; border: 1px solid rgba(197,165,102,0.25);
    display: flex; align-items: center; justify-content: center;
    font-size: 0.6rem; font-weight: 600; color: rgba(197,165,102,0.55);
    flex-shrink: 0;
}
.upload-step-t {
    font-size: 0.82rem; color: rgba(237,229,212,0.35); letter-spacing: 0.3px;
}
.upload-step-arrow {
    font-size: 0.6rem; color: rgba(197,165,102,0.2);
    margin: 0 -12px; align-self: center;
}

/* ═══ METRIC CARDS ═════════════════════════════════════════════════════════ */
.metric-card {
    background: linear-gradient(145deg, var(--p3) 0%, var(--p2) 100%);
    border: 1px solid rgba(197,165,102,0.12);
    border-top: none;
    border-radius: var(--r-md);
    padding: 28px 24px 24px;
    text-align: left;
    position: relative; overflow: hidden;
    transition: all 0.35s cubic-bezier(.22,1,.36,1);
    animation: fadeUp 0.5s cubic-bezier(.22,1,.36,1) both;
}
/* Linha superior colorida */
.metric-card::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, transparent, var(--g), transparent);
    opacity: 0.5;
    transition: opacity 0.3s ease;
}
/* Reflexo de luz interno */
.metric-card::after {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 50%;
    background: linear-gradient(180deg,
        rgba(197,165,102,0.04) 0%, transparent 100%);
    border-radius: var(--r-md) var(--r-md) 0 0;
    pointer-events: none;
}
.metric-card:hover {
    transform: translateY(-4px) scale(1.01);
    border-color: rgba(197,165,102,0.28);
    box-shadow: 0 20px 60px rgba(0,0,0,0.4),
                0 0 30px rgba(197,165,102,0.07);
}
.metric-card:hover::before { opacity: 1; }

.metric-icon {
    width: 36px; height: 36px;
    border-radius: var(--r-sm);
    border: 1px solid rgba(197,165,102,0.2);
    background: rgba(197,165,102,0.07);
    display: flex; align-items: center; justify-content: center;
    margin-bottom: 18px;
    transition: all 0.3s ease;
}
.metric-card:hover .metric-icon {
    background: rgba(197,165,102,0.13);
    border-color: rgba(197,165,102,0.4);
}
.metric-icon svg {
    width: 18px; height: 18px;
    stroke: var(--g); fill: none; stroke-width: 1.5;
    stroke-linecap: round; stroke-linejoin: round;
}
.metric-card h4 {
    font-family: var(--sans);
    font-size: 0.72rem; font-weight: 600;
    letter-spacing: 3.5px; text-transform: uppercase;
    color: rgba(197,165,102,0.45); margin: 0 0 8px 0;
}
.metric-card h2 {
    font-family: var(--serif);
    font-size: 3rem; font-weight: 600;
    line-height: 1; margin: 0;
    background: linear-gradient(135deg, var(--g2) 0%, var(--g) 100%);
    background-clip: text; -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.metric-card-sub {
    font-size: 0.78rem; color: rgba(197,165,102,0.3);
    letter-spacing: 0.8px; margin-top: 6px;
    font-style: italic;
}

/* ═══ DOWNLOAD SECTION ═════════════════════════════════════════════════════ */
.dl-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }

[data-testid="stDownloadButton"] > button {
    background: var(--p3) !important;
    border: 1px solid rgba(197,165,102,0.14) !important;
    color: rgba(197,165,102,0.8) !important;
    border-radius: var(--r-md) !important;
    font-family: var(--sans) !important;
    font-size: 0.78rem !important; font-weight: 500 !important;
    letter-spacing: 1px !important; text-transform: uppercase !important;
    padding: 14px 18px !important;
    transition: all 0.3s cubic-bezier(.22,1,.36,1) !important;
    width: 100% !important; text-align: left !important;
    position: relative !important; overflow: hidden !important;
}
/* Linha lateral de acento */
[data-testid="stDownloadButton"] > button::before {
    content: '';
    position: absolute; top: 12%; left: 0;
    width: 3px; height: 76%;
    background: linear-gradient(180deg, transparent, var(--g), transparent);
    border-radius: 0 2px 2px 0; opacity: 0.4;
    transition: opacity 0.25s ease;
}
/* Reflexo de entrada */
[data-testid="stDownloadButton"] > button::after {
    content: '';
    position: absolute; top: 0; left: -100%;
    width: 60%; height: 100%;
    background: linear-gradient(90deg, transparent, rgba(197,165,102,0.06), transparent);
    transition: left 0.45s ease;
    transform: skewX(-15deg);
}
[data-testid="stDownloadButton"] > button:hover {
    background: var(--p4) !important;
    border-color: rgba(197,165,102,0.35) !important;
    color: var(--g) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 28px rgba(0,0,0,0.35), 0 0 16px rgba(197,165,102,0.06) !important;
}
[data-testid="stDownloadButton"] > button:hover::before { opacity: 1; }
[data-testid="stDownloadButton"] > button:hover::after  { left: 100%; }

/* ═══ DATAFRAME ════════════════════════════════════════════════════════════ */
[data-testid="stDataFrame"] {
    border: 1px solid rgba(197,165,102,0.12) !important;
    border-radius: var(--r-md) !important;
    overflow: hidden !important;
    animation: fadeUp 0.4s ease both;
}
[data-testid="stDataFrame"] th {
    background: var(--p3) !important;
    color: rgba(197,165,102,0.65) !important;
    font-family: var(--sans) !important;
    font-size: 0.72rem !important; font-weight: 600 !important;
    letter-spacing: 2px !important; text-transform: uppercase !important;
    border-bottom: 1px solid rgba(197,165,102,0.15) !important;
    padding: 14px 16px !important;
}
[data-testid="stDataFrame"] td {
    font-family: var(--sans) !important;
    font-size: 0.86rem !important;
    color: rgba(237,229,212,0.75) !important;
    border-color: rgba(197,165,102,0.06) !important;
    padding: 11px 16px !important;
}
[data-testid="stDataFrame"] tr:hover td {
    background: rgba(197,165,102,0.04) !important;
}

/* ═══ ALERT / INFO ═════════════════════════════════════════════════════════ */
[data-testid="stAlert"] {
    background: rgba(197,165,102,0.05) !important;
    border: 1px solid rgba(197,165,102,0.18) !important;
    border-radius: var(--r-md) !important;
    color: rgba(197,165,102,0.7) !important;
    font-size: 0.82rem !important;
}

/* ═══ SPINNER ══════════════════════════════════════════════════════════════ */
[data-testid="stSpinner"] > div {
    border-color: rgba(197,165,102,0.15) !important;
    border-top-color: var(--g) !important;
    border-radius: 50%;
}
[data-testid="stSpinner"] p {
    color: rgba(197,165,102,0.5) !important;
    font-family: var(--sans) !important;
    font-size: 0.82rem !important; letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
}

/* ═══ SIDEBAR ══════════════════════════════════════════════════════════════ */
[data-testid="stSidebar"] {
    background: #04060C;
    border-right: 1px solid rgba(197,165,102,0.1);
}
[data-testid="stSidebar"] > div:first-child { padding-top: 0; }

.sb-header {
    padding: 28px 18px 18px;
    border-bottom: 1px solid rgba(197,165,102,0.08);
    position: relative;
    background: linear-gradient(180deg,
        rgba(197,165,102,0.04) 0%, transparent 100%);
}
.sb-header::after {
    content: '';
    position: absolute; bottom: -1px; left: 0;
    width: 50px; height: 1px;
    background: var(--g);
    animation: glow 2.5s ease-in-out infinite;
}
.sb-eyebrow {
    font-size: 0.65rem; font-weight: 600;
    letter-spacing: 4px; text-transform: uppercase;
    color: rgba(197,165,102,0.32); margin-bottom: 4px;
}
.sb-title {
    font-family: var(--serif);
    font-size: 1.3rem; font-weight: 600;
    color: var(--c); letter-spacing: 0.5px; margin: 0;
}
.sb-title span { color: var(--g); }

/* Tutorial na sidebar */
.sb-tutorial {
    margin: 12px 14px;
    padding: 12px 14px;
    border-radius: var(--r-sm);
    background: rgba(197,165,102,0.04);
    border: 1px solid rgba(197,165,102,0.1);
}
.sb-tutorial-title {
    font-size: 0.68rem; font-weight: 600;
    letter-spacing: 2.5px; text-transform: uppercase;
    color: rgba(197,165,102,0.4); margin-bottom: 7px;
}
.sb-tutorial-text {
    font-size: 0.82rem; color: rgba(237,229,212,0.38);
    line-height: 1.6; letter-spacing: 0.2px;
}

/* Botões marcar/desmarcar */
[data-testid="stSidebar"] .stButton > button {
    border-radius: var(--r-sm) !important;
    font-family: var(--sans) !important;
    font-size: 0.57rem !important; font-weight: 600 !important;
    letter-spacing: 1.8px !important; text-transform: uppercase !important;
    padding: 7px 0 !important; width: 100% !important;
    transition: all 0.2s ease !important; border: none !important;
}
[data-testid="stSidebar"] .stButton:nth-of-type(1) > button {
    background: rgba(197,165,102,0.1) !important;
    color: var(--g) !important;
    border-right: 1px solid rgba(197,165,102,0.12) !important;
}
[data-testid="stSidebar"] .stButton:nth-of-type(1) > button:hover {
    background: rgba(197,165,102,0.18) !important;
    transform: none !important;
}
[data-testid="stSidebar"] .stButton:nth-of-type(2) > button {
    background: transparent !important;
    color: rgba(237,229,212,0.22) !important;
}
[data-testid="stSidebar"] .stButton:nth-of-type(2) > button:hover {
    color: rgba(237,229,212,0.5) !important;
    background: rgba(255,255,255,0.025) !important;
}

/* Checkboxes como items de lista */
[data-testid="stSidebar"] .stCheckbox { margin:0 !important; padding:0 !important; }
[data-testid="stSidebar"] .stCheckbox > label > div:first-child { display:none !important; }
[data-testid="stSidebar"] .stCheckbox > label {
    display: flex !important; align-items: center !important;
    gap: 8px !important; width: 100% !important;
    padding: 8px 14px 8px 16px !important;
    margin: 0 !important; cursor: pointer !important;
    border-left: 2px solid transparent !important;
    border-radius: 0 var(--r-sm) var(--r-sm) 0 !important;
    transition: all 0.18s ease !important;
    background: transparent !important;
}
[data-testid="stSidebar"] .stCheckbox > label:hover {
    background: rgba(197,165,102,0.04) !important;
    border-left-color: rgba(197,165,102,0.22) !important;
}
[data-testid="stSidebar"] .stCheckbox > label > div:last-child,
[data-testid="stSidebar"] .stCheckbox > label > span {
    font-family: var(--sans) !important;
    font-size: 0.8rem !important; font-weight: 400 !important;
    color: rgba(237,229,212,0.28) !important;
    letter-spacing: 0.8px !important; text-transform: uppercase !important;
    line-height: 1 !important;
}
[data-testid="stSidebar"] .stCheckbox:has(input:checked) > label {
    border-left-color: var(--g) !important;
    background: rgba(197,165,102,0.06) !important;
}
[data-testid="stSidebar"] .stCheckbox:has(input:checked) > label > div:last-child,
[data-testid="stSidebar"] .stCheckbox:has(input:checked) > label > span {
    color: rgba(197,165,102,0.85) !important; font-weight: 500 !important;
}

.sidebar-divider {
    border: none;
    border-top: 1px solid rgba(197,165,102,0.07);
    margin: 4px 0 0;
}
.rubrica-count {
    padding: 8px 16px 16px;
    font-size: 0.68rem; font-family: var(--sans);
    letter-spacing: 2px; text-transform: uppercase;
}

/* ═══ FOOTER ═══════════════════════════════════════════════════════════════ */
.em-footer {
    margin-top: 100px;
    padding: 48px 0 24px;
    border-top: 1px solid rgba(197,165,102,0.1);
    display: flex; flex-direction: column;
    align-items: center; gap: 16px;
    position: relative;
}
.em-footer::before {
    content: '';
    position: absolute; top: -1px; left: 50%;
    transform: translateX(-50%);
    width: 100px; height: 1px;
    background: linear-gradient(90deg, transparent, var(--g), transparent);
    animation: glow 3s ease-in-out infinite;
}
.em-footer-name {
    font-family: var(--serif);
    font-size: 1.8rem; font-weight: 600; font-style: italic;
    color: var(--g); letter-spacing: 2px;
}
.em-footer-contacts {
    display: flex; gap: 28px; flex-wrap: wrap; justify-content: center;
}
.em-footer-contact {
    font-size: 0.8rem; color: rgba(197,165,102,0.4); letter-spacing: 1px;
}
.em-footer-contact a {
    color: rgba(197,165,102,0.4); text-decoration: none;
    transition: color 0.2s;
}
.em-footer-contact a:hover { color: var(--g); }
.em-whatsapp-btn {
    display: inline-flex; align-items: center; gap: 10px;
    background: rgba(197,165,102,0.05);
    border: 1px solid rgba(197,165,102,0.3);
    border-radius: var(--r-sm);
    color: rgba(197,165,102,0.7);
    font-family: var(--sans); font-size: 0.64rem;
    font-weight: 600; letter-spacing: 2.5px;
    text-transform: uppercase; padding: 11px 28px;
    text-decoration: none;
    transition: all 0.3s cubic-bezier(.22,1,.36,1);
    cursor: pointer; margin-top: 6px; position: relative; overflow: hidden;
}
.em-whatsapp-btn::after {
    content: '';
    position: absolute; top: 0; left: -100%;
    width: 60%; height: 100%;
    background: linear-gradient(90deg, transparent, rgba(197,165,102,0.08), transparent);
    transform: skewX(-15deg);
    transition: left 0.5s ease;
}
.em-whatsapp-btn:hover {
    border-color: var(--g); color: var(--g); text-decoration: none;
    background: rgba(197,165,102,0.1);
    box-shadow: 0 8px 30px rgba(197,165,102,0.1);
    transform: translateY(-2px);
}
.em-whatsapp-btn:hover::after { left: 120%; }

/* ═══ SCROLLBAR ════════════════════════════════════════════════════════════ */
::-webkit-scrollbar { width: 3px; height: 3px; }
::-webkit-scrollbar-track { background: var(--p); }
::-webkit-scrollbar-thumb {
    background: rgba(197,165,102,0.22);
    border-radius: 2px;
}
::-webkit-scrollbar-thumb:hover { background: rgba(197,165,102,0.5); }

/* ═══ HEADER NATIVO ════════════════════════════════════════════════════════ */
header[data-testid="stHeader"] {
    background: rgba(4,6,12,0.9) !important;
    border-bottom: 1px solid rgba(197,165,102,0.07) !important;
    backdrop-filter: blur(16px) !important;
}
</style>
""", unsafe_allow_html=True)

# --- 1b. LÓGICA DE LOGIN ---
def _check_login(email: str, senha: str) -> bool:
    return email.strip() == "edson.senabr@gmail.com" and senha == "Edsonsena14"

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:

    # CSS da tela de login
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400;1,600&family=Inter:wght@300;400;500;600&family=Great+Vibes&display=swap');

    header, footer, [data-testid="stSidebar"],
    [data-testid="stToolbar"], [data-testid="stDecoration"],
    [data-testid="stStatusWidget"] { display: none !important; }

    .stApp {
        background: #04060C !important;
        background-image: radial-gradient(circle, rgba(197,165,102,0.045) 1px, transparent 1px) !important;
        background-size: 28px 28px !important;
    }

    /* Centraliza o container verticalmente */
    .block-container {
        max-width: 1000px !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        min-height: 100vh !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
    }

    /* Remove gaps entre colunas do Streamlit */
    [data-testid="stHorizontalBlock"] {
        gap: 0 !important;
        border: 1px solid rgba(197,165,102,0.12) !important;
        border-radius: 0 !important;
        overflow: hidden !important;
        box-shadow: 0 40px 100px rgba(0,0,0,0.7) !important;
    }
    [data-testid="stHorizontalBlock"] > div {
        padding: 0 !important;
    }

    /* Painel esquerdo */
    .lx-left {
        padding: 60px 48px;
        background: linear-gradient(145deg,
            rgba(197,165,102,0.06) 0%,
            rgba(6,10,16,0.95) 50%,
            rgba(10,16,24,0.98) 100%);
        border-right: 1px solid rgba(197,165,102,0.1);
        min-height: 560px;
        display: flex; flex-direction: column; justify-content: center;
        position: relative; overflow: hidden;
    }
    .lx-left::after {
        content: '';
        position: absolute; top: -60px; left: -60px;
        width: 260px; height: 260px; border-radius: 50%;
        border: 1px solid rgba(197,165,102,0.06);
        pointer-events: none;
    }
    .lx-eyebrow {
        font-family: 'Inter', sans-serif;
        font-size: 0.62rem; font-weight: 600;
        letter-spacing: 5px; text-transform: uppercase;
        color: rgba(197,165,102,0.4);
        margin-bottom: 18px;
    }
    .lx-name {
        font-family: 'Cormorant Garamond', serif;
        font-size: 2.8rem; font-weight: 600; line-height: 1.1;
        color: #EDE5D4; letter-spacing: 1px;
        margin-bottom: 6px;
    }
    .lx-name em { color: #C5A566; font-style: normal; }
    .lx-role {
        font-family: 'Cormorant Garamond', serif;
        font-size: 1.05rem; font-style: italic;
        color: rgba(197,165,102,0.5); letter-spacing: 2px;
        margin-bottom: 28px;
    }
    .lx-sig {
        font-family: 'Great Vibes', cursive;
        font-size: 2.8rem; color: rgba(197,165,102,0.32);
        line-height: 1; margin-bottom: 28px;
    }
    .lx-sep {
        width: 44px; height: 1px;
        background: linear-gradient(90deg, #C5A566, transparent);
        margin-bottom: 24px;
    }
    .lx-desc {
        font-family: 'Inter', sans-serif;
        font-size: 0.82rem; font-weight: 300;
        color: rgba(237,229,212,0.32); line-height: 1.75;
        margin-bottom: 32px;
    }
    .lx-feat { display: flex; flex-direction: column; gap: 10px; }
    .lx-feat-row { display: flex; align-items: center; gap: 10px; }
    .lx-dot {
        width: 5px; height: 5px; border-radius: 50%;
        background: #C5A566; opacity: 0.45; flex-shrink: 0;
    }
    .lx-feat-t {
        font-family: 'Inter', sans-serif;
        font-size: 0.78rem; color: rgba(237,229,212,0.35);
    }

    /* Painel direito */
    .lx-right {
        padding: 60px 44px;
        background: rgba(6,10,16,0.85);
        min-height: 560px;
        display: flex; flex-direction: column; justify-content: center;
    }
    .lx-form-label {
        font-family: 'Inter', sans-serif;
        font-size: 0.6rem; font-weight: 600;
        letter-spacing: 4px; text-transform: uppercase;
        color: rgba(197,165,102,0.36); margin-bottom: 8px;
    }
    .lx-form-title {
        font-family: 'Cormorant Garamond', serif;
        font-size: 2.2rem; font-weight: 600; color: #EDE5D4;
        margin-bottom: 6px; line-height: 1.1;
    }
    .lx-form-title span { color: #C5A566; }
    .lx-form-sub {
        font-family: 'Cormorant Garamond', serif;
        font-size: 0.95rem; font-style: italic;
        color: rgba(197,165,102,0.4); margin-bottom: 32px;
    }
    .lx-orn {
        display: flex; align-items: center;
        gap: 10px; margin-bottom: 28px;
    }
    .lx-orn-l { flex: 1; height: 1px; background: rgba(197,165,102,0.14); }
    .lx-orn-d { font-size: 0.38rem; color: rgba(197,165,102,0.28); }

    /* Inputs */
    [data-testid="stForm"] {
        background: transparent !important;
        border: none !important; padding: 0 !important;
    }
    [data-testid="stForm"] label {
        font-family: 'Inter', sans-serif !important;
        font-size: 0.62rem !important; font-weight: 600 !important;
        letter-spacing: 3px !important; text-transform: uppercase !important;
        color: rgba(197,165,102,0.4) !important;
    }
    [data-testid="stForm"] label span { display: none !important; }
    [data-testid="stForm"] input {
        background: rgba(197,165,102,0.04) !important;
        border: 1px solid rgba(197,165,102,0.14) !important;
        border-radius: 10px !important;
        color: #EDE5D4 !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.9rem !important; font-weight: 300 !important;
        padding: 13px 16px !important;
        caret-color: #C5A566 !important;
        outline: none !important; box-shadow: none !important;
        transition: all 0.25s ease !important;
    }
    [data-testid="stForm"] input:focus {
        border-color: rgba(197,165,102,0.5) !important;
        background: rgba(197,165,102,0.07) !important;
        box-shadow: 0 0 0 3px rgba(197,165,102,0.07) !important;
    }
    [data-testid="stFormSubmitButton"] > button {
        width: 100% !important;
        background: rgba(197,165,102,0.09) !important;
        border: 1px solid rgba(197,165,102,0.32) !important;
        border-radius: 10px !important;
        color: #C5A566 !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.72rem !important; font-weight: 600 !important;
        letter-spacing: 3px !important; text-transform: uppercase !important;
        padding: 14px !important; margin-top: 8px !important;
        transition: all 0.3s ease !important;
    }
    [data-testid="stFormSubmitButton"] > button:hover {
        background: rgba(197,165,102,0.16) !important;
        border-color: #C5A566 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 24px rgba(197,165,102,0.12) !important;
    }
    [data-testid="stAlert"] {
        background: rgba(180,60,60,0.06) !important;
        border: 1px solid rgba(180,60,60,0.22) !important;
        border-radius: 10px !important;
        color: rgba(220,110,110,0.8) !important;
        font-size: 0.75rem !important;
    }
    [data-testid="stAlert"] svg { display: none !important; }

    /* Rodapé fixo */
    .lx-footer {
        text-align: center;
        font-family: 'Inter', sans-serif;
        font-size: 0.62rem; letter-spacing: 2px;
        text-transform: uppercase;
        color: rgba(197,165,102,0.2);
        margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

    # LAYOUT: st.columns para split real
    col_esq, col_dir = st.columns([1.15, 0.85])

    with col_esq:
        st.markdown("""
        <div class="lx-left">
            <div class="lx-eyebrow">Escritório de Assessoria Jurídica</div>
            <div class="lx-name">Edson<br><em>Medeiros</em></div>
            <div class="lx-role">Consultorias &amp; Compliance</div>
            <div class="lx-sig">E. Medeiros</div>
            <div class="lx-sep"></div>
            <p class="lx-desc">
                Sistema especializado em auditoria bancária inteligente.
                Identificamos cobranças indevidas com precisão e geramos
                relatórios prontos para uso jurídico.
            </p>
            <div class="lx-feat">
                <div class="lx-feat-row">
                    <div class="lx-dot"></div>
                    <div class="lx-feat-t">Extrai débitos indevidos do extrato PDF</div>
                </div>
                <div class="lx-feat-row">
                    <div class="lx-dot"></div>
                    <div class="lx-feat-t">Gera planilhas com cálculo em dobro (Art. 42 CDC)</div>
                </div>
                <div class="lx-feat-row">
                    <div class="lx-dot"></div>
                    <div class="lx-feat-t">Suporta extratos Bradesco · múltiplas páginas</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_dir:
        st.markdown("""
        <div class="lx-right">
            <div class="lx-form-label">Sistema de Auditoria</div>
            <div class="lx-form-title">Extrato<span>X</span></div>
            <div class="lx-form-sub">Acesse sua conta para continuar</div>
            <div class="lx-orn">
                <div class="lx-orn-l"></div>
                <div class="lx-orn-d">◆</div>
                <div class="lx-orn-l"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form", clear_on_submit=False):
            _email = st.text_input("E-mail", placeholder="seu@email.com", key="login_email")
            _senha = st.text_input("Senha", placeholder="••••••••••", type="password", key="login_senha")
            _submitted = st.form_submit_button("◆  Acessar o Sistema")

        if _submitted:
            if _check_login(_email, _senha):
                st.session_state["autenticado"] = True
                st.rerun()
            else:
                st.error("Credenciais inválidas — verifique e-mail e senha")

    st.markdown("""
    <div class="lx-footer">
        Edson Medeiros Consultorias &nbsp;·&nbsp; (92) 99508-7379 &nbsp;·&nbsp; edson.senabr@gmail.com
    </div>
    """, unsafe_allow_html=True)

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

    # "SAQUEcorrespondente" / "SAQUEterminal" / "SAQUEpremium" — tarifa de saque bancário
    # Aparecem como SUBLINHA de "TARIFA BANCARIA" no extrato Bradesco (Caso C):
    #   Linha anterior (COM valor): "TARIFA BANCARIA  0000001  6,75  2.239,89"
    #   Sublinha (sem valor):       "SAQUEcorrespondente"   ← esta linha é detectada
    #
    # O motor Caso C: rubrica sem valor na linha atual → busca valor na linha ANTERIOR.
    # A linha anterior "TARIFA BANCARIA X,XX" fornece o valor correto.
    #
    # NÃO captura "SAQUE DIN CORBAN CARTAO" (saque do cliente — não é tarifa).
    # NÃO captura "SAQUE DINHEIRO ATM" (saque do cliente — não é tarifa).
    # NÃO captura "CESTA B.EXPRESSO4" (sublinha diferente — capturada pela rubrica CESTA).
    "SAQUE TERMINAL": r"\bSAQUECORRESPONDENTE\b|\bSAQUETERMINAL\b|\bSAQUE\s+CORRESPONDENTE\b|\bSAQUE\s+TERMINAL\b|\bSAQUEPREMIUM\b",

    # "TARIFA EMISSAO EXTRATO" / "EXTRATOmes(E)" — tarifa de emissão de extrato mensal
    # No extrato Bradesco aparece em duas formas:
    #   Forma A (linha completa): "TARIFA EMISSAO EXTRATO 0210220 1,35 1,00" → TEM o valor
    #   Forma B (sublinha):       "EXTRATOMES(E)"  →  sem valor, a linha anterior TEM o valor
    #
    # ATENÇÃO: capturamos APENAS a Forma A (linha completa com valor).
    # A sublinha EXTRATOMES(E) é ignorada pois o valor já foi capturado na linha anterior.
    # Isso evita duplicatas e valores errados causados pelo Caso C pegando lançamentos vizinhos.
    "EXTRATO MES": r"TARIFA\s+EMISSAO\s+EXTRATO",
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
    # Remove registros EXATAMENTE duplicados (mesma DATA+CATEGORIA+VALOR+HISTÓRICO
    # que aparecem mais de uma vez por bug do motor — ex: Caso B + Caso A na mesma linha).
    # PRESERVA registros com mesmo valor/categoria no mesmo dia quando o histórico
    # for idêntico (ex: dois SAQUEcorrespondente de R$13,50 no mesmo dia — são
    # dois débitos reais distintos, não duplicatas de bug).
    #
    # Estratégia: conta quantas vezes cada chave aparece no extrato original
    # (source_count) e preserva no máximo essa quantidade no resultado.
    from collections import Counter
    chave_count = Counter(
        (r['DATA'], r['CATEGORIA'], r['VALOR'], r.get('HISTÓRICO','')[:80])
        for r in resultados
    )
    # Para sublinhas sem saldo (ex: SAQUECORRESPONDENTE), o histórico é sempre igual.
    # Não deduplicar se a contagem natural for > 1 (são débitos reais distintos).
    # Só remover quando o mesmo registro apareceu mais de uma vez POR BUG DO MOTOR
    # (o que indica captura dupla do mesmo lançamento físico do extrato).
    # Heurística: se dois registros têm (DATA, CAT, VALOR, HIST) idênticos mas
    # o HISTÓRICO contém informação de saldo diferente, são distintos.
    # Como sublinhas não têm saldo no histórico, usamos contador sequencial.
    vistos_count = Counter()
    unicos = []
    for r in resultados:
        chave = (r['DATA'], r['CATEGORIA'], r['VALOR'], r.get('HISTÓRICO','')[:80])
        vistos_count[chave] += 1
        # Só descarta se apareceu mais vezes do que o esperado pela fonte
        # (indica captura dupla do motor, não dois débitos reais)
        # Para históricos sem saldo (sublinhas), permitir até source_count ocorrências
        unicos.append(r)
    # Remover apenas duplicatas exatas introduzidas pelo motor (não pelo extrato)
    # Identificadas por: mesmo histórico COM saldo (linha completa) aparecendo 2x
    vistos2 = set()
    resultado_final = []
    for r in unicos:
        hist = r.get('HISTÓRICO','')
        # Se o histórico tem valores numéricos (linha completa), pode ser duplicata de bug
        tem_valores = bool(re.search(r'\d{1,3}(?:\.\d{3})*,\d{2}', hist))
        chave = (r['DATA'], r['CATEGORIA'], r['VALOR'], hist[:80])
        if tem_valores:
            # Linha completa: aplicar deduplicação estrita
            if chave not in vistos2:
                vistos2.add(chave)
                resultado_final.append(r)
        else:
            # Sublinha (ex: SAQUECORRESPONDENTE, EXTRATOMES): preservar todas
            # (cada uma corresponde a um débito real no extrato)
            resultado_final.append(r)
    return resultado_final

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
    <div class="em-monogram">
        <span class="em-monogram-text">EM</span>
    </div>
    <div class="em-eyebrow">Assessoria Jurídica &nbsp;·&nbsp; Auditoria Bancária Inteligente</div>
    <h1 class="em-name">Edson Medeiros</h1>
    <div class="em-subtitle">Consultorias &amp; Compliance</div>
    <div class="em-badge-row">
        <div class="em-badge">
            <div class="em-badge-dot"></div>
            Sistema Online
        </div>
        <div class="em-badge">ExtratoX v2.0</div>
        <div class="em-badge">Bradesco · Extrato PDF</div>
    </div>
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
<div class="sb-tutorial">
    <div class="sb-tutorial-title">Como usar</div>
    <div class="sb-tutorial-text">
        Selecione as rubricas que deseja auditar. Cada rubrica representa um tipo de cobrança bancária. O sistema identificará automaticamente os valores cobrados no extrato.
    </div>
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
    <div class="em-divider-pill">
        <span class="em-divider-label">Análise de Extrato</span>
    </div>
    <div class="em-divider-line"></div>
</div>

<div class="upload-tutorial">
    <div class="upload-step">
        <div class="upload-step-n">1</div>
        <div class="upload-step-t">Selecione as rubricas na barra lateral</div>
    </div>
    <div class="upload-step-arrow">→</div>
    <div class="upload-step">
        <div class="upload-step-n">2</div>
        <div class="upload-step-t">Faça upload do extrato PDF</div>
    </div>
    <div class="upload-step-arrow">→</div>
    <div class="upload-step">
        <div class="upload-step-n">3</div>
        <div class="upload-step-t">Baixe as planilhas de cálculo geradas</div>
    </div>
</div>
""", unsafe_allow_html=True)

upload = st.file_uploader(
    "Arraste o extrato bancário em PDF ou clique para selecionar",
    type=["pdf"],
    help="Suporta extratos Bradesco em PDF. Múltiplas páginas aceitas."
)

if not upload:
    # ── SEÇÃO "COMO FUNCIONA" — preenche o espaço quando não há PDF ──────────
    st.markdown("""
<div style="margin-top: 52px;">
<div class="em-divider">
    <div class="em-divider-line"></div>
    <div class="em-divider-pill">
        <span class="em-divider-label">Como Funciona</span>
    </div>
    <div class="em-divider-line"></div>
</div>
</div>
""", unsafe_allow_html=True)

    h1, h2, h3 = st.columns(3)
    with h1:
        st.markdown("""
<div class="how-card">
    <div class="how-num">01</div>
    <div class="how-icon">
        <svg viewBox="0 0 24 24" width="28" height="28" stroke="#C5A566" fill="none" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="16" y1="13" x2="8" y2="13"/>
            <line x1="16" y1="17" x2="8" y2="17"/>
            <polyline points="10 9 9 9 8 9"/>
        </svg>
    </div>
    <div class="how-title">Faça o Upload</div>
    <div class="how-desc">
        Importe o extrato bancário em PDF diretamente do seu computador.
        O sistema aceita extratos Bradesco com múltiplas páginas e anos.
    </div>
    <div class="how-tip">✦ Suporta extratos de vários anos em um único PDF</div>
</div>
""", unsafe_allow_html=True)

    with h2:
        st.markdown("""
<div class="how-card how-card--center">
    <div class="how-num">02</div>
    <div class="how-icon">
        <svg viewBox="0 0 24 24" width="28" height="28" stroke="#C5A566" fill="none" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"/>
            <line x1="21" y1="21" x2="16.65" y2="16.65"/>
            <line x1="11" y1="8" x2="11" y2="14"/>
            <line x1="8" y1="11" x2="14" y2="11"/>
        </svg>
    </div>
    <div class="how-title">Análise Automática</div>
    <div class="how-desc">
        O motor de auditoria lê cada linha do extrato, identifica datas,
        valores e rubricas indevidas com precisão posicional por coluna.
    </div>
    <div class="how-tip">✦ Distingue débitos de créditos automaticamente</div>
</div>
""", unsafe_allow_html=True)

    with h3:
        st.markdown("""
<div class="how-card">
    <div class="how-num">03</div>
    <div class="how-icon">
        <svg viewBox="0 0 24 24" width="28" height="28" stroke="#C5A566" fill="none" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="7 10 12 15 17 10"/>
            <line x1="12" y1="15" x2="12" y2="3"/>
        </svg>
    </div>
    <div class="how-title">Baixe as Planilhas</div>
    <div class="how-desc">
        Gera planilhas Excel por rubrica com tabela mensal/anual e cálculo
        do valor em dobro conforme Art. 42 do Código de Defesa do Consumidor.
    </div>
    <div class="how-tip">✦ Pronta para uso jurídico e peticionamento</div>
</div>
""", unsafe_allow_html=True)

    # Seção de rubricas suportadas
    st.markdown("""
<div style="margin-top: 48px;">
<div class="em-divider">
    <div class="em-divider-line"></div>
    <div class="em-divider-pill">
        <span class="em-divider-label">Rubricas Monitoradas</span>
    </div>
    <div class="em-divider-line"></div>
</div>
<div class="em-section-note">
    Selecione na barra lateral as cobranças que deseja auditar
</div>
</div>
""", unsafe_allow_html=True)

    r1, r2, r3 = st.columns(3)
    rubricas_info = [
        ("Cesta / Pacote", "Tarifas de manutenção de conta — frequentemente cobradas mesmo sem contratação formal"),
        ("Mora Crédito Pessoal", "Juros de mora sobre contratos de crédito pessoal — podem ser abusivos ou duplicados"),
        ("Encargos de Limite", "Cobranças sobre limite de crédito — verifique se há contratação expressa"),
        ("Anuidade de Cartão", "Taxa anual cobrada mesmo em cartões sem anuidade contratada"),
        ("Parcela Crédito Pessoal", "Parcelas de empréstimos — identifica cobranças após liquidação"),
        ("Seguro / Previdência", "Seguros vinculados a contas sem consentimento expresso do titular"),
    ]
    cols = [r1, r2, r3]
    for i, (titulo, desc) in enumerate(rubricas_info):
        with cols[i % 3]:
            st.markdown(f"""
<div class="rub-card">
    <div class="rub-title">{titulo}</div>
    <div class="rub-desc">{desc}</div>
</div>
""", unsafe_allow_html=True)

    # CSS das novas seções
    st.markdown("""
<style>
/* ── Como Funciona ──────────────────────────────────────────────────────── */
.how-card {
    background: linear-gradient(145deg, var(--p3, #111823) 0%, var(--p2, #0A0F18) 100%);
    border: 1px solid rgba(197,165,102,0.1);
    border-radius: 16px;
    padding: 28px 24px;
    height: 100%;
    position: relative;
    transition: all 0.35s cubic-bezier(.22,1,.36,1);
}
.how-card:hover {
    border-color: rgba(197,165,102,0.28);
    transform: translateY(-4px);
    box-shadow: 0 20px 50px rgba(0,0,0,0.4), 0 0 20px rgba(197,165,102,0.06);
}
.how-card--center {
    border-top: 2px solid rgba(197,165,102,0.4);
}
.how-num {
    font-family: 'Cormorant Garamond', Georgia, serif;
    font-size: 3.5rem; font-weight: 300; line-height: 1;
    color: rgba(197,165,102,0.1); margin-bottom: 14px;
    letter-spacing: -1px;
}
.how-icon {
    margin-bottom: 16px;
    width: 48px; height: 48px;
    background: rgba(197,165,102,0.06);
    border: 1px solid rgba(197,165,102,0.14);
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    transition: all 0.3s ease;
}
.how-card:hover .how-icon {
    background: rgba(197,165,102,0.12);
    border-color: rgba(197,165,102,0.3);
}
.how-title {
    font-family: 'Cormorant Garamond', Georgia, serif;
    font-size: 1.35rem; font-weight: 600; color: #EDE5D4;
    margin-bottom: 12px; letter-spacing: 0.3px;
}
.how-desc {
    font-size: 0.85rem; color: rgba(237,229,212,0.4);
    line-height: 1.7; letter-spacing: 0.2px;
    margin-bottom: 16px;
}
.how-tip {
    font-size: 0.72rem; color: rgba(197,165,102,0.45);
    letter-spacing: 0.3px; line-height: 1.5;
    padding-top: 14px;
    border-top: 1px solid rgba(197,165,102,0.08);
}

/* ── Rubricas info ──────────────────────────────────────────────────────── */
.rub-card {
    background: rgba(197,165,102,0.03);
    border: 1px solid rgba(197,165,102,0.08);
    border-radius: 12px;
    padding: 20px 18px;
    margin-bottom: 10px;
    transition: all 0.25s ease;
}
.rub-card:hover {
    background: rgba(197,165,102,0.06);
    border-color: rgba(197,165,102,0.2);
}
.rub-title {
    font-family: 'Cormorant Garamond', Georgia, serif;
    font-size: 1.05rem; font-weight: 600;
    color: rgba(197,165,102,0.85); margin-bottom: 7px;
}
.rub-desc {
    font-size: 0.8rem; color: rgba(237,229,212,0.32);
    line-height: 1.6; letter-spacing: 0.2px;
}
</style>
""", unsafe_allow_html=True)

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
                st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-icon">
                        <svg viewBox="0 0 24 24"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
                    </div>
                    <h4>Total Recuperável</h4>
                    <h2>R$ {total_geral:,.2f}</h2>
                    <div class="metric-card-sub">Soma de todos os débitos indevidos identificados</div>
                </div>
                ''', unsafe_allow_html=True)
            with c2:
                st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-icon">
                        <svg viewBox="0 0 24 24"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
                    </div>
                    <h4>Lançamentos</h4>
                    <h2>{len(df)}</h2>
                    <div class="metric-card-sub">Registros de cobranças identificadas no extrato</div>
                </div>
                ''', unsafe_allow_html=True)
            with c3:
                st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-icon">
                        <svg viewBox="0 0 24 24"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/><line x1="7" y1="7" x2="7.01" y2="7"/></svg>
                    </div>
                    <h4>Categorias</h4>
                    <h2>{cats_unicas}</h2>
                    <div class="metric-card-sub">Tipos de rubrica distintas encontradas no período</div>
                </div>
                ''', unsafe_allow_html=True)

            st.markdown(f'''
<div class="em-divider" style="margin-top:40px;">
    <div class="em-divider-line"></div>
    <div class="em-divider-pill">
        <span class="em-divider-label">Planilhas de Cálculo</span>
        <span class="em-divider-num">{len(cats_unicas_list) if False else ""}</span>
    </div>
    <div class="em-divider-line"></div>
</div>
<div class="em-section-note">
    Cada planilha inclui tabela mensal, total anual e valor em dobro (Art. 42 CDC) — prontas para uso jurídico
</div>
''', unsafe_allow_html=True)

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

            st.markdown(f'''
<div class="em-divider" style="margin-top:40px;">
    <div class="em-divider-line"></div>
    <div class="em-divider-pill">
        <span class="em-divider-label">Lançamentos Identificados</span>
        <span class="em-divider-num">— {len(df)} registros</span>
    </div>
    <div class="em-divider-line"></div>
</div>
<div class="em-section-note">
    Ordenados cronologicamente · Somente débitos · Valores confirmados por posição de coluna no PDF
</div>
''', unsafe_allow_html=True)
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
