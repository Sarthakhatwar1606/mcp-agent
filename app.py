import compat  # noqa: F401 — must be first, stubs broken protobuf modules
import json
import subprocess
import sys
from pathlib import Path

import chromadb
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="MCP Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; }
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
#MainMenu, footer, .stDeployButton { visibility: hidden; }

/* ── Animated starfield background ───────────────────── */
.stApp {
    background: #02050F;
    background-image:
        radial-gradient(ellipse 100% 60% at 10% -5%,  rgba(99,102,241,0.18) 0%, transparent 55%),
        radial-gradient(ellipse 70%  50% at 90%  110%, rgba(139,92,246,0.14) 0%, transparent 55%),
        radial-gradient(ellipse 50%  40% at 50%  60%,  rgba(6,182,212,0.06)  0%, transparent 65%);
}
.main .block-container { padding-top: 0 !important; max-width: 1400px; }

/* ── Scrollbar ────────────────────────────────────────── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(99,102,241,0.35); border-radius: 3px; }

/* ── Floating particles (pure CSS) ───────────────────── */
.particles { position: fixed; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 0; overflow: hidden; }
.particle {
    position: absolute; border-radius: 50%; opacity: 0;
    animation: rise linear infinite;
}
@keyframes rise {
    0%   { transform: translateY(100vh) scale(0);  opacity: 0; }
    10%  { opacity: 0.6; }
    90%  { opacity: 0.3; }
    100% { transform: translateY(-10vh) scale(1.2); opacity: 0; }
}

/* ── Hero banner ──────────────────────────────────────── */
.hero {
    position: relative; overflow: hidden;
    background: linear-gradient(135deg,
        rgba(15,23,42,0.95) 0%,
        rgba(30,27,75,0.95) 50%,
        rgba(15,23,42,0.95) 100%);
    border: 1px solid rgba(99,102,241,0.3);
    border-radius: 24px;
    padding: 32px 40px 28px;
    margin-bottom: 24px;
}
.hero-glow-1 {
    position: absolute; top: -80px; right: -80px;
    width: 300px; height: 300px; border-radius: 50%;
    background: radial-gradient(circle, rgba(99,102,241,0.35) 0%, transparent 65%);
    animation: orb 5s ease-in-out infinite;
}
.hero-glow-2 {
    position: absolute; bottom: -60px; left: 20%;
    width: 200px; height: 200px; border-radius: 50%;
    background: radial-gradient(circle, rgba(6,182,212,0.25) 0%, transparent 65%);
    animation: orb 7s ease-in-out infinite reverse;
}
.hero-glow-3 {
    position: absolute; top: 10px; left: 40%;
    width: 150px; height: 150px; border-radius: 50%;
    background: radial-gradient(circle, rgba(139,92,246,0.2) 0%, transparent 65%);
    animation: orb 6s ease-in-out infinite 2s;
}
@keyframes orb {
    0%, 100% { transform: scale(1) translate(0,0); }
    33%       { transform: scale(1.1) translate(10px,-10px); }
    66%       { transform: scale(0.95) translate(-8px, 8px); }
}
.hero-content { position: relative; z-index: 1; }
.hero-eyebrow {
    font-size: 0.72rem; font-weight: 700; letter-spacing: 3px;
    text-transform: uppercase; color: #6366F1; margin-bottom: 10px;
}
.hero-title {
    font-size: 2.6rem; font-weight: 900; letter-spacing: -1.5px; line-height: 1.1;
    background: linear-gradient(135deg, #fff 0%, #A5B4FC 45%, #67E8F9 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; margin-bottom: 10px;
}
.hero-sub { color: #475569; font-size: 0.92rem; font-weight: 400; margin-bottom: 20px; }
.badge {
    display: inline-flex; align-items: center; gap: 5px;
    padding: 4px 12px; border-radius: 99px; margin-right: 6px; margin-bottom: 4px;
    font-size: 0.72rem; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase;
    border: 1px solid;
}
.badge-indigo { background: rgba(99,102,241,0.15);  border-color: rgba(99,102,241,0.35);  color: #A5B4FC; }
.badge-cyan   { background: rgba(6,182,212,0.12);   border-color: rgba(6,182,212,0.3);    color: #67E8F9; }
.badge-purple { background: rgba(139,92,246,0.12);  border-color: rgba(139,92,246,0.3);   color: #C4B5FD; }
.badge-green  { background: rgba(16,185,129,0.12);  border-color: rgba(16,185,129,0.3);   color: #34D399; }
.badge-amber  { background: rgba(245,158,11,0.12);  border-color: rgba(245,158,11,0.3);   color: #FCD34D; }

/* ── 3D stat cards ────────────────────────────────────── */
.card-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin: 20px 0; }
.card-3d {
    perspective: 800px;
}
.card-3d-inner {
    position: relative; padding: 22px 20px;
    background: linear-gradient(145deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 18px;
    transform: rotateX(4deg) rotateY(-2deg);
    transform-style: preserve-3d;
    transition: transform 0.4s ease, box-shadow 0.4s ease;
    box-shadow: 0 20px 60px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.04) inset;
}
.card-3d-inner:hover {
    transform: rotateX(0deg) rotateY(0deg) translateY(-4px);
    box-shadow: 0 30px 80px rgba(0,0,0,0.5), 0 0 30px rgba(99,102,241,0.15);
}
.card-3d-inner::before {
    content: ''; position: absolute; inset: 0; border-radius: 18px;
    background: linear-gradient(135deg, rgba(255,255,255,0.08) 0%, transparent 50%);
    pointer-events: none;
}
.card-icon { font-size: 1.8rem; margin-bottom: 10px; display: block; }
.card-value {
    font-size: 2rem; font-weight: 800; letter-spacing: -1px;
    background: linear-gradient(135deg, #fff, #A5B4FC);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
}
.card-label { font-size: 0.75rem; color: #475569; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-top: 4px; }
.card-sub   { font-size: 0.7rem;  color: #334155; margin-top: 8px; }
.card-accent-1 { border-color: rgba(99,102,241,0.25) !important; }
.card-accent-2 { border-color: rgba(6,182,212,0.25)  !important; }
.card-accent-3 { border-color: rgba(139,92,246,0.25) !important; }
.card-accent-4 { border-color: rgba(16,185,129,0.25) !important; }

/* ── Automation pipeline ──────────────────────────────── */
.pipeline {
    display: flex; align-items: center; gap: 0;
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(99,102,241,0.15);
    border-radius: 16px;
    padding: 18px 24px;
    margin: 16px 0;
    overflow-x: auto;
}
.pipe-step {
    display: flex; flex-direction: column; align-items: center;
    gap: 6px; min-width: 90px; flex-shrink: 0;
}
.pipe-icon {
    width: 48px; height: 48px; border-radius: 14px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.3rem; position: relative;
    border: 1px solid rgba(255,255,255,0.1);
}
.pipe-icon.active {
    box-shadow: 0 0 20px var(--glow);
    animation: pipe-pulse 2s ease-in-out infinite;
}
@keyframes pipe-pulse {
    0%, 100% { box-shadow: 0 0 10px var(--glow); }
    50%       { box-shadow: 0 0 25px var(--glow), 0 0 50px var(--glow); }
}
.pipe-label { font-size: 0.65rem; color: #475569; font-weight: 600; text-align: center; text-transform: uppercase; letter-spacing: 0.5px; }
.pipe-arrow {
    flex: 1; height: 2px; min-width: 30px; max-width: 60px;
    background: linear-gradient(90deg, rgba(99,102,241,0.5), rgba(6,182,212,0.5));
    position: relative; margin: 0 4px; margin-bottom: 20px;
}
.pipe-arrow::after {
    content: ''; position: absolute; right: -5px; top: -4px;
    border: 5px solid transparent;
    border-left-color: rgba(6,182,212,0.7);
}
.pipe-dot {
    position: absolute; top: -3px; left: 0;
    width: 8px; height: 8px; border-radius: 50%;
    background: #67E8F9; box-shadow: 0 0 8px #67E8F9;
    animation: flow 2s linear infinite;
}
@keyframes flow {
    0%   { left: 0; opacity: 0; }
    10%  { opacity: 1; }
    90%  { opacity: 1; }
    100% { left: calc(100% - 8px); opacity: 0; }
}

/* ── Tool call terminal ───────────────────────────────── */
.terminal {
    background: #0A0F1A; border: 1px solid rgba(6,182,212,0.2);
    border-radius: 14px; overflow: hidden; margin: 8px 0;
}
.terminal-bar {
    display: flex; align-items: center; gap: 6px;
    background: rgba(6,182,212,0.08); padding: 10px 16px;
    border-bottom: 1px solid rgba(6,182,212,0.15);
}
.t-dot { width: 10px; height: 10px; border-radius: 50%; }
.t-dot-r { background: #EF4444; }
.t-dot-y { background: #F59E0B; }
.t-dot-g { background: #10B981; }
.terminal-title { font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #475569; margin-left: 6px; }
.terminal-body { padding: 14px 16px; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; line-height: 1.7; }
.t-prompt  { color: #6366F1; }
.t-cmd     { color: #67E8F9; }
.t-arg     { color: #C4B5FD; }
.t-result  { color: #34D399; }
.t-comment { color: #334155; }

/* ── Result cards ─────────────────────────────────────── */
.result-card {
    background: linear-gradient(135deg, rgba(99,102,241,0.08) 0%, rgba(139,92,246,0.05) 100%);
    border: 1px solid rgba(99,102,241,0.2);
    border-radius: 16px;
    padding: 20px 24px;
    margin: 10px 0;
    position: relative;
    overflow: hidden;
}
.result-card::before {
    content: ''; position: absolute; left: 0; top: 0; bottom: 0;
    width: 3px;
    background: linear-gradient(180deg, #6366F1, #8B5CF6, #67E8F9);
    border-radius: 3px 0 0 3px;
}

/* ── Chat ─────────────────────────────────────────────── */
[data-testid="stChatMessage"] {
    border-radius: 16px !important;
    margin-bottom: 12px !important;
    padding: 16px 20px !important;
    border: 1px solid transparent !important;
    transition: border-color 0.2s !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    background: linear-gradient(135deg, rgba(99,102,241,0.1) 0%, rgba(99,102,241,0.05) 100%) !important;
    border-color: rgba(99,102,241,0.25) !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
    background: rgba(255,255,255,0.025) !important;
    border-color: rgba(255,255,255,0.07) !important;
}
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] li,
[data-testid="stChatMessage"] span { color: #CBD5E1 !important; }
[data-testid="stChatMessage"] code {
    color: #67E8F9 !important; background: rgba(6,182,212,0.12) !important;
    border-radius: 5px; font-family: 'JetBrains Mono', monospace;
}

/* ── Chat input ───────────────────────────────────────── */
[data-testid="stChatInput"] > div {
    background: rgba(15,23,42,0.9) !important;
    border: 1px solid rgba(99,102,241,0.35) !important;
    border-radius: 16px !important;
    box-shadow: 0 0 30px rgba(99,102,241,0.1), 0 4px 20px rgba(0,0,0,0.3) !important;
}
[data-testid="stChatInput"] > div:focus-within {
    border-color: rgba(99,102,241,0.65) !important;
    box-shadow: 0 0 40px rgba(99,102,241,0.2), 0 4px 20px rgba(0,0,0,0.3) !important;
}
[data-testid="stChatInput"] textarea { color: #E2E8F0 !important; }

/* ── Tabs ─────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 2px; background: transparent;
    border-bottom: 1px solid rgba(99,102,241,0.12);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px 10px 0 0; padding: 10px 22px;
    font-weight: 500; font-size: 0.85rem; color: #334155; background: transparent;
}
.stTabs [data-baseweb="tab"]:hover { color: #A5B4FC; }
.stTabs [aria-selected="true"] {
    background: rgba(99,102,241,0.1) !important;
    color: #A5B4FC !important;
    border-top: 2px solid #6366F1 !important;
    font-weight: 600 !important;
}

/* ── Sidebar ──────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #060B18 0%, #02050F 100%) !important;
    border-right: 1px solid rgba(99,102,241,0.12) !important;
}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] div  { color: #64748B !important; }
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3   { color: #E2E8F0 !important; }
section[data-testid="stSidebar"] hr   { border-color: rgba(99,102,241,0.1) !important; }
section[data-testid="stSidebar"] .stButton > button {
    background: rgba(255,255,255,0.02) !important;
    border: 1px solid rgba(99,102,241,0.18) !important;
    color: #64748B !important; border-radius: 8px !important;
    font-size: 0.78rem !important; text-align: left !important;
    transition: all 0.2s !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(99,102,241,0.1) !important;
    border-color: rgba(99,102,241,0.4) !important;
    color: #A5B4FC !important; transform: translateX(4px) !important;
}
section[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(99,102,241,0.22) !important;
    border-radius: 8px !important; color: #E2E8F0 !important;
}

/* ── Status ───────────────────────────────────────────── */
[data-testid="stStatus"] {
    background: rgba(6,182,212,0.05) !important;
    border: 1px solid rgba(6,182,212,0.2) !important;
    border-radius: 14px !important;
}
[data-testid="stStatus"] p, [data-testid="stStatus"] span { color: #67E8F9 !important; }

/* ── Misc ─────────────────────────────────────────────── */
.stCode, [data-testid="stCode"] {
    border-radius: 10px !important;
    border: 1px solid rgba(99,102,241,0.12) !important;
    background: rgba(0,0,0,0.5) !important;
    font-family: 'JetBrains Mono', monospace !important;
}
details {
    border: 1px solid rgba(99,102,241,0.15) !important;
    border-radius: 12px !important;
    background: rgba(99,102,241,0.03) !important; margin: 6px 0 !important;
}
details summary { color: #A5B4FC !important; font-weight: 500 !important; font-size: 0.84rem !important; padding: 10px 14px !important; }
[data-testid="stMetric"] {
    background: rgba(255,255,255,0.025) !important;
    border: 1px solid rgba(99,102,241,0.15) !important;
    border-radius: 14px !important; padding: 16px 20px !important;
}
[data-testid="stMetricValue"] { color: #A5B4FC !important; font-size: 1.6rem !important; font-weight: 800 !important; }
[data-testid="stMetricLabel"] { color: #334155 !important; font-size: 0.72rem !important; text-transform: uppercase; letter-spacing: 1px; }
[data-testid="stDataFrame"] { border: 1px solid rgba(99,102,241,0.15) !important; border-radius: 14px !important; overflow: hidden !important; }
[data-testid="stAlert"] { border-radius: 12px !important; }
[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(255,255,255,0.015) !important;
    border: 1px solid rgba(99,102,241,0.12) !important; border-radius: 14px !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%) !important;
    border: none !important; border-radius: 10px !important;
    font-weight: 700 !important; color: white !important;
    box-shadow: 0 4px 20px rgba(99,102,241,0.4) !important;
    transition: all 0.2s !important;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 6px 30px rgba(99,102,241,0.6) !important;
    transform: translateY(-2px) !important;
}
.stButton > button[kind="secondary"] {
    border-radius: 10px !important;
    border: 1px solid rgba(99,102,241,0.3) !important;
    color: #A5B4FC !important; background: rgba(99,102,241,0.07) !important;
}
.stTextInput > div > div > input, .stTextArea > div > textarea {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(99,102,241,0.25) !important;
    border-radius: 10px !important; color: #E2E8F0 !important;
}
hr { border-color: rgba(99,102,241,0.1) !important; }
.main p, .main li { color: #64748B; }
.main h1, .main h2, .main h3 { color: #E2E8F0 !important; }
[data-testid="collapsedControl"] {
    background: #6366F1 !important;
    border-radius: 0 8px 8px 0 !important;
    color: white !important; opacity: 1 !important; visibility: visible !important;
}
[data-testid="collapsedControl"] svg { fill: white !important; }

/* ── Empty chat ───────────────────────────────────────── */
.empty-state {
    display: flex; flex-direction: column; align-items: center;
    padding: 64px 20px; text-align: center; gap: 12px;
}
.empty-icon {
    font-size: 4rem; animation: levitate 4s ease-in-out infinite;
    filter: drop-shadow(0 0 30px rgba(99,102,241,0.7));
}
@keyframes levitate {
    0%, 100% { transform: translateY(0) rotate(-5deg); }
    50%       { transform: translateY(-12px) rotate(5deg); }
}
.empty-title { color: #E2E8F0; font-size: 1.3rem; font-weight: 700; }
.empty-sub   { color: #334155; font-size: 0.85rem; max-width: 400px; }
.chip-row    { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; margin-top: 6px; }
.chip {
    background: rgba(99,102,241,0.1); border: 1px solid rgba(99,102,241,0.25);
    color: #A5B4FC; padding: 7px 16px; border-radius: 99px;
    font-size: 0.78rem; font-weight: 500; cursor: default;
}

/* ── Sidebar logo ─────────────────────────────────────── */
.sb-brand { display: flex; align-items: center; gap: 10px; padding: 4px 0 12px; }
.sb-icon {
    width: 38px; height: 38px; border-radius: 12px;
    background: linear-gradient(135deg, #6366F1, #8B5CF6);
    display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem; box-shadow: 0 0 20px rgba(99,102,241,0.5);
    flex-shrink: 0;
}
.sb-name    { font-size: 1rem; font-weight: 800; color: #E2E8F0 !important; }
.sb-version { font-size: 0.68rem; color: #1E293B !important; margin-top: 1px; }

/* ── Live dot ─────────────────────────────────────────── */
.live-pill {
    display: flex; align-items: center; gap: 8px;
    background: rgba(16,185,129,0.08); border: 1px solid rgba(16,185,129,0.2);
    border-radius: 10px; padding: 9px 14px; margin: 8px 0;
}
.live-dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: #10B981; box-shadow: 0 0 8px #10B981;
    animation: blink 2s ease-in-out infinite; flex-shrink: 0;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.3} }
.live-label { font-size: 0.78rem; font-weight: 600; color: #34D399 !important; }

/* ── Dashboard section label ──────────────────────────── */
.section-label {
    font-size: 0.68rem; font-weight: 700; letter-spacing: 2px;
    text-transform: uppercase; color: #1E293B !important; margin-bottom: 8px;
    display: block;
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ── Floating particles ──────────────────────────────────────────────────────────
PARTICLE_HTML = """
<div class="particles">
""" + "".join([
    f'<div class="particle" style="'
    f'left:{(i*37+13)%100}%;'
    f'width:{2+(i%3)}px;height:{2+(i%3)}px;'
    f'background:{"#6366F1" if i%3==0 else "#67E8F9" if i%3==1 else "#8B5CF6"};'
    f'animation-duration:{8+(i%7)}s;'
    f'animation-delay:{(i*1.3)%8}s;'
    f'opacity:0.4;'
    f'"></div>'
    for i in range(25)
]) + "</div>"
st.markdown(PARTICLE_HTML, unsafe_allow_html=True)

# ── Data helpers ────────────────────────────────────────────────────────────────
DATA_DIR    = Path(__file__).parent / "data"
DB_PATH     = DATA_DIR / "catalog.duckdb"
CHROMA_PATH = str(DATA_DIR / "chromadb")

import os as _os
_ON_CLOUD = bool(_os.environ.get("GROQ_API_KEY", ""))

OLLAMA_MODELS = {
    "llama3.2:3b  — recommended":  "llama3.2:3b",
    "llama3.2:1b  — smallest":     "llama3.2:1b",
    "llama3.1     — 4.9 GB":       "llama3.1",
    "phi3.5:mini  — 2.2 GB":       "phi3.5:mini",
    "mistral      — 4.1 GB":       "mistral",
}
GROQ_MODELS = {
    "llama-3.3-70b  — best (Groq)":    "llama-3.3-70b-versatile",
    "llama-3.1-8b   — fast (Groq)":    "llama-3.1-8b-instant",
    "mixtral-8x7b   — balanced (Groq)": "mixtral-8x7b-32768",
}
MODELS = GROQ_MODELS if _ON_CLOUD else OLLAMA_MODELS

SAMPLE_QUESTIONS = [
    "What tables are in the data catalog?",
    "Show the top 3 highest paid employees",
    "What's our Q2 2024 total revenue by region?",
    "Which project has the largest budget?",
    "Find documents about security policy",
    "What's the average salary per department?",
    "Search for AI recommendation engine docs",
    "How many employees were hired after 2022?",
]

for k, v in {"messages": [], "chat_model": "llama3.2:3b", "tool_history": []}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Auto-seed on first run (important on cloud where data/ is not committed)
_auto_seed()


def is_seeded() -> bool:
    return DB_PATH.exists()


def seed_data():
    r = subprocess.run(
        [sys.executable, str(Path(__file__).parent / "seed_data.py")],
        capture_output=True, text=True,
    )
    return r.returncode == 0, r.stdout + r.stderr


@st.cache_resource(show_spinner="Seeding data for first run…")
def _auto_seed():
    """Run once per deployment — seeds databases if they don't exist yet."""
    if not is_seeded():
        ok, log = seed_data()
        return ok, log
    return True, "already seeded"


def db_query(sql: str):
    db  = duckdb.connect(str(DB_PATH), read_only=True)
    df  = db.execute(sql).fetchdf()
    db.close()
    return df


def get_tables() -> list[str]:
    if not is_seeded():
        return []
    return [r[0] for r in db_query(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='main' ORDER BY table_name"
    ).itertuples(index=False)]


def get_chroma_docs() -> list[dict]:
    try:
        col = chromadb.PersistentClient(path=CHROMA_PATH).get_or_create_collection("documents")
        if col.count() == 0:
            return []
        d = col.get()
        return [{"id": d["ids"][i], "document": d["documents"][i], "metadata": d["metadatas"][i]}
                for i in range(len(d["ids"]))]
    except Exception:
        return []


def chroma_search(query: str, n: int = 5) -> list[dict]:
    col   = chromadb.PersistentClient(path=CHROMA_PATH).get_or_create_collection("documents")
    count = col.count()
    if count == 0:
        return []
    res = col.query(query_texts=[query], n_results=min(n, count))
    return [{"id": res["ids"][0][i], "score": round(1 - res["distances"][0][i], 4),
             "document": res["documents"][0][i], "metadata": res["metadatas"][0][i]}
            for i in range(len(res["documents"][0]))]


def add_chroma_doc(doc_id, content, category, source):
    col = chromadb.PersistentClient(path=CHROMA_PATH).get_or_create_collection("documents")
    col.add(documents=[content], ids=[doc_id], metadatas=[{"category": category, "source": source}])


# ── Plotly theme ────────────────────────────────────────────────────────────────
PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter", color="#94A3B8", size=12),
    margin=dict(l=0, r=0, t=30, b=0),
    colorway=["#6366F1", "#67E8F9", "#8B5CF6", "#34D399", "#F59E0B", "#EF4444"],
)

def apply_theme(fig):
    fig.update_layout(**PLOT_LAYOUT)
    fig.update_xaxes(gridcolor="rgba(99,102,241,0.08)", zerolinecolor="rgba(99,102,241,0.1)")
    fig.update_yaxes(gridcolor="rgba(99,102,241,0.08)", zerolinecolor="rgba(99,102,241,0.1)")
    return fig


# ── Sidebar ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sb-brand">
        <div class="sb-icon">⚡</div>
        <div>
            <div class="sb-name">MCP Intelligence</div>
            <div class="sb-version">v2.0 · LangGraph · Ollama</div>
        </div>
    </div>""", unsafe_allow_html=True)

    if is_seeded():
        st.markdown("""
        <div class="live-pill">
            <div class="live-dot"></div>
            <span class="live-label">All systems operational</span>
        </div>""", unsafe_allow_html=True)
    else:
        st.warning("Data not seeded", icon="⚠️")
        if st.button("Seed Sample Data", type="primary", use_container_width=True):
            with st.spinner("Seeding databases…"):
                ok, log = seed_data()
            st.success("Done!") if ok else st.error(f"Failed:\n{log}")
            if ok:
                st.rerun()

    st.divider()
    st.markdown('<span class="section-label">Model</span>', unsafe_allow_html=True)
    if _ON_CLOUD:
        st.markdown("<span style='font-size:0.72rem;color:#34D399'>☁️ Groq API detected</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span style='font-size:0.72rem;color:#F59E0B'>🖥️ Local Ollama mode</span>", unsafe_allow_html=True)
    label = st.selectbox("model", list(MODELS.keys()), label_visibility="collapsed")
    st.session_state.chat_model = MODELS[label]
    st.markdown(f"<code style='font-size:0.75rem;color:#6366F1'>{st.session_state.chat_model}</code>",
                unsafe_allow_html=True)

    st.divider()
    st.markdown('<span class="section-label">Quick Ask</span>', unsafe_allow_html=True)
    for q in SAMPLE_QUESTIONS:
        if st.button(q, use_container_width=True):
            st.session_state["prefill"] = q

    st.divider()
    cols_sb = st.columns(2)
    if cols_sb[0].button("Clear chat", use_container_width=True):
        st.session_state.messages     = []
        st.session_state.tool_history = []
        st.rerun()
    if cols_sb[1].button("Clear tools", use_container_width=True):
        st.session_state.tool_history = []
        st.rerun()

    st.divider()
    st.markdown("""
    <div style='font-size:0.7rem;line-height:2'>
        <span class='badge badge-indigo'>MCP</span>
        <span class='badge badge-cyan'>DuckDB</span>
        <span class='badge badge-purple'>ChromaDB</span>
        <span class='badge badge-green'>Ollama</span><br>
        <span style='color:#1E293B'>100% local · no cloud · no cost</span>
    </div>""", unsafe_allow_html=True)


# ── Hero ─────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-glow-1"></div>
    <div class="hero-glow-2"></div>
    <div class="hero-glow-3"></div>
    <div class="hero-content">
        <p class="hero-eyebrow">Enterprise AI · Tool-Calling Agent</p>
        <h1 class="hero-title">MCP Intelligence</h1>
        <p class="hero-sub">Ask questions in plain English. The agent decides which tools to call, queries your databases, searches your documents, and returns structured answers — all locally.</p>
        <div>
            <span class='badge badge-green'>● Live</span>
            <span class='badge badge-indigo'>LangGraph ReAct</span>
            <span class='badge badge-cyan'>DuckDB · SQL</span>
            <span class='badge badge-purple'>ChromaDB · Vectors</span>
            <span class='badge badge-amber'>Ollama · Local LLM</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Main tabs ─────────────────────────────────────────────────────────────────────
tab_chat, tab_dash, tab_catalog, tab_docs = st.tabs([
    "💬  Agent Chat",
    "📊  Dashboard",
    "🗄️  Data Catalog",
    "📚  Knowledge Base",
])


# ═══════════════════════════════════════════════════════════════
# TAB 1 — CHAT
# ═══════════════════════════════════════════════════════════════
with tab_chat:
    if not is_seeded():
        st.info("Seed sample data first using the sidebar button.", icon="ℹ️")
        st.stop()

    # ── Automation pipeline visualiser ──────────────────────────────────────────
    st.markdown("""
    <div class="pipeline">
        <div class="pipe-step">
            <div class="pipe-icon active" style="background:rgba(99,102,241,0.15);--glow:rgba(99,102,241,0.6)">💬</div>
            <span class="pipe-label">Question</span>
        </div>
        <div class="pipe-arrow"><div class="pipe-dot"></div></div>
        <div class="pipe-step">
            <div class="pipe-icon active" style="background:rgba(139,92,246,0.15);--glow:rgba(139,92,246,0.6)">🧠</div>
            <span class="pipe-label">LLM Reason</span>
        </div>
        <div class="pipe-arrow"><div class="pipe-dot" style="animation-delay:0.5s"></div></div>
        <div class="pipe-step">
            <div class="pipe-icon active" style="background:rgba(6,182,212,0.15);--glow:rgba(6,182,212,0.6)">🔧</div>
            <span class="pipe-label">Tool Call</span>
        </div>
        <div class="pipe-arrow"><div class="pipe-dot" style="animation-delay:1s"></div></div>
        <div class="pipe-step">
            <div class="pipe-icon active" style="background:rgba(245,158,11,0.15);--glow:rgba(245,158,11,0.6)">🗄️</div>
            <span class="pipe-label">DuckDB</span>
        </div>
        <div class="pipe-arrow"><div class="pipe-dot" style="animation-delay:1.3s"></div></div>
        <div class="pipe-step">
            <div class="pipe-icon active" style="background:rgba(99,102,241,0.15);--glow:rgba(99,102,241,0.6)">🔮</div>
            <span class="pipe-label">ChromaDB</span>
        </div>
        <div class="pipe-arrow"><div class="pipe-dot" style="animation-delay:1.6s"></div></div>
        <div class="pipe-step">
            <div class="pipe-icon active" style="background:rgba(16,185,129,0.15);--glow:rgba(16,185,129,0.6)">✅</div>
            <span class="pipe-label">Answer</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Chat history ─────────────────────────────────────────────────────────────
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant":
                if msg.get("tool_calls"):
                    with st.expander(f"🔧 {len(msg['tool_calls'])} tool call(s)", expanded=False):
                        for tc in msg["tool_calls"]:
                            st.markdown(f"`{tc['name']}`")
                            st.code(json.dumps(tc["args"], indent=2), language="json")
                if msg.get("tool_results"):
                    with st.expander("📦 Tool results", expanded=False):
                        for tr in msg["tool_results"]:
                            st.markdown(f"`{tr['tool']}`")
                            try:
                                st.code(json.dumps(json.loads(tr["content"]), indent=2)[:800], language="json")
                            except Exception:
                                st.code(tr["content"][:800])
                st.markdown(msg["content"])
            else:
                st.markdown(msg["content"])

    # ── Empty state ───────────────────────────────────────────────────────────────
    if not st.session_state.messages:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">🤖</div>
            <p class="empty-title">Your enterprise AI is ready</p>
            <p class="empty-sub">Ask anything about employees, projects, revenue, or company documents. The agent picks the right tool automatically.</p>
            <div class="chip-row">
                <span class="chip">Top paid employees</span>
                <span class="chip">Q2 revenue by region</span>
                <span class="chip">Security policy</span>
                <span class="chip">AI project budgets</span>
                <span class="chip">Hiring trends</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Input & agent execution ───────────────────────────────────────────────────
    prefill    = st.session_state.pop("prefill", None)
    user_input = st.chat_input("Ask anything about your enterprise data…") or prefill

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        tool_calls   = []
        tool_results = []
        answer       = ""

        with st.chat_message("assistant"):
            with st.status("⚡ Agent reasoning…", expanded=True) as status:
                try:
                    from agent import run_agent
                    for event in run_agent(user_input, st.session_state.chat_model):
                        if event["type"] == "tool_call":
                            tool_calls.append(event)
                            st.markdown(f"""
                            <div class="terminal">
                                <div class="terminal-bar">
                                    <div class="t-dot t-dot-r"></div>
                                    <div class="t-dot t-dot-y"></div>
                                    <div class="t-dot t-dot-g"></div>
                                    <span class="terminal-title">mcp-tool-call</span>
                                </div>
                                <div class="terminal-body">
                                    <span class="t-prompt">▶ </span>
                                    <span class="t-cmd">{event['name']}</span>
                                    <span class="t-arg">(</span>
                                    <span class="t-arg">{', '.join(f'{k}={repr(v)}' for k,v in event['args'].items())}</span>
                                    <span class="t-arg">)</span>
                                </div>
                            </div>""", unsafe_allow_html=True)

                        elif event["type"] == "tool_result":
                            tool_results.append(event)
                            try:
                                parsed = json.loads(event["content"])
                                preview = json.dumps(parsed, indent=2)[:500]
                            except Exception:
                                preview = event["content"][:500]
                            st.markdown(f"""
                            <div class="terminal">
                                <div class="terminal-bar">
                                    <div class="t-dot t-dot-r"></div>
                                    <div class="t-dot t-dot-y"></div>
                                    <div class="t-dot t-dot-g"></div>
                                    <span class="terminal-title">{event['tool']} → result</span>
                                </div>
                                <div class="terminal-body">
                                    <span class="t-result">{preview}</span>
                                </div>
                            </div>""", unsafe_allow_html=True)

                        elif event["type"] == "answer":
                            answer = event["content"]

                        elif event["type"] == "error":
                            answer = f"Error: {event['content']}"
                            if "connection refused" in event["content"].lower():
                                answer += "\n\n> Make sure Ollama is running: `ollama serve`"

                    status.update(label=f"✅ Done — {len(tool_calls)} tool call(s)", state="complete", expanded=False)
                except Exception as e:
                    status.update(label="❌ Error", state="error")
                    answer = f"Agent error: {e}"

            st.markdown(answer or "_No response generated._")

        # Save to history for Dashboard tab
        st.session_state.tool_history.append({
            "question":     user_input,
            "tool_calls":   [t["name"] for t in tool_calls],
            "answer":       answer,
        })

        st.session_state.messages.append({
            "role":         "assistant",
            "content":      answer,
            "tool_calls":   tool_calls,
            "tool_results": tool_results,
        })


# ═══════════════════════════════════════════════════════════════
# TAB 2 — DASHBOARD
# ═══════════════════════════════════════════════════════════════
with tab_dash:
    if not is_seeded():
        st.info("Seed sample data from the sidebar first.", icon="ℹ️")
        st.stop()

    emp = db_query("SELECT * FROM employees")
    prj = db_query("SELECT * FROM projects")
    sal = db_query("SELECT * FROM sales")

    # ── 3D KPI cards ─────────────────────────────────────────────────────────────
    total_payroll  = emp["salary"].sum()
    avg_salary     = int(emp["salary"].mean())
    active_proj    = len(prj[prj["status"] == "In Progress"])
    total_revenue  = sal["revenue"].sum()

    st.markdown(f"""
    <div class="card-grid">
        <div class="card-3d">
            <div class="card-3d-inner card-accent-1">
                <span class="card-icon">👥</span>
                <div class="card-value">{len(emp)}</div>
                <div class="card-label">Total Employees</div>
                <div class="card-sub">{emp['department'].nunique()} departments</div>
            </div>
        </div>
        <div class="card-3d">
            <div class="card-3d-inner card-accent-2">
                <span class="card-icon">💰</span>
                <div class="card-value">${avg_salary:,}</div>
                <div class="card-label">Avg Salary</div>
                <div class="card-sub">Total payroll ${total_payroll:,}</div>
            </div>
        </div>
        <div class="card-3d">
            <div class="card-3d-inner card-accent-3">
                <span class="card-icon">🚀</span>
                <div class="card-value">{active_proj}</div>
                <div class="card-label">Active Projects</div>
                <div class="card-sub">{len(prj)} total · {len(prj[prj['status']=='Completed'])} completed</div>
            </div>
        </div>
        <div class="card-3d">
            <div class="card-3d-inner card-accent-4">
                <span class="card-icon">📈</span>
                <div class="card-value">${total_revenue/1_000_000:.1f}M</div>
                <div class="card-label">Total Revenue</div>
                <div class="card-sub">{sal['units_sold'].sum():,} units sold</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # ── Row 1: Charts ─────────────────────────────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Salary by Department")
        dept_sal = emp.groupby("department")["salary"].mean().reset_index().sort_values("salary", ascending=True)
        fig = go.Figure(go.Bar(
            x=dept_sal["salary"], y=dept_sal["department"],
            orientation="h",
            marker=dict(
                color=dept_sal["salary"],
                colorscale=[[0,"#6366F1"],[0.5,"#8B5CF6"],[1,"#67E8F9"]],
                showscale=False,
            ),
            text=[f"${v:,.0f}" for v in dept_sal["salary"]],
            textposition="outside",
            textfont=dict(color="#94A3B8", size=11),
        ))
        fig.update_layout(**PLOT_LAYOUT, height=280)
        fig.update_xaxes(gridcolor="rgba(99,102,241,0.08)")
        fig.update_yaxes(gridcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Revenue by Region & Quarter")
        fig2 = px.bar(
            sal, x="quarter", y="revenue", color="region",
            barmode="group",
            color_discrete_sequence=["#6366F1","#67E8F9","#8B5CF6","#34D399"],
        )
        fig2.update_layout(**PLOT_LAYOUT, height=280, legend=dict(orientation="h", y=-0.2))
        fig2.update_traces(marker_line_width=0)
        st.plotly_chart(fig2, use_container_width=True)

    # ── Row 2 ──────────────────────────────────────────────────────────────────────
    col3, col4 = st.columns(2)

    with col3:
        st.markdown("#### Project Budget Breakdown")
        fig3 = px.pie(
            prj, names="name", values="budget",
            hole=0.55,
            color_discrete_sequence=["#6366F1","#8B5CF6","#67E8F9","#34D399","#F59E0B"],
        )
        fig3.update_traces(textposition="outside", textinfo="label+percent",
                           textfont=dict(color="#94A3B8", size=10),
                           pull=[0.04]*len(prj))
        fig3.update_layout(**PLOT_LAYOUT, height=300,
                           legend=dict(orientation="v", x=1, y=0.5, font=dict(size=10)))
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        st.markdown("#### Headcount by Department")
        hc = emp.groupby("department").size().reset_index(name="count")
        fig4 = go.Figure(go.Scatterpolar(
            r=hc["count"], theta=hc["department"],
            fill="toself",
            fillcolor="rgba(99,102,241,0.15)",
            line=dict(color="#6366F1", width=2),
            marker=dict(size=8, color="#A5B4FC"),
        ))
        fig4.update_layout(**PLOT_LAYOUT, height=300,
                           polar=dict(
                               bgcolor="rgba(0,0,0,0)",
                               radialaxis=dict(gridcolor="rgba(99,102,241,0.15)", color="#334155"),
                               angularaxis=dict(gridcolor="rgba(99,102,241,0.1)", color="#475569"),
                           ))
        st.plotly_chart(fig4, use_container_width=True)

    # ── Row 3: salary scatter ──────────────────────────────────────────────────────
    st.markdown("#### Employee Salary Distribution")
    fig5 = px.scatter(
        emp, x="hire_date", y="salary",
        color="department", size="salary",
        size_max=22, hover_name="name",
        hover_data={"role": True, "location": True, "salary": True},
        color_discrete_sequence=["#6366F1","#67E8F9","#8B5CF6","#34D399","#F59E0B","#EF4444"],
    )
    fig5.update_layout(**PLOT_LAYOUT, height=320,
                       legend=dict(orientation="h", y=-0.2))
    fig5.update_traces(marker=dict(line=dict(width=1, color="rgba(255,255,255,0.15)")))
    st.plotly_chart(fig5, use_container_width=True)

    # ── Agent usage stats ──────────────────────────────────────────────────────────
    if st.session_state.tool_history:
        st.divider()
        st.markdown("#### Agent Session Stats")
        all_tools = [t for h in st.session_state.tool_history for t in h["tool_calls"]]
        if all_tools:
            from collections import Counter
            tc_df = pd.DataFrame(Counter(all_tools).items(), columns=["tool","count"])
            fig6 = px.bar(tc_df.sort_values("count"), x="count", y="tool", orientation="h",
                          color="count",
                          color_continuous_scale=[[0,"#6366F1"],[1,"#67E8F9"]])
            fig6.update_layout(**PLOT_LAYOUT, height=220, coloraxis_showscale=False)
            c_a, c_b = st.columns(2)
            c_a.metric("Questions asked", len(st.session_state.tool_history))
            c_a.metric("Tool calls made", len(all_tools))
            c_b.plotly_chart(fig6, use_container_width=True)


# ═══════════════════════════════════════════════════════════════
# TAB 3 — DATA CATALOG
# ═══════════════════════════════════════════════════════════════
with tab_catalog:
    st.markdown("### Data Catalog")
    st.caption("DuckDB — structured enterprise data, queried locally.")

    if not is_seeded():
        st.info("Seed sample data from the sidebar first.", icon="ℹ️")
    else:
        tables = get_tables()
        if tables:
            cols = st.columns(len(tables))
            for col, t in zip(cols, tables):
                df_p = db_query(f"SELECT * FROM {t}")
                col.metric(t.replace("_"," ").title(), f"{len(df_p)} rows")

            st.divider()
            selected = st.selectbox("Browse table", tables, format_func=lambda x: x.replace("_"," ").title())
            if selected:
                df = db_query(f"SELECT * FROM {selected}")
                st.markdown(f"**{selected.replace('_',' ').title()}** · {len(df)} rows · {len(df.columns)} columns")
                st.dataframe(df, use_container_width=True, height=280)

                st.divider()
                with st.expander("🖥️ Run a SQL query"):
                    query = st.text_area("SQL", value=f"SELECT * FROM {selected} LIMIT 10", height=80)
                    if st.button("Run Query", type="primary"):
                        try:
                            result = db_query(query)
                            st.dataframe(result, use_container_width=True)
                        except Exception as e:
                            st.error(str(e))


# ═══════════════════════════════════════════════════════════════
# TAB 4 — KNOWLEDGE BASE
# ═══════════════════════════════════════════════════════════════
with tab_docs:
    st.markdown("### Knowledge Base")
    st.caption("ChromaDB vector store — semantic search over enterprise documents.")

    if not is_seeded():
        st.info("Seed sample data from the sidebar first.", icon="ℹ️")
    else:
        kb_search, kb_browse, kb_add = st.tabs(["🔍 Semantic Search", "📋 Browse All", "➕ Add Document"])

        with kb_search:
            q = st.text_input("Search query", placeholder="e.g. security policy, AI engine…")
            n = st.slider("Max results", 1, 8, 4)
            if st.button("Search", type="primary") and q.strip():
                results = chroma_search(q.strip(), n)
                if not results:
                    st.info("No results found.")
                else:
                    for r in results:
                        sc = r["score"]
                        sc_color = "#10B981" if sc > 0.7 else "#F59E0B" if sc > 0.4 else "#EF4444"
                        sc_label = "High" if sc > 0.7 else "Medium" if sc > 0.4 else "Low"
                        with st.container(border=True):
                            st.markdown(
                                f"<span style='color:{sc_color};font-weight:700;font-size:0.82rem'>"
                                f"● {sc_label} match ({sc})</span>"
                                f" &nbsp;·&nbsp; <code style='font-size:0.78rem'>{r['id']}</code>"
                                f" &nbsp;·&nbsp; <span style='color:#334155;font-size:0.78rem'>"
                                f"{r['metadata'].get('category','')} / {r['metadata'].get('source','')}</span>",
                                unsafe_allow_html=True,
                            )
                            st.markdown(r["document"])

        with kb_browse:
            docs = get_chroma_docs()
            if not docs:
                st.info("No documents yet.")
            else:
                st.markdown(f"**{len(docs)} documents** in the knowledge base")
                cats = list({d["metadata"].get("category","") for d in docs})
                sel_cat = st.multiselect("Filter by category", cats, default=cats)
                for doc in docs:
                    if doc["metadata"].get("category","") in sel_cat:
                        with st.expander(
                            f"`{doc['id']}` · {doc['metadata'].get('category','')} / {doc['metadata'].get('source','')}",
                            expanded=False,
                        ):
                            st.markdown(doc["document"])

        with kb_add:
            with st.form("add_doc"):
                c1, c2 = st.columns(2)
                doc_id  = c1.text_input("Document ID",  placeholder="e.g. policy_v8")
                source  = c2.text_input("Source",       placeholder="e.g. confluence")
                content = st.text_area("Content", height=130, placeholder="Paste document text…")
                cat     = st.selectbox("Category", ["governance","engineering","security","ml","business","operations","general"])
                submitted = st.form_submit_button("Add to Knowledge Base", type="primary", use_container_width=True)
                if submitted:
                    if not doc_id.strip() or not content.strip():
                        st.error("ID and content are required.")
                    else:
                        try:
                            add_chroma_doc(doc_id.strip(), content.strip(), cat, source.strip())
                            st.success(f"Added `{doc_id}` to the knowledge base.")
                        except Exception as e:
                            st.error(str(e))
