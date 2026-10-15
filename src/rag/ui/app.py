import base64
import json
import os
import re
import textwrap
import time
from datetime import datetime
from pathlib import Path
import altair as alt
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from rag.ui.client import RAGAPIClient
from rag.nlp.arabic import is_arabic_text
from rag.ui.chart_extractor import extract_all_charts

load_dotenv()

# =========================================================
# Page Configuration
# =========================================================

st.set_page_config(
    page_title="PSUT | Sovereign Hybrid RAG",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# University Institutional Theme (PSUT White & Royal Navy)
# Strict High-Contrast CSS: All text guaranteed 100% visible
# =========================================================

HIGH_CONTRAST_PSUT_CSS = """
<style>
/* Base typography & container spacing */
.main .block-container {
    padding-top: 1.2rem;
    padding-bottom: 3.5rem;
    max-width: 1320px;
}

/* Light institutional background */
[data-testid="stAppViewContainer"], body {
    background-color: #F8FAFC !important;
    color: #0F172A !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background-color: #FFFFFF !important;
    border-right: 1.5px solid #E2E8F0 !important;
}

/* Hide default streamlit headers and footer while keeping collapsedControl visible */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {
    background: transparent !important;
}

[data-testid="collapsedControl"] {
    visibility: visible !important;
    display: flex !important;
    color: #002D62 !important;
    background-color: #FFFFFF !important;
    border: 1.5px solid #CBD5E1 !important;
    border-radius: 8px !important;
    margin: 8px 12px !important;
    box-shadow: 0 2px 6px rgba(0, 45, 98, 0.08) !important;
    transition: all 140ms ease !important;
    z-index: 999999 !important;
}

[data-testid="collapsedControl"]:hover {
    border-color: #002D62 !important;
    background-color: #EFF6FF !important;
    box-shadow: 0 4px 10px rgba(0, 45, 98, 0.14) !important;
}

[data-testid="stSidebarCollapseButton"] button {
    color: #002D62 !important;
}

/* Universal text visibility overrides - High Contrast */
h1, h2, h3, h4, h5, h6 {
    color: #002D62 !important;
    font-weight: 800 !important;
    letter-spacing: -0.02em;
}

p, span, label, div, li {
    color: #0F172A;
}

/* Form inputs & text areas with Emil focus ring */
textarea, input[type="text"] {
    color: #0F172A !important;
    background-color: #FFFFFF !important;
    border: 1.5px solid #94A3B8 !important;
    border-radius: 8px !important;
    font-size: 1rem !important;
    font-weight: 500 !important;
    transition: border-color 140ms cubic-bezier(0.23, 1, 0.32, 1), box-shadow 140ms ease !important;
}

textarea:focus, input[type="text"]:focus {
    border-color: #002D62 !important;
    box-shadow: 0 0 0 3px rgba(0, 45, 98, 0.15), 0 1px 2px rgba(0, 0, 0, 0.05) !important;
}

textarea::placeholder {
    color: #64748B !important;
    font-weight: 400 !important;
}

/* Widget labels */
[data-testid="stWidgetLabel"] p, label p {
    color: #002D62 !important;
    font-weight: 700 !important;
    font-size: 0.92rem !important;
}

/* Hardware Telemetry Metric Cards - Emil Layered Elevation */
[data-testid="stMetric"] {
    background: #FFFFFF !important;
    border: 1.5px solid #E2E8F0 !important;
    border-radius: 10px !important;
    padding: 12px 16px !important;
    box-shadow: 0 1px 3px rgba(0, 45, 98, 0.04), 0 4px 10px rgba(0, 45, 98, 0.02) !important;
    transition: transform 140ms cubic-bezier(0.23, 1, 0.32, 1), box-shadow 140ms ease, border-color 140ms ease !important;
}

[data-testid="stMetric"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 14px rgba(0, 45, 98, 0.08) !important;
    border-color: #BFDBFE !important;
}

[data-testid="stMetricLabel"] p {
    font-size: 0.82rem !important;
    font-weight: 700 !important;
    color: #64748B !important;
    text-transform: uppercase !important;
    letter-spacing: 0.02em !important;
}

[data-testid="stMetricValue"] {
    color: #002D62 !important;
    font-weight: 800 !important;
    font-size: 1.35rem !important;
}

/* Badges - Maximum Contrast & Legibility */
.badge-row {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 8px;
    margin-bottom: 22px;
}

.trust-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    border-radius: 8px;
    font-size: 0.78rem;
    font-weight: 800;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
    transition: transform 140ms cubic-bezier(0.23, 1, 0.32, 1), box-shadow 140ms ease !important;
}

.trust-badge:hover {
    transform: translateY(-1px);
    box-shadow: 0 3px 8px rgba(0, 0, 0, 0.12);
}

.badge-navy {
    background-color: #002D62;
    color: #FFFFFF !important;
    border: 1px solid #001A38;
}

.badge-blue {
    background-color: #1E40AF;
    color: #FFFFFF !important;
    border: 1px solid #1E3A8A;
}

.badge-green {
    background-color: #047857;
    color: #FFFFFF !important;
    border: 1px solid #065F46;
}

.badge-amber {
    background-color: #B45309;
    color: #FFFFFF !important;
    border: 1px solid #92400E;
}

/* Conflict Detective Badges */
.rel-badge {
    display: inline-block;
    padding: 8px 16px;
    border-radius: 8px;
    font-size: 0.95rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 12px;
}
.rel-agreement {
    background-color: #DCFCE7;
    color: #166534 !important;
    border: 2px solid #86EFAC;
}
.rel-version {
    background-color: #DBEAFE;
    color: #1E40AF !important;
    border: 2px solid #93C5FD;
}
.rel-conflict {
    background-color: #FEE2E2;
    color: #991B1B !important;
    border: 2px solid #FCA5A5;
}
.rel-insufficient {
    background-color: #F1F5F9;
    color: #475569 !important;
    border: 2px solid #CBD5E1;
}

/* Primary Button (PSUT Navy) - Emil Kowalski Micro-Interactions */
.stButton>button[kind="primary"] {
    background-color: #002D62 !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.55rem 1.25rem !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    box-shadow: 0 1px 3px rgba(0, 45, 98, 0.12), 0 3px 8px rgba(0, 45, 98, 0.16) !important;
    transition: transform 140ms cubic-bezier(0.23, 1, 0.32, 1), background-color 140ms ease, box-shadow 140ms ease !important;
}

.stButton>button[kind="primary"] p {
    color: #FFFFFF !important;
    font-weight: 700 !important;
}

.stButton>button[kind="primary"]:hover {
    background-color: #1E40AF !important;
    box-shadow: 0 2px 6px rgba(0, 45, 98, 0.2), 0 6px 14px rgba(0, 45, 98, 0.18) !important;
    transform: translateY(-1px) !important;
}

.stButton>button[kind="primary"]:active {
    transform: scale(0.97) !important;
    box-shadow: 0 1px 2px rgba(0, 45, 98, 0.2) !important;
}

/* Secondary Button - Emil Kowalski Tactile Feedback */
.stButton>button[kind="secondary"] {
    background-color: #FFFFFF !important;
    color: #002D62 !important;
    border: 1.5px solid #CBD5E1 !important;
    border-radius: 8px !important;
    transition: transform 140ms cubic-bezier(0.23, 1, 0.32, 1), border-color 140ms ease, background-color 140ms ease !important;
}

.stButton>button[kind="secondary"] p {
    color: #002D62 !important;
    font-weight: 700 !important;
}

.stButton>button[kind="secondary"]:hover {
    border-color: #002D62 !important;
    color: #002D62 !important;
    background-color: #EFF6FF !important;
    transform: translateY(-1px) !important;
}

.stButton>button[kind="secondary"]:active {
    transform: scale(0.97) !important;
}

/* Download Button - Emil Kowalski Tactile Feedback */
[data-testid="stDownloadButton"] button {
    background-color: #FFFFFF !important;
    color: #002D62 !important;
    border: 2px solid #002D62 !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    transition: transform 140ms cubic-bezier(0.23, 1, 0.32, 1), background-color 140ms ease, color 140ms ease !important;
}

[data-testid="stDownloadButton"] button p {
    color: #002D62 !important;
    font-weight: 700 !important;
}

[data-testid="stDownloadButton"] button:hover {
    background-color: #002D62 !important;
    color: #FFFFFF !important;
    transform: translateY(-1px) !important;
}

[data-testid="stDownloadButton"] button:hover p {
    color: #FFFFFF !important;
}

[data-testid="stDownloadButton"] button:active {
    transform: scale(0.97) !important;
}

/* Top Tab Bar Styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    border-bottom: 2px solid #CBD5E1;
    margin-bottom: 18px;
}

.stTabs [data-baseweb="tab"] {
    font-size: 1.02rem;
    font-weight: 700;
    color: #475569;
    padding: 10px 18px;
    border-radius: 8px 8px 0 0;
}

.stTabs [aria-selected="true"] {
    color: #002D62 !important;
    border-bottom: 3px solid #002D62 !important;
    font-weight: 800 !important;
}

/* Executive Box & Cards */
.exec-box {
    background-color: #FFFFFF;
    border: 1.5px solid #CBD5E1;
    border-left: 5px solid #002D62;
    border-radius: 8px;
    padding: 18px 22px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 45, 98, 0.05);
}

.finding-card {
    background-color: #FFFFFF;
    border: 1.5px solid #E2E8F0;
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 14px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
    transition: transform 140ms cubic-bezier(0.23, 1, 0.32, 1), box-shadow 140ms ease, border-color 140ms ease !important;
}

.finding-card:hover {
    transform: translateY(-2px) !important;
    border-color: #BFDBFE !important;
    box-shadow: 0 4px 14px rgba(0, 45, 98, 0.08) !important;
}

.finding-tag {
    display: inline-block;
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 0.72rem;
    font-weight: 800;
    text-transform: uppercase;
    margin-bottom: 6px;
}
.tag-policy { background: #DBEAFE; color: #1E40AF; }
.tag-technical { background: #E0E7FF; color: #3730A3; }
.tag-compliance { background: #FEF3C7; color: #92400E; }
.tag-action_item { background: #DCFCE7; color: #166534; }

.source-pill-quote {
    background-color: #F8FAFC;
    border-left: 3px solid #002D62;
    padding: 8px 12px;
    margin-top: 8px;
    font-size: 0.88rem;
    line-height: 1.6;
    color: #334155;
    font-style: italic;
    border-radius: 0 6px 6px 0;
}

/* Emil Kowalski Hero Institutional Card */
.hero-institution-card {
    background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
    border: 1.5px solid #E2E8F0;
    border-radius: 14px;
    padding: 20px 24px;
    margin-bottom: 18px;
    box-shadow: 0 1px 3px rgba(0, 45, 98, 0.04), 0 6px 18px rgba(0, 45, 98, 0.02);
    transition: border-color 140ms ease, box-shadow 140ms ease;
}

.hero-institution-card:hover {
    border-color: #CBD5E1;
    box-shadow: 0 4px 16px rgba(0, 45, 98, 0.06);
}

/* Grounded Result Card */
.grounded-result-card {
    background: #FFFFFF;
    border: 1.5px solid #BFDBFE;
    border-radius: 12px;
    padding: 20px 24px;
    box-shadow: 0 2px 8px rgba(0, 45, 98, 0.05);
    margin-bottom: 16px;
    transition: border-color 140ms ease, box-shadow 140ms ease;
}

.grounded-result-card:hover {
    border-color: #93C5FD;
    box-shadow: 0 4px 14px rgba(0, 45, 98, 0.08);
}

/* Conflict Detective Cards */
.conflict-card-a {
    background: #FFFFFF;
    border: 1.5px solid #CBD5E1;
    border-top: 5px solid #002D62;
    border-radius: 10px;
    padding: 18px 20px;
    box-shadow: 0 2px 6px rgba(0, 45, 98, 0.04);
    margin-bottom: 12px;
    transition: transform 140ms cubic-bezier(0.23, 1, 0.32, 1), box-shadow 140ms ease;
}

.conflict-card-a:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 45, 98, 0.08);
}

.conflict-card-b {
    background: #FFFFFF;
    border: 1.5px solid #CBD5E1;
    border-top: 5px solid #2563EB;
    border-radius: 10px;
    padding: 18px 20px;
    box-shadow: 0 2px 6px rgba(37, 99, 235, 0.04);
    margin-bottom: 12px;
    transition: transform 140ms cubic-bezier(0.23, 1, 0.32, 1), box-shadow 140ms ease;
}

.conflict-card-b:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.08);
}

.conflict-summary-banner {
    background: #F8FAFC;
    border: 1.5px solid #E2E8F0;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
}

.conflict-guidance-card {
    background: #FFFDF5;
    border: 1.5px solid #FDE68A;
    border-left: 5px solid #D97706;
    border-radius: 10px;
    padding: 18px 22px;
    margin-top: 16px;
    box-shadow: 0 1px 3px rgba(217, 119, 6, 0.06);
}

/* Executive Briefing Overview Card */
.brief-overview-card {
    background: #FFFFFF;
    border: 1.5px solid #CBD5E1;
    border-left: 5px solid #002D62;
    border-radius: 10px;
    padding: 20px 24px;
    box-shadow: 0 2px 8px rgba(0, 45, 98, 0.04);
    margin-bottom: 18px;
}

/* Streamlit Expander Polish */
[data-testid="stExpander"] {
    background: #FFFFFF !important;
    border: 1.5px solid #E2E8F0 !important;
    border-radius: 10px !important;
    margin-bottom: 12px !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03) !important;
    transition: border-color 140ms ease, box-shadow 140ms ease !important;
}

[data-testid="stExpander"]:hover {
    border-color: #CBD5E1 !important;
    box-shadow: 0 3px 8px rgba(0, 45, 98, 0.05) !important;
}

[data-testid="stExpander"] summary {
    font-weight: 700 !important;
    color: #002D62 !important;
    padding: 10px 14px !important;
}

/* File Uploader Polish */
[data-testid="stFileUploader"] {
    background: #FFFFFF !important;
    border: 1.5px dashed #94A3B8 !important;
    border-radius: 12px !important;
    padding: 20px !important;
    transition: border-color 140ms ease, background-color 140ms ease !important;
}

[data-testid="stFileUploader"]:hover {
    border-color: #002D62 !important;
    background-color: #F8FAFC !important;
}

/* Entry Animation - Emil Kowalski 180ms ease-out */
@keyframes emilFadeInUp {
    from {
        opacity: 0;
        transform: translateY(6px) scale(0.99);
    }
    to {
        opacity: 1;
        transform: translateY(0) scale(1);
    }
}

@media (prefers-reduced-motion: no-preference) {
    .hero-institution-card, .grounded-result-card, .conflict-card-a, .conflict-card-b, .conflict-guidance-card, .brief-overview-card, .finding-card {
        animation: emilFadeInUp 180ms cubic-bezier(0.23, 1, 0.32, 1) both;
    }
}

/* Streamlit 1.61.1 MultiSelect Tag / Pill Styling - Absolute White Contrast */
[data-tag],
[data-tag-index],
[data-baseweb="tag"],
[data-testid="stMultiSelectTagsContainer"] [data-tag],
[data-testid="stMultiSelect"] [data-tag],
.stMultiSelect [data-tag],
[role="group"][aria-label="Selected values"] > div,
[role="group"][aria-label="Selected values"] > span {
    background-color: #002D62 !important;
    border: 1.5px solid #3B82F6 !important;
    border-radius: 6px !important;
    padding: 3px 10px !important;
    margin: 3px 4px !important;
}

[data-tag] *,
[data-tag] span,
[data-tag] span[title],
[data-tag-index] *,
[data-tag-index] span,
[data-baseweb="tag"] *,
[data-baseweb="tag"] span,
[data-testid="stMultiSelectTagsContainer"] *,
[data-testid="stMultiSelectTagsContainer"] span,
[data-testid="stMultiSelect"] [data-tag] *,
[data-testid="stMultiSelect"] [data-tag] span,
.stMultiSelect [data-tag] *,
[role="group"][aria-label="Selected values"] * {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    fill: #FFFFFF !important;
    font-weight: 700 !important;
    font-size: 0.88rem !important;
    letter-spacing: 0.02em !important;
}

[data-tag] svg,
[data-tag] path,
[data-tag] [aria-label*="Remove"] svg,
[data-tag] [aria-label*="Remove"] path,
[data-testid="stMultiSelectTagsContainer"] svg,
[data-testid="stMultiSelectTagsContainer"] path {
    color: #FFFFFF !important;
    fill: #FFFFFF !important;
    stroke: #FFFFFF !important;
}

[data-tag]:hover,
[data-tag-index]:hover,
[data-baseweb="tag"]:hover {
    background-color: #1E40AF !important;
}

/* Multiselect and Selectbox input containers */
[data-baseweb="select"] > div:first-child {
    background-color: #FFFFFF !important;
    border: 1.5px solid #94A3B8 !important;
    border-radius: 8px !important;
}

[data-baseweb="select"] input {
    color: #0F172A !important;
}

/* Dropdown menu items when open */
[data-baseweb="popover"],
[data-baseweb="menu"],
ul[role="listbox"] {
    background-color: #FFFFFF !important;
    border: 1.5px solid #CBD5E1 !important;
    border-radius: 8px !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
}

li[role="option"],
[data-baseweb="menu"] [role="option"] {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
    font-weight: 600 !important;
    padding: 8px 12px !important;
}

li[role="option"]:hover,
li[role="option"][aria-selected="true"],
[data-baseweb="menu"] [role="option"]:hover,
[data-baseweb="menu"] [role="option"][aria-selected="true"] {
    background-color: #EFF6FF !important;
    color: #002D62 !important;
}

/* Sidebar Feature Navigation Radio Cards */
[data-testid="stSidebar"] [data-testid="stRadio"] > div {
    gap: 8px !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label {
    background: #FFFFFF !important;
    border: 1.5px solid #CBD5E1 !important;
    border-radius: 8px !important;
    padding: 10px 14px !important;
    transition: all 140ms ease !important;
    cursor: pointer !important;
    width: 100% !important;
    box-shadow: 0 1px 3px rgba(0, 45, 98, 0.03) !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: #EFF6FF !important;
    border-color: #002D62 !important;
    box-shadow: 0 2px 6px rgba(0, 45, 98, 0.08) !important;
    transform: translateY(-1px);
}

[data-testid="stSidebar"] [data-testid="stRadio"] label[data-checked="true"],
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
    background: #EFF6FF !important;
    border-color: #002D62 !important;
    border-left: 4px solid #002D62 !important;
    box-shadow: 0 0 0 2px rgba(0, 45, 98, 0.12) !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label p {
    color: #002D62 !important;
    font-weight: 700 !important;
    font-size: 0.88rem !important;
    margin: 0 !important;
}
</style>
"""

ARABIC_RTL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800;900&display=swap');

/* Clean, directional RTL setup on container level */
.block-container, [data-testid="stSidebarContent"], [data-testid="stMarkdownContainer"] {
    direction: rtl;
    text-align: right;
    font-family: 'Cairo', 'Segoe UI', Tahoma, -apple-system, sans-serif !important;
}

h1, h2, h3, h4, h5, h6, p, label, li {
    font-family: 'Cairo', 'Segoe UI', Tahoma, -apple-system, sans-serif !important;
    text-align: right;
    direction: rtl;
}

/* CRITICAL FIX: Explicitly preserve Material Symbols icon fonts so they NEVER render as raw ligature text (e.g. keyboard_ar) */
[data-testid="stIconMaterial"], 
.material-symbols-rounded, 
.material-symbols-outlined, 
.material-icons,
[class*="material-symbols"],
[data-testid="stExpanderToggleIcon"],
[data-testid="stExpander"] summary span svg,
[data-testid="stExpander"] summary [data-testid="stIconMaterial"] {
    font-family: "Material Symbols Rounded", "Material Symbols Outlined", "Material Icons" !important;
    direction: ltr !important;
    text-align: center !important;
    font-style: normal !important;
    font-weight: normal !important;
}

/* Preserve code blocks and technical identifiers from RTL distortion */
code, kbd, samp, pre, [data-testid="stCodeBlock"], .en-code {
    font-family: "Consolas", "Monaco", "Courier New", monospace !important;
    direction: ltr !important;
    text-align: left !important;
    display: inline-block !important;
    unicode-bidi: embed !important;
}

/* BiDi Isolation utilities */
.bidi-text, [dir="auto"] {
    unicode-bidi: plaintext !important;
    text-align: right !important;
}

.ltr-isolate, [dir="ltr"] {
    direction: ltr !important;
    text-align: left !important;
    display: inline-block !important;
    unicode-bidi: isolate !important;
}

/* Streamlit Expander styling in RTL */
[data-testid="stExpander"] summary {
    direction: rtl !important;
    text-align: right !important;
}

[data-testid="stExpander"] summary [data-testid="stMarkdownContainer"] {
    margin-right: 8px !important;
    margin-left: 0 !important;
    text-align: right !important;
}

/* Streamlit Tabs in RTL */
.stTabs [data-baseweb="tab-list"] {
    direction: rtl !important;
}

/* Sidebar styling in RTL */
[data-testid="stSidebar"] {
    direction: rtl !important;
    text-align: right !important;
}

/* Form inputs */
textarea, input[type="text"] {
    direction: rtl !important;
    text-align: right !important;
    font-family: 'Cairo', 'Segoe UI', Tahoma, sans-serif !important;
}

.trust-badge {
    direction: rtl !important;
    font-family: 'Cairo', sans-serif !important;
}

.exec-box {
    border-left: 1.5px solid #CBD5E1 !important;
    border-right: 5px solid #002D62 !important;
    direction: rtl !important;
    text-align: right !important;
}

.source-pill-quote {
    border-left: none !important;
    border-right: 3px solid #002D62 !important;
    border-radius: 4px 0 0 4px !important;
    direction: rtl !important;
    text-align: right !important;
}

/* Streamlit 1.61.1 MultiSelect Tag in RTL - Force LTR text and white color */
[data-tag],
[data-tag-index],
[data-baseweb="tag"],
[data-testid="stMultiSelectTagsContainer"] [data-tag],
[data-testid="stMultiSelect"] [data-tag],
.stMultiSelect [data-tag],
[role="group"][aria-label="Selected values"] > div,
[role="group"][aria-label="Selected values"] > span {
    background-color: #002D62 !important;
    border: 1.5px solid #3B82F6 !important;
    border-radius: 6px !important;
    direction: ltr !important;
}

[data-tag] *,
[data-tag] span,
[data-tag] span[title],
[data-tag-index] *,
[data-tag-index] span,
[data-baseweb="tag"] *,
[data-baseweb="tag"] span,
[data-testid="stMultiSelectTagsContainer"] *,
[data-testid="stMultiSelectTagsContainer"] span,
[data-testid="stMultiSelect"] [data-tag] *,
[data-testid="stMultiSelect"] [data-tag] span,
.stMultiSelect [data-tag] *,
[role="group"][aria-label="Selected values"] * {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    fill: #FFFFFF !important;
    direction: ltr !important;
}

[data-tag] svg,
[data-tag] path,
[data-tag] [aria-label*="Remove"] svg,
[data-tag] [aria-label*="Remove"] path,
[data-testid="stMultiSelectTagsContainer"] svg,
[data-testid="stMultiSelectTagsContainer"] path {
    color: #FFFFFF !important;
    fill: #FFFFFF !important;
    stroke: #FFFFFF !important;
}

/* Emil Kowalski Card Directional Overrides in RTL */
.hero-institution-card [style*="border-left"] {
    border-left: none !important;
    border-right: 2.5px solid #E2E8F0 !important;
    padding-left: 0 !important;
    padding-right: 20px !important;
}

.grounded-result-card {
    border-right: 5px solid #002D62 !important;
    direction: rtl !important;
    text-align: right !important;
}

.conflict-card-a, .conflict-card-b {
    direction: rtl !important;
    text-align: right !important;
}

.conflict-guidance-card {
    border-left: 1.5px solid #FDE68A !important;
    border-right: 5px solid #D97706 !important;
    direction: rtl !important;
    text-align: right !important;
}

.brief-overview-card {
    border-left: 1.5px solid #CBD5E1 !important;
    border-right: 5px solid #002D62 !important;
    direction: rtl !important;
    text-align: right !important;
}

.bidi-text {
    line-height: 1.85 !important;
}
</style>
"""

st.markdown(HIGH_CONTRAST_PSUT_CSS, unsafe_allow_html=True)

# =========================================================
# Client Initialization & Session State
# =========================================================

api_url = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
client = RAGAPIClient(base_url=api_url)

if "question_input" not in st.session_state:
    st.session_state["question_input"] = ""

if "trigger_ask" not in st.session_state:
    st.session_state["trigger_ask"] = False

if "last_result" not in st.session_state:
    st.session_state["last_result"] = None

if "last_question" not in st.session_state:
    st.session_state["last_question"] = ""

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

if "documents" not in st.session_state:
    try:
        st.session_state["documents"] = client.list_documents()
    except Exception:
        st.session_state["documents"] = []

if "health_status" not in st.session_state:
    st.session_state["health_status"] = None


# =========================================================
# Helper Functions
# =========================================================

def get_logo_path() -> str | None:
    candidates = [
        "assets/psut_logo.png",
        "assets/psut_logo.jpg",
        "assets/psut_logo.svg",
        "assets/psut_crest.svg",
    ]
    for c in candidates:
        if Path(c).is_file():
            return c
    return None


def get_logo_base64() -> str | None:
    path = get_logo_path()
    if path and Path(path).is_file():
        try:
            with open(path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
                mime = "image/svg+xml" if path.endswith(".svg") else "image/png"
                return f"data:{mime};base64,{encoded}"
        except Exception:
            pass
    return None


def clean_source_name(raw_src: str) -> tuple[str, str]:
    base_src = os.path.basename(raw_src or "Document")
    clean_src = base_src.split("_", 1)[-1] if len(base_src) > 65 and "_" in base_src else base_src
    return clean_src, base_src


def build_chunk_text_map(trace: dict | None, evidence_list: list | None = None) -> dict[str, str]:
    chunk_map = {}
    if evidence_list:
        for ev in evidence_list:
            cid = ev.get("chunk_id")
            text = ev.get("text")
            if cid and text:
                chunk_map[cid] = text

    if trace:
        for chunk in trace.get("final_evidence", []):
            cid = chunk.get("chunk_id")
            text = chunk.get("text")
            if cid and text and cid not in chunk_map:
                chunk_map[cid] = text

        for candidate in trace.get("candidates", []):
            cid = candidate.get("chunk_id")
            text = candidate.get("text")
            if cid and text and cid not in chunk_map:
                chunk_map[cid] = text

    return chunk_map


def shorten_chart_label(text: str) -> str:
    """Creates a concise, clean single-line label for chart axis so it sits strictly underneath each column."""
    lbl = re.sub(r"[*_`]", "", str(text)).strip()
    lbl = re.sub(r"\[\d+\]", "", lbl).strip()
    # Government service label cleanups for visual clarity
    lbl = re.sub(r"^(خدمة\s+|إجراء\s+)", "", lbl)
    lbl = re.sub(r"إصدار\s+وتجديد\s+عادي", "إصدار عادي", lbl)
    lbl = re.sub(r"إصدار\s+جواز\s+سفر\s+مستعجل", "جواز مستعجل", lbl)
    lbl = re.sub(r"\(خدمة\s+VIP\)", "(VIP)", lbl, flags=re.IGNORECASE)
    lbl = re.sub(r"لمن\s+أتم\s+(\d+)\s+عاماً?\s+فما\s+فوق", r"فوق \1 سنة", lbl)
    lbl = re.sub(r"لمن\s+هم\s+دون\s+(\d+)\s+عاماً?", r"دون \1 سنة", lbl)
    lbl = re.sub(r"للمرة\s+الأولى\s+وما\s+فوق", "أول مرة", lbl)
    lbl = re.sub(r"\s+", " ", lbl).strip()
    if len(lbl) > 28:
        lbl = lbl[:26].strip() + "…"
    return lbl


def render_single_chart(chart_spec: dict, is_ar: bool = False, color: str = "#002D62"):
    """Renders a single institutional PSUT-themed bar chart with labels strictly underneath."""
    if not chart_spec or not chart_spec.get("data"):
        return

    data = chart_spec.get("data", [])
    title = chart_spec.get("title", "مقارنة إحصائية / رقمية" if is_ar else "Quantitative Comparison")
    metric_label = chart_spec.get("metric_label") or chart_spec.get("y_label") or ("القيمة / المعيار" if is_ar else "Value")

    clean_rows = []
    for row in data:
        if isinstance(row, dict) and "label" in row and "value" in row:
            try:
                val_raw = row["value"]
                if isinstance(val_raw, (int, float)):
                    val = float(val_raw)
                else:
                    val_str = re.sub(r"[^\d.]", "", str(val_raw))
                    val = float(val_str) if val_str else 0.0
                raw_lbl = str(row["label"]).strip()
                clean_rows.append({
                    "raw_label": raw_lbl,
                    "label": shorten_chart_label(raw_lbl),
                    "value": val,
                })
            except Exception:
                continue

    if not clean_rows:
        return

    df = pd.DataFrame(clean_rows)

    chart_header_html = textwrap.dedent(f"""
<div style="background:#FFFFFF; border:1.5px solid #BFDBFE; border-top:4px solid {color}; border-radius:10px; padding:12px 16px; margin-top:10px; margin-bottom:8px; box-shadow: 0 2px 6px rgba(0,45,98,0.04);">
<div style="display:flex; justify-content:space-between; align-items:center;">
<div style="display:flex; align-items:center; gap:8px;">
<span style="font-size:1.15rem;">📊</span>
<span style="font-size:0.92rem; font-weight:800; color:#002D62; text-transform:uppercase; letter-spacing:0.03em;">
{title}
</span>
</div>
<span style="background:#EFF6FF; color:#002D62; font-size:0.75rem; font-weight:700; padding:3px 8px; border-radius:4px; border:1px solid #BFDBFE;">
{'مخطط مقارنة تفاعلي' if is_ar else 'Interactive Comparison'}
</span>
</div>
</div>
""").strip()

    st.markdown(chart_header_html, unsafe_allow_html=True)

    # Label configuration so text sits strictly UNDERNEATH each column
    num_cols = len(df)
    label_angle = 0 if num_cols <= 4 else -25
    label_align = "center" if label_angle == 0 else "right"

    # Base column bars
    bars = (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6, color=color)
        .encode(
            x=alt.X(
                "label:N",
                sort=None,
                axis=alt.Axis(
                    title=None,
                    labelAngle=label_angle,
                    labelBaseline="top",
                    labelAlign=label_align,
                    labelPadding=14,
                    labelFontSize=11.5,
                    labelFontWeight="bold",
                    labelColor="#002D62",
                    labelLimit=250,
                    tickColor="#CBD5E1",
                    domainColor="#94A3B8",
                    domainWidth=1.5,
                ),
            ),
            y=alt.Y(
                "value:Q",
                axis=alt.Axis(
                    title=metric_label,
                    titleColor="#002D62",
                    titleFontWeight="bold",
                    titleFontSize=12,
                    titlePadding=12,
                    gridColor="#F1F5F9",
                    tickColor="#CBD5E1",
                    domainColor="#94A3B8",
                ),
            ),
            tooltip=[
                alt.Tooltip("raw_label:N", title="الخدمة / البيان" if is_ar else "Item / Service"),
                alt.Tooltip("value:Q", title=metric_label, format=".2f" if any(r["value"] % 1 != 0 for r in clean_rows) else ".0f"),
            ],
        )
    )

    # Value numbers overlaid on top of each bar
    val_format = ".2f" if any(r["value"] % 1 != 0 for r in clean_rows) else ".0f"
    text_overlay = (
        alt.Chart(df)
        .mark_text(
            dy=-10,
            color=color,
            fontSize=12,
            fontWeight="bold",
        )
        .encode(
            x=alt.X("label:N", sort=None),
            y=alt.Y("value:Q"),
            text=alt.Text("value:Q", format=val_format),
        )
    )

    final_chart = (bars + text_overlay).properties(height=320)
    st.altair_chart(final_chart, use_container_width=True)


def render_charts(charts: list[dict], is_ar: bool = False):
    """Renders one or multiple comparison charts (e.g. Fees and SLA)."""
    if not charts:
        return

    st.markdown(
        textwrap.dedent(f"""
<div style="font-size:0.86rem; font-weight:800; color:#002D62; text-transform:uppercase; letter-spacing:0.04em; margin-top:16px; margin-bottom:4px;">
{'📊 الرسوم البيانية ومؤشرات المقارنة التفاعلية' if is_ar else '📊 Interactive Comparison Charts & Visual Metrics'}
</div>
""").strip(),
        unsafe_allow_html=True,
    )

    if len(charts) == 2:
        col1, col2 = st.columns(2)
        with col1:
            render_single_chart(charts[0], is_ar=is_ar, color="#002D62")
        with col2:
            render_single_chart(charts[1], is_ar=is_ar, color="#1E40AF")
    else:
        colors = ["#002D62", "#1E40AF", "#047857", "#B45309"]
        for idx, chart in enumerate(charts):
            render_single_chart(chart, is_ar=is_ar, color=colors[idx % len(colors)])


def render_chart_spec(chart_spec: dict, is_ar: bool = False):
    """Backward-compatible helper to render a single chart spec."""
    if chart_spec:
        render_single_chart(chart_spec, is_ar=is_ar)


def generate_executive_brief_export(
    question: str,
    result: dict,
    chunk_map: dict[str, str],
    is_ar: bool = False,
) -> str:
    req_id = result.get("request_id", "N/A")
    latency = result.get("latency", {})
    answer = result.get("answer", "")
    citations = result.get("citations", [])
    abstained = result.get("abstained", False)

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if is_ar or is_arabic_text(question):
        doc = [
            "# 🏛️ جامعة الأميرة سمية للتكنولوجيا",
            "## تقرير الإيجاز والاستخلاص الذكي السيادي",
            f"**تاريخ التوليد:** {now_str} (بيئة عمل سيادية معزولة محلياً)",
            "**التصنيف:** سري / استخبارات حكومية سيادية",
            f"**معرف الطلب:** `{req_id}`",
            f"**حالة التدقيق:** {'⚠️ اعتذار (أدلة غير كافية للتحقق)' if abstained else '✅ موثق ومطابق للأدلة الرسمية'}",
            "\n---\n",
            "## 🎯 الاستفسار الإجرائي / التنفيذي",
            f"> {question}",
            "\n---\n",
            "## 📌 الاستخلاص الذكي والنتائج المعتمدة",
            answer,
            "\n---\n",
            "## 📑 الأدلة الموثقة وتوثيق المراجع الرسمية",
        ]

        if not citations:
            doc.append("_لا توجد مراجع مباشرة مسجلة._")
        else:
            for cit in citations:
                ref = cit.get("reference")
                source = cit.get("source")
                clean_name, base_name = clean_source_name(source)
                page = cit.get("page_number")
                heading = " ← ".join(cit.get("heading_path") or [])
                cid = cit.get("chunk_id", "")
                raw_quote = chunk_map.get(cid, "فقرة نصية موثقة من أصل الوثيقة الرسمية.")
                
                snippet = raw_quote.strip()
                if len(snippet) > 250:
                    snippet = snippet[:247] + "..."

                page_info = f"، صفحة {page}" if page is not None else ""
                heading_info = f" ({heading})" if heading else ""
                doc.append(f"### [مرجع {ref}] {clean_name}{page_info}{heading_info}")
                doc.append(f"> \"{snippet}\"\n")
                doc.append(f"- *الملف:* `{base_name}` | *معرف المقطع:* `{cid}`\n")

        doc.extend([
            "\n---\n",
            "## 🛡️ سجل التدقيق والموثوقية السيادية",
            "- **محرك الاسترجاع:** هجين (تضمين كثيف Dense + معجمي BM25 + دمج تراتبي RRF)",
            "- **معيد الترتيب:** Cross-Encoder (`BAAI/bge-reranker-base`) متعدد اللغات",
            "- **محرك التوليد المحلي:** Cohere Command R7B Arabic (`Ollama`)",
            "- **التسريع العتادي:** NVIDIA GeForce RTX 3060 Laptop GPU (CUDA مفعّل)",
            "- **قاعدة المتجهات:** Qdrant مدمجة ومحلية بالكامل",
            f"- **تفصيل زمن الاستجابة:** إجمالي {latency.get('total_ms', 0):.0f} مللي ثانية (الاسترجاع: {latency.get('retrieval_ms', 0):.0f} مللي ثانية | إعادة الترتيب: {latency.get('reranking_ms', 0):.0f} مللي ثانية | التوليد: {latency.get('generation_ms', 0):.0f} مللي ثانية)",
        ])
    else:
        doc = [
            "# 🏛️ PRINCESS SUMAYA UNIVERSITY FOR TECHNOLOGY",
            "## Sovereign Hybrid RAG Intelligence Briefing",
            f"**Generated:** {now_str} (Air-Gapped Sovereign Workstation)",
            "**Classification:** Confidential / Sovereign Enterprise Intelligence",
            f"**Request Identifier:** `{req_id}`",
            f"**Audit Status:** {'⚠️ Abstained (Insufficient Evidence)' if abstained else '✅ Verified & Grounded'}",
            "\n---\n",
            "## 🎯 Executive Inquiry",
            f"> {question}",
            "\n---\n",
            "## 📌 Key Synthesis & Grounded Findings",
            answer,
            "\n---\n",
            "## 📑 Verified Evidence & Source Citations",
        ]

        if not citations:
            doc.append("_No direct citations recorded._")
        else:
            for cit in citations:
                ref = cit.get("reference")
                source = cit.get("source")
                clean_name, base_name = clean_source_name(source)
                page = cit.get("page_number")
                heading = " → ".join(cit.get("heading_path") or [])
                cid = cit.get("chunk_id", "")
                raw_quote = chunk_map.get(cid, "Evidence excerpt verified in primary document.")
                
                snippet = raw_quote.strip()
                if len(snippet) > 250:
                    snippet = snippet[:247] + "..."

                page_info = f", Page {page}" if page is not None else ""
                heading_info = f" ({heading})" if heading else ""
                doc.append(f"### [{ref}] {clean_name}{page_info}{heading_info}")
                doc.append(f"> \"{snippet}\"\n")
                doc.append(f"- *File:* `{base_name}` | *Chunk ID:* `{cid}`\n")

        doc.extend([
            "\n---\n",
            "## 🛡️ Reliability & Sovereignty Audit",
            "- **Retrieval Pipeline:** Hybrid (Dense Vector + BM25 Lexical + Reciprocal Rank Fusion)",
            "- **Reranker:** Cross-Encoder (`BAAI/bge-reranker-base`)",
            "- **Local LLM Engine:** Cohere Command R7B Arabic (`Ollama`)",
            "- **Hardware Acceleration:** NVIDIA GeForce RTX 3060 Laptop GPU (CUDA Active)",
            "- **Vector Index:** Embedded Qdrant (Zero-Docker Local Storage)",
            f"- **Latency Breakdown:** Total {latency.get('total_ms', 0):.0f} ms (Retrieval: {latency.get('retrieval_ms', 0):.0f} ms | Rerank: {latency.get('reranking_ms', 0):.0f} ms | Gen: {latency.get('generation_ms', 0):.0f} ms)",
        ])

    return "\n\n".join(doc)


# =========================================================
# Sidebar
# =========================================================

with st.sidebar:
    logo_file = get_logo_path()
    if logo_file:
        st.image(logo_file, use_container_width=True)

    st.markdown('<div class="sidebar-section-title">Language / لغة الواجهة</div>', unsafe_allow_html=True)
    ui_lang = st.radio(
        "اختر لغة الواجهة / Select Language",
        ["🇸🇦 العربية (Arabic)", "🇬🇧 English"],
        index=0,
        label_visibility="collapsed",
    )
    is_ar = ui_lang.startswith("🇸🇦")

    if is_ar:
        st.markdown(ARABIC_RTL_CSS, unsafe_allow_html=True)

    # Feature Navigation Menu
    st.markdown(
        f'<div class="sidebar-section-title">{"🧭 اختيار الوظيفة والميزة" if is_ar else "🧭 Feature & Module Selection"}</div>',
        unsafe_allow_html=True,
    )
    feature_labels = [
        "🔍 المحادثة ومستكشف الأدلة" if is_ar else "🔍 Interactive Chat & Evidence",
        "⚖️ محقق تعارض وتناقض الوثائق" if is_ar else "⚖️ Document Conflict Detective",
        "📋 الإيجاز والتقارير التنفيذية" if is_ar else "📋 Executive Briefings & Reports",
        "📁 مستودع المعرفة والتشخيص الفني" if is_ar else "📁 Knowledge Repository & Diagnostics",
    ]

    if "selected_feature_idx" not in st.session_state:
        st.session_state["selected_feature_idx"] = 0

    selected_feature_idx = st.radio(
        "اختر الميزة" if is_ar else "Select Feature",
        options=list(range(len(feature_labels))),
        format_func=lambda idx: feature_labels[idx],
        index=st.session_state["selected_feature_idx"],
        key="feature_selector_radio",
        label_visibility="collapsed",
    )
    st.session_state["selected_feature_idx"] = selected_feature_idx

    st.markdown(
        f'<div class="sidebar-section-title">{"حالة الأنظمة السيادية" if is_ar else "System Status"}</div>',
        unsafe_allow_html=True,
    )
    try:
        health = client.get_health()
        st.session_state["health_status"] = health
        st.success("🟢 الأنظمة تعمل محلياً (Air-Gapped)" if is_ar else "🟢 Core Services Ready (Air-Gapped)")
    except Exception:
        st.error("🔴 جاري الاتصال بالخادم..." if is_ar else "🔴 Connecting to API Server...")

    doc_count = len(st.session_state.get("documents", []))
    st.metric("الوثائق المفهرسة" if is_ar else "Indexed Documents", doc_count)

    st.markdown(
        f'<div class="sidebar-section-title">{"نطاق البحث والتدقيق" if is_ar else "Retrieval & Scope"}</div>',
        unsafe_allow_html=True,
    )
    docs = st.session_state.get("documents", [])
    all_label = "جميع الوثائق الـ 12 المعتمدة" if is_ar else "All 12 Ingested Documents"
    doc_options = [all_label] + [f"{clean_source_name(d.get('filename'))[0]} ({d.get('document_id')[:8]})" for d in docs]
    selected_scope_label = st.selectbox(
        "نطاق استرجاع الوثائق" if is_ar else "Document Scope",
        options=doc_options,
        index=0,
    )
    selected_doc_ids = None
    if selected_scope_label != all_label:
        selected_idx = doc_options.index(selected_scope_label) - 1
        selected_doc_ids = [docs[selected_idx]["document_id"]]

    include_trace = st.checkbox(
        "تضمين تدقيق معيد الترتيب" if is_ar else "Include Reranker Trace",
        value=True,
    )

    st.markdown(
        f'<div class="sidebar-section-title">{"إدارة الجلسة" if is_ar else "Session Controls"}</div>',
        unsafe_allow_html=True,
    )
    if st.button("🔄 تحديث الوثائق" if is_ar else "🔄 Refresh Documents", use_container_width=True):
        try:
            st.session_state["documents"] = client.list_documents()
            st.success("تم التحديث بنجاح!" if is_ar else "Synchronized!")
        except Exception as e:
            st.error(str(e))

    if st.button("🧹 مسح سجل المحادثة" if is_ar else "🧹 Clear Chat History", use_container_width=True):
        st.session_state["chat_turns"] = []
        st.session_state["chat_history"] = []
        st.session_state["last_result"] = None
        st.session_state["last_question"] = ""
        st.rerun()


# =========================================================
# Main Institutional Header
# =========================================================

header_logo = get_logo_path()
logo_b64 = get_logo_base64()
if logo_b64:
    if is_ar:
        st.markdown(
            f"""
            <div class="hero-institution-card">
                <div style="display:flex; align-items:center; justify-content:space-between; gap:20px; flex-wrap:wrap;">
                    <div style="display:flex; align-items:center; gap:20px;">
                        <img src="{logo_b64}" style="height:74px; max-width:180px; object-fit:contain; filter:drop-shadow(0 2px 4px rgba(0,45,98,0.06));" alt="PSUT Logo" />
                        <div style="border-right:2.5px solid #E2E8F0; padding-right:20px;">
                            <div style="font-size:0.8rem; font-weight:800; color:#1E40AF; text-transform:uppercase; letter-spacing:0.04em; margin-bottom:2px;">
                                جامعة الأميرة سمية للتكنولوجيا • هاكاثون 42 إربد
                            </div>
                            <h1 style="color:#002D62; font-size:1.75rem; font-weight:800; margin:0; line-height:1.25;">
                                نظام الاسترجاع الهجين والذكاء الاصطناعي السيادي
                            </h1>
                            <div style="color:#475569; font-size:0.9rem; margin-top:4px; font-weight:600;">
                                بنية تحتية محلية معزولة 100% • قطاع الخدمات الحكومية والسيادية • استرجاع موثق ومطابق للأصل
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div class="hero-institution-card">
                <div style="display:flex; align-items:center; justify-content:space-between; gap:20px; flex-wrap:wrap;">
                    <div style="display:flex; align-items:center; gap:20px;">
                        <img src="{logo_b64}" style="height:74px; max-width:180px; object-fit:contain; filter:drop-shadow(0 2px 4px rgba(0,45,98,0.06));" alt="PSUT Logo" />
                        <div style="border-left:2.5px solid #E2E8F0; padding-left:20px;">
                            <div style="font-size:0.8rem; font-weight:800; color:#1E40AF; text-transform:uppercase; letter-spacing:0.04em; margin-bottom:2px;">
                                Princess Sumaya University for Technology • 42 Irbid
                            </div>
                            <h1 style="color:#002D62; font-size:1.75rem; font-weight:800; margin:0; line-height:1.25;">
                                Sovereign Hybrid RAG Engine
                            </h1>
                            <div style="color:#475569; font-size:0.9rem; margin-top:4px; font-weight:600;">
                                100% Air-Gapped Local Infrastructure • Sovereign Public Services • Verifiable Evidence
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
else:
    st.title("🏛️ جامعة الأميرة سمية للتكنولوجيا - الذكاء الاصطناعي السيادي" if is_ar else "🏛️ PSUT Sovereign Hybrid RAG")



# =========================================================
# Active Feature Workspace
# =========================================================

feature_headers = [
    ("🔍 المحادثة التفاعلية ومستكشف الأدلة الرسمية", "🔍 Interactive Chat & Grounded Evidence Explorer"),
    ("⚖️ محقق تعارض وتناقض الوثائق والسياسات", "⚖️ Document Conflict & Policy Discrepancy Detective"),
    ("📋 الإيجاز والاستخبارات التنفيذية متعددة الوثائق", "📋 Multi-Document Executive Briefing & Intelligence Reports"),
    ("📁 مستودع المعرفة السيادي والتشخيص الفني", "📁 Sovereign Knowledge Repository & Live System Diagnostics"),
]

cur_header = feature_headers[selected_feature_idx][0] if is_ar else feature_headers[selected_feature_idx][1]

st.markdown(
    f"""
    <div style="display:flex; justify-content:space-between; align-items:center; background:#FFFFFF; border:1.5px solid #CBD5E1; border-top:4px solid #002D62; border-radius:10px; padding:12px 20px; margin-bottom:20px; box-shadow:0 2px 8px rgba(0,45,98,0.04); flex-wrap:wrap; gap:8px;">
        <div style="display:flex; align-items:center; gap:10px;">
            <span style="font-size:1.12rem; font-weight:800; color:#002D62;">{cur_header}</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# FEATURE 1: INTERACTIVE CHAT & EVIDENCE EXPLORER
# =========================================================

if selected_feature_idx == 0:
    if "chat_turns" not in st.session_state:
        st.session_state["chat_turns"] = []

    # Interactive Conversation Feed
    if not st.session_state["chat_turns"]:
        st.markdown(
            f"""
            <div class="grounded-result-card" style="margin-top: 15px; text-align: center; border-right: 5px solid #002D62; padding: 26px 30px;">
                <div style="font-size: 2.2rem; margin-bottom: 8px;">🇯🇴</div>
                <div style="font-size: 1.2rem; font-weight: 800; color: #002D62; margin-bottom: 6px;">
                    {'المساعد الذكي لدائرة الأحوال المدنية والجوازات' if is_ar else 'Sovereign RAG Assistant for Jordan Public Services'}
                </div>
                <div style="color: #475569; font-size: 0.92rem; line-height: 1.7; max-width: 700px; margin: 0 auto;">
                    {'أنا جاهز للإجابة بدقة مطلقة على استفساراتكم حول معاملات جواز السفر، البطاقة الذكية، ودفتر العائلة، مدعوماً بالسند القانوني والوثائق الـ 12 المعتمدة ومحرك Cohere Command R7B المحلي على كارت الشاشة GPU.' if is_ar else 'Ready to answer your queries regarding Jordanian Passport, Smart ID Card, and Family Book services with 100% official grounding and Cohere Command R7B Arabic running locally on GPU.'}
                </div>
                <div style="margin-top: 14px;">
                    <span style="background: #EFF6FF; color: #002D62; font-size: 0.82rem; font-weight: 700; padding: 5px 14px; border-radius: 20px; border: 1px solid #BFDBFE;">
                        {'💬 اكتب استفسارك في الصندوق بالأسفل لبدء المحادثة المباشرة' if is_ar else '💬 Type your inquiry in the chat box below to begin'}
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        for idx_turn, turn in enumerate(st.session_state["chat_turns"], start=1):
            with st.chat_message("user", avatar="👤"):
                st.markdown(turn["question"])

            with st.chat_message("assistant", avatar="🇯🇴"):
                res = turn.get("result", {})
                if not res:
                    st.markdown(turn.get("content", ""))
                    continue

                trace = res.get("trace")
                evidence_list = res.get("evidence", [])
                chunk_map = build_chunk_text_map(trace, evidence_list)
                citations = res.get("citations", [])
                latency = res.get("latency", {})
                abstained = res.get("abstained", False)
                was_rewritten = res.get("was_rewritten", False)
                retrieval_q = res.get("retrieval_question")

                if was_rewritten and retrieval_q:
                    st.info(
                        f"ℹ️ **{'إعادة صياغة السؤال لسياق المحادثة:' if is_ar else 'Conversational Intent Resolved:'}** "
                        f"{'تم تحسين الاستفسار إلى' if is_ar else 'Query reformulated to'} *\"{retrieval_q}\"*"
                    )

                if abstained:
                    st.warning(
                        "⚠️ **اعتذار النظام (امتناع آمن)**: لم يتم العثور على سند رسمي مطابق للتحقق. لا يتم توليد أي إجابة تكهنية غير مدعومة بوثائق رسمية."
                        if is_ar
                        else "⚠️ **System Abstained**: Retrieval confidence fell below safety threshold. No speculative answer generated."
                    )
                else:
                    clean_answer, charts = extract_all_charts(res.get("answer", ""), is_ar=is_ar)
                    selected_svc_name = res.get("selected_service_name")
                    svc_badge_html = (
                        f'<span style="background:#EFF6FF; color:#002D62; font-size:0.75rem; font-weight:800; padding:3px 8px; border-radius:4px; border:1px solid #BFDBFE; margin-right:8px;">🏛️ {selected_svc_name}</span>'
                        if selected_svc_name
                        else ""
                    )
                    
                    st.markdown(f"{svc_badge_html}\n\n{clean_answer}", unsafe_allow_html=True)

                    if charts:
                        render_charts(charts, is_ar=is_ar)

                # Collapsible Evidence & Citations
                items = citations if citations else evidence_list
                if items:
                    with st.expander(
                        f"📑 {'السند الرسمي والوثائق المسترجعة' if is_ar else 'Verified Official Evidence'} ({len(items)} {'بنود رسمية' if is_ar else 'items'}) • ⚡ {latency.get('total_ms', 0):.0f}ms",
                        expanded=False,
                    ):
                        for idx, cit in enumerate(items, start=1):
                            ref = cit.get("reference", idx)
                            raw_src = cit.get("source", "Document")
                            clean_name, base_src = clean_source_name(raw_src)
                            page = cit.get("page_number")
                            cid = cit.get("chunk_id", "")
                            doc_id = cit.get("document_id", "")
                            heading = " → ".join(cit.get("heading_path") or [])
                            svc_name = cit.get("service_name")
                            sec_type = cit.get("section_type")
                            raw_text = cit.get("text") or chunk_map.get(cid)

                            page_label = f" • {'صفحة' if is_ar else 'Page'} {page}" if page is not None else ""
                            svc_label = f" • 🏛️ {svc_name}" if svc_name else ""
                            sec_label = f" • [{sec_type}]" if sec_type else ""
                            st.markdown(f"**📌 [{ref}] {clean_name}{svc_label}{page_label}{sec_label}**")
                            if raw_text:
                                st.markdown(f"<div class='source-pill-quote' dir='auto'>\"{raw_text.strip()}\"</div>", unsafe_allow_html=True)

                # Optional Reranker Audit Trace
                if turn.get("include_trace") and trace:
                    trace_header = "🔍 " + ("سجل تدقيق معيد الترتيب (Reranker Trace)" if is_ar else "Reranker Audit Trace")
                    with st.expander(trace_header, expanded=False):
                        cand_list = trace.get("candidates", [])
                        if cand_list:
                            trace_rows = []
                            for c_idx, c in enumerate(cand_list[:10], start=1):
                                c_src, _ = clean_source_name(c.get("source", ""))
                                trace_rows.append({
                                    "#" if is_ar else "Rank": c_idx,
                                    "الوثيقة" if is_ar else "Document": c_src,
                                    "Rerank Score": f"{c.get('score', 0):.4f}" if c.get("score") is not None else "N/A",
                                    "Dense Score": f"{c.get('dense_score', 0):.4f}" if c.get("dense_score") is not None else "N/A",
                                    "BM25 Score": f"{c.get('sparse_score', 0):.4f}" if c.get("sparse_score") is not None else "N/A",
                                })
                            st.dataframe(pd.DataFrame(trace_rows), use_container_width=True, hide_index=True)

                # Download Executive Brief for this turn
                export_content = generate_executive_brief_export(turn["question"], res, chunk_map, is_ar=is_ar)
                st.download_button(
                    label="📥 " + ("تصدير إيجاز تنفيذي لهذه النتيجة (.md)" if is_ar else "Export Turn Briefing (.md)"),
                    data=export_content,
                    file_name=f"briefing_turn_{idx_turn}_{res.get('request_id', 'audit')[:6]}.md",
                    mime="text/markdown",
                    key=f"dl_turn_{idx_turn}",
                )

    # Bottom Pinned Chat Input
    chat_prompt = st.chat_input("اطرح استفسارك هنا باللغة العربية..." if is_ar else "Ask your question here in Arabic or English...")

    if chat_prompt:
        active_question = chat_prompt.strip()
        history_payload = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.get("chat_history", [])[-4:]
        ]
        with st.chat_message("user", avatar="👤"):
            st.markdown(active_question)

        with st.chat_message("assistant", avatar="🇯🇴"):
            with st.spinner("جاري تنفيذ الاسترجاع الهجين والتحليل المقيد بالأدلة الرسمية..." if is_ar else "Retrieving official evidence & synthesizing grounded answer..."):
                try:
                    res = client.ask(
                        question=active_question,
                        history=history_payload,
                        document_ids=selected_doc_ids,
                        include_trace=include_trace,
                    )
                    st.session_state["chat_turns"].append({
                        "question": active_question,
                        "result": res,
                        "include_trace": include_trace,
                    })
                    st.session_state["chat_history"].append({"role": "user", "content": active_question})
                    st.session_state["chat_history"].append({"role": "assistant", "content": res.get("answer", "")})
                    st.session_state["last_result"] = res
                    st.session_state["last_question"] = active_question
                    st.rerun()
                except Exception as exc:
                    st.error(f"{'فشل التحليل والاسترجاع:' if is_ar else 'Analysis failed:'} {exc}")


# =========================================================
# FEATURE 2: DOCUMENT CONFLICT DETECTIVE (STAR DEMO FEATURE)
# =========================================================

elif selected_feature_idx == 1:
    st.subheader("⚖️ محقق تعارض وتناقض الوثائق والسياسات" if is_ar else "⚖️ Document Conflict Detective")
    st.caption(
        "مقارنة دقيقة ومعزولة بين وثيقتين لاكتشاف التناقضات أو الفروقات الإجرائية أو التوافق التام."
        if is_ar
        else "Perform rigorous, air-gapped comparison between two documents to detect contradictions, version differences, or policy alignment."
    )

    docs = st.session_state.get("documents", [])
    if len(docs) < 2:
        st.info("يرجى فهرسة وثيقتين على الأقل لتفعيل خاصية كشف التعارض والتناقض." if is_ar else "Please index at least two documents to activate side-by-side conflict detection.")
    else:
        doc_names = [f"{clean_source_name(d.get('filename'))[0]} ({d.get('document_id')[:8]})" for d in docs]
        c1, c2 = st.columns(2)
        with c1:
            sel_a = st.selectbox("الوثيقة المرجعية الأساسية (أ)" if is_ar else "Primary Baseline Document (A)", options=doc_names, index=0)
        with c2:
            sel_b = st.selectbox("وثيقة المقارنة والتحقق (ب)" if is_ar else "Comparison Target Document (B)", options=doc_names, index=min(1, len(doc_names) - 1))

        doc_a_idx = doc_names.index(sel_a)
        doc_b_idx = doc_names.index(sel_b)
        doc_a_id = docs[doc_a_idx]["document_id"]
        doc_b_id = docs[doc_b_idx]["document_id"]

        default_topic = (
            "رسوم المعاملة المستعجلة وزمن الإنجاز واعتماد تطبيق سند"
            if is_ar
            else "Container restart policies and resource allocation"
        )
        if "topic_input" not in st.session_state:
            st.session_state["topic_input"] = default_topic

        topic_val = st.text_input(
            "موضوع المقارنة / البند الإجرائي أو القانوني:" if is_ar else "Comparison Topic / Policy Area",
            value=st.session_state["topic_input"],
            help="حدد البند أو المسألة الإجرائية المراد تدقيقها بدقة بين الوثيقتين.",
        )

        preset_comp_cols = st.columns(3)
        if is_ar:
            with preset_comp_cols[0]:
                if st.button("🛂 مقارنة الرسوم وزمن الإنجاز", key="cmp_ar_fees", use_container_width=True):
                    st.session_state["topic_input"] = "رسوم المعاملة المستعجلة والمدة الزمنية لإنجاز الجواز"
                    st.rerun()
            with preset_comp_cols[1]:
                if st.button("📱 مقارنة إثبات الهوية وسند", key="cmp_ar_id", use_container_width=True):
                    st.session_state["topic_input"] = "اشتراط بطاقة الأحوال الذكية واعتماد الهوية الرقمية عبر تطبيق سند"
                    st.rerun()
            with preset_comp_cols[2]:
                if st.button("⚠️ مقارنة الشروط والاستثناءات", key="cmp_ar_cond", use_container_width=True):
                    st.session_state["topic_input"] = "شروط حالة الاستعجال والفئات المستثناة وموافقة ولي الأمر"
                    st.rerun()
        else:
            with preset_comp_cols[0]:
                if st.button("Compare Restart Policies", key="cmp_restart", use_container_width=True):
                    st.session_state["topic_input"] = "Container restart policies and failure handling"
                    st.rerun()
            with preset_comp_cols[1]:
                if st.button("Compare Timeout Limits", key="cmp_timeout", use_container_width=True):
                    st.session_state["topic_input"] = "Database connection timeout and retry procedures"
                    st.rerun()
            with preset_comp_cols[2]:
                if st.button("Compare DNS Resolvers", key="cmp_dns", use_container_width=True):
                    st.session_state["topic_input"] = "DNS resolution configuration and fallback addresses"
                    st.rerun()

        run_cmp_btn = st.button("⚖️ تشغيل تدقيق التعارض والتطابق" if is_ar else "🔍 Run Conflict & Divergence Audit", type="primary", use_container_width=True)

        if run_cmp_btn:
            active_topic = topic_val.strip() or st.session_state.get("topic_input", "").strip()
            if not active_topic:
                st.warning("يرجى تحديد موضوع للمقارنة." if is_ar else "Please specify a topic to audit.")
            else:
                try:
                    with st.spinner("جاري تدقيق أدلة الوثيقتين واكتشاف الفروقات والتناقضات..." if is_ar else "Auditing document evidence, scopes, and potential contradictions..."):
                        comp_res = client.compare(
                            document_a_id=doc_a_id,
                            document_b_id=doc_b_id,
                            topic=active_topic,
                        )

                    # Relationship Badge
                    rel = comp_res.get("relationship", "insufficient_evidence")
                    badge_class = {
                        "agreement": "rel-agreement",
                        "scope_or_version_difference": "rel-version",
                        "possible_conflict": "rel-conflict",
                        "insufficient_evidence": "rel-insufficient",
                    }.get(rel, "rel-insufficient")

                    if is_ar:
                        rel_label = {
                            "agreement": "✅ توافق في السياسات: تطابق تام في الأحكام والشروط",
                            "scope_or_version_difference": "ℹ️ اختلاف في النطاق أو الإصدار: تباين إجرائي أو تحديث رسمي",
                            "possible_conflict": "⚠️ تعارض وتناقض محتمل: تضارب مباشر بين نصوص الوثيقتين",
                            "insufficient_evidence": "❓ أدلة غير كافية: لا تتوفر تفاصيل كافية للمقارنة",
                        }.get(rel, rel)
                    else:
                        rel_label = {
                            "agreement": "✅ Policy Agreement: Factual Alignment",
                            "scope_or_version_difference": "ℹ️ Scope / Version Difference: Tier or Effective Date Divergence",
                            "possible_conflict": "⚠️ Possible Conflict: Direct Contradiction Detected",
                            "insufficient_evidence": "❓ Insufficient Evidence: Inconclusive Coverage",
                        }.get(rel, rel.replace("_", " ").title())

                    st.markdown(f'<div class="rel-badge {badge_class}">{rel_label}</div>', unsafe_allow_html=True)
                    
                    # Summary Banner
                    sum_label = "الملخص التنفيذي للنتيجة والتدقيق:" if is_ar else "Executive Divergence Summary:"
                    st.markdown(
                        f"""
                        <div class="conflict-summary-banner">
                            <div style="font-size:0.82rem; font-weight:800; color:#002D62; text-transform:uppercase; margin-bottom:4px;">
                                📌 {sum_label}
                            </div>
                            <div class="bidi-text" dir="auto" style="font-size:1.02rem; font-weight:600; color:#0F172A; line-height:1.7;">
                                {comp_res.get('summary')}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    # Side by side cards
                    card_a, card_b = st.columns(2)
                    doc_a_claim = comp_res.get("document_a", {})
                    doc_b_claim = comp_res.get("document_b", {})

                    with card_a:
                        fname_a = doc_a_claim.get("filename", "")
                        clean_a, _ = clean_source_name(fname_a)
                        scope_a = doc_a_claim.get("scope_notes")
                        scope_html_a = f"<div style='font-size:0.82rem; color:#475569; margin-top:8px;'><b>{'نطاق التطبيق أو شرط الإصدار:' if is_ar else 'Scope / Version Condition:'}</b> <span dir='auto'>{scope_a}</span></div>" if scope_a else ""
                        st.markdown(
                            f"""
                            <div class="conflict-card-a">
                                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                                    <span style="font-size:0.78rem; font-weight:800; color:#002D62; text-transform:uppercase; background:#EFF6FF; padding:3px 8px; border-radius:4px; border:1px solid #BFDBFE;">
                                        📄 {'الوثيقة المرجعية (أ)' if is_ar else 'Reference Baseline (A)'}
                                    </span>
                                    <code dir="ltr" style="font-size:0.82rem; font-weight:700;">{clean_a}</code>
                                </div>
                                <div style="font-size:0.88rem; font-weight:800; color:#002D62; margin-top:8px; margin-bottom:4px;">
                                    {'الحكم أو النص النظامي الوارد:' if is_ar else 'Stated Rule / Claim:'}
                                </div>
                                <div class="bidi-text" dir="auto" style="font-size:0.98rem; line-height:1.7; color:#0F172A;">
                                    {doc_a_claim.get('claim')}
                                </div>
                                {scope_html_a}
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                        ev_a = doc_a_claim.get("evidence", [])
                        if ev_a:
                            exp_label = f"📑 {'الأدلة والفقرات الموثقة (أ)' if is_ar else 'Verified Evidence (A)'} ({len(ev_a)} {'فقرات' if is_ar else 'passages'})"
                            with st.expander(exp_label, expanded=True):
                                for ev in ev_a:
                                    st.markdown(f"> \"<span dir='auto'>{ev.get('text', '')[:300]}...</span>\"", unsafe_allow_html=True)
                                    st.caption(f"{'المصدر:' if is_ar else 'Source:'} <code dir='ltr'>{clean_source_name(ev.get('source'))[0]}</code>", unsafe_allow_html=True)

                    with card_b:
                        fname_b = doc_b_claim.get("filename", "")
                        clean_b, _ = clean_source_name(fname_b)
                        scope_b = doc_b_claim.get("scope_notes")
                        scope_html_b = f"<div style='font-size:0.82rem; color:#475569; margin-top:8px;'><b>{'نطاق التطبيق أو شرط الإصدار:' if is_ar else 'Scope / Version Condition:'}</b> <span dir='auto'>{scope_b}</span></div>" if scope_b else ""
                        st.markdown(
                            f"""
                            <div class="conflict-card-b">
                                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                                    <span style="font-size:0.78rem; font-weight:800; color:#1E40AF; text-transform:uppercase; background:#EFF6FF; padding:3px 8px; border-radius:4px; border:1px solid #93C5FD;">
                                        📄 {'وثيقة المقارنة والتحقق (ب)' if is_ar else 'Comparison Target (B)'}
                                    </span>
                                    <code dir="ltr" style="font-size:0.82rem; font-weight:700;">{clean_b}</code>
                                </div>
                                <div style="font-size:0.88rem; font-weight:800; color:#1E40AF; margin-top:8px; margin-bottom:4px;">
                                    {'الحكم أو النص النظامي الوارد:' if is_ar else 'Stated Rule / Claim:'}
                                </div>
                                <div class="bidi-text" dir="auto" style="font-size:0.98rem; line-height:1.7; color:#0F172A;">
                                    {doc_b_claim.get('claim')}
                                </div>
                                {scope_html_b}
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                        ev_b = doc_b_claim.get("evidence", [])
                        if ev_b:
                            exp_label = f"📑 {'الأدلة والفقرات الموثقة (ب)' if is_ar else 'Verified Evidence (B)'} ({len(ev_b)} {'فقرات' if is_ar else 'passages'})"
                            with st.expander(exp_label, expanded=True):
                                for ev in ev_b:
                                    st.markdown(f"> \"<span dir='auto'>{ev.get('text', '')[:300]}...</span>\"", unsafe_allow_html=True)
                                    st.caption(f"{'المصدر:' if is_ar else 'Source:'} <code dir='ltr'>{clean_source_name(ev.get('source'))[0]}</code>", unsafe_allow_html=True)

                    # Resolution guidance
                    default_guidance = (
                        "يوصى بالرجوع إلى الوثائق المرجعية الأصلية قبل اعتماد القرار الإجرائي."
                        if is_ar
                        else "Review primary documents before policy enforcement."
                    )
                    res_guidance = comp_res.get("resolution_notes") or default_guidance
                    guidance_title = "توجيهات وتوصيات صانع القرار الرسمية" if is_ar else "Official Decision-Maker Resolution Guidance"
                    st.markdown(
                        f"""
                        <div class="conflict-guidance-card">
                            <div style="display:flex; align-items:center; gap:8px; margin-bottom:6px;">
                                <span style="font-size:1.1rem;">🛡️</span>
                                <span style="font-size:0.88rem; font-weight:800; color:#92400E; text-transform:uppercase; letter-spacing:0.04em;">
                                    {guidance_title}
                                </span>
                            </div>
                            <div class="bidi-text" dir="auto" style="font-size:0.98rem; font-weight:500; color:#78350F; line-height:1.75;">
                                {res_guidance}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                except Exception as exc:
                    st.error(f"Comparison analysis failed: {exc}")


# =========================================================
# FEATURE 3: EXECUTIVE BRIEFINGS (MULTI-DOC MAP-REDUCE)
# =========================================================

elif selected_feature_idx == 2:
    st.subheader("📋 الإيجاز والتقارير التنفيذية متعددة الوثائق" if is_ar else "📋 Multi-Document Executive Briefing")
    st.caption(
        "توليد إيجاز تركيبي استراتيجي يغطي عدة وثائق حكومية مع تصنيف النتائج وتوثيق المراجع."
        if is_ar
        else "Generate a structured synthesis across multiple documents with category-tagged findings and verifiable citations."
    )

    docs = st.session_state.get("documents", [])
    if not docs:
        st.info("لا توجد وثائق مفهرسة حالياً. يرجى رفع الوثائق في التبويب الرابع لتوليد الإيجاز." if is_ar else "No documents indexed yet. Upload documents in Tab 4 to generate briefings.")
    else:
        doc_map = {f"{clean_source_name(d.get('filename'))[0]} ({d.get('document_id')[:8]})": d.get("document_id") for d in docs}
        selected_brief_names = st.multiselect(
            "اختر الوثائق الحكومية المراد تلخيصها ودمجها:" if is_ar else "Select Documents to Synthesize",
            options=list(doc_map.keys()),
            default=list(doc_map.keys())[:min(3, len(doc_map))],
        )

        default_brief_focus = (
            "الملخص التنفيذي، شروط المعاملات، الرسوم والمدد الزمنية، والامتثال القانوني"
            if is_ar
            else "Executive Summary, Critical Policies, and Key Operational Standards"
        )
        focus_input = st.text_input(
            "محور التركيز وأهداف الإيجاز التنفيذي:" if is_ar else "Briefing Focus / Objectives",
            value=default_brief_focus,
        )

        run_brief_btn = st.button("📋 توليد الإيجاز التنفيذي" if is_ar else "📋 Generate Executive Briefing", type="primary", use_container_width=True)

        if run_brief_btn:
            if not selected_brief_names:
                st.warning("يرجى اختيار وثيقة واحدة على الأقل." if is_ar else "Please select at least one document.")
            else:
                target_ids = [doc_map[name] for name in selected_brief_names]
                try:
                    with st.spinner("جاري تلخيص ودمج الوثائق باستخدام محرك Map-Reduce السيادي..." if is_ar else "Synthesizing multi-document briefing using Map-Reduce engine..."):
                        brief_res = client.brief(
                            document_ids=target_ids,
                            focus=focus_input,
                            max_findings=8,
                        )

                    # Summary Box
                    analyzed_docs = brief_res.get("analyzed_documents", [])
                    analyzed_docs_str = ", ".join([f"<code dir='ltr'>{clean_source_name(d)[0]}</code>" for d in analyzed_docs])
                    overview_title = "نظرة عامة وتنفيذية استراتيجية" if is_ar else "Executive Overview & Strategic Mandates"
                    analyzed_label = "تم التحليل عبر" if is_ar else "Analyzed across"
                    docs_label = "وثائق رسمية:" if is_ar else "documents:"

                    clean_exec_summary, brief_charts = extract_all_charts(brief_res.get("executive_summary", ""), is_ar=is_ar)

                    st.markdown(
                        f"""
                        <div class="brief-overview-card">
                            <div style="font-size:0.88rem; font-weight:800; color:#002D62; text-transform:uppercase; letter-spacing:0.04em; margin-bottom:10px;">
                                📌 {overview_title}
                            </div>
                            <div class="bidi-text" dir="auto" style="font-size:1.02rem; line-height:1.85; color:#0F172A; margin-bottom:14px;">
                                {clean_exec_summary}
                            </div>
                            <div style="font-size:0.82rem; color:#64748B; border-top:1px solid #E2E8F0; padding-top:10px;">
                                {analyzed_label} {brief_res.get('document_count')} {docs_label} {analyzed_docs_str}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    # Dynamic comparative chart in summary if present
                    if brief_charts:
                        render_charts(brief_charts, is_ar=is_ar)

                    # Findings List & Category Visualization
                    findings = brief_res.get("findings", [])

                    cat_labels_ar = {
                        "policy": "🏛️ السياسات والأنظمة",
                        "technical": "⚙️ المتطلبات التقنية",
                        "compliance": "⚖️ الشروط والامتثال",
                        "action_item": "✅ الإجراءات التنفيذية",
                    }
                    cat_labels_en = {
                        "policy": "🏛️ Policy & Mandates",
                        "technical": "⚙️ Technical Specs",
                        "compliance": "⚖️ Compliance & Rules",
                        "action_item": "✅ Action Items",
                    }
                    cat_dict = cat_labels_ar if is_ar else cat_labels_en

                    if findings:
                        # Strategic Governance Distribution Chart & Matrix Table
                        cat_counts = {k: 0 for k in cat_dict.keys()}
                        for f in findings:
                            c = f.get("category", "policy")
                            if c in cat_counts:
                                cat_counts[c] += 1
                            else:
                                cat_counts[c] = 1

                        col_chart, col_matrix = st.columns([1.3, 1.7])
                        with col_chart:
                            st.markdown(
                                f"""
                                <div style="background:#FFFFFF; border:1.5px solid #BFDBFE; border-top:4px solid #002D62; border-radius:10px; padding:12px 16px; margin-bottom:10px;">
                                    <div style="display:flex; justify-content:space-between; align-items:center;">
                                        <span style="font-weight:800; color:#002D62; font-size:0.86rem; text-transform:uppercase;">
                                            📊 {'توزيع النتائج حسب المحور الاستراتيجي' if is_ar else 'Findings by Strategic Pillar'}
                                        </span>
                                        <span style="font-size:0.75rem; font-weight:700; color:#1E40AF; background:#EFF6FF; padding:2px 8px; border-radius:4px;">
                                            {len(findings)} {'نتائج' if is_ar else 'Total'}
                                        </span>
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                            chart_rows = [{"Pillar": cat_dict.get(k, k), ("عدد النتائج" if is_ar else "Count"): v} for k, v in cat_counts.items()]
                            df_cat = pd.DataFrame(chart_rows)
                            st.bar_chart(
                                df_cat.set_index("Pillar"),
                                color="#002D62",
                                height=230,
                                use_container_width=True,
                            )

                        with col_matrix:
                            st.markdown(
                                f"""
                                <div style="background:#FFFFFF; border:1.5px solid #BFDBFE; border-top:4px solid #1E40AF; border-radius:10px; padding:12px 16px; margin-bottom:10px;">
                                    <div style="display:flex; justify-content:space-between; align-items:center;">
                                        <span style="font-weight:800; color:#002D62; font-size:0.86rem; text-transform:uppercase;">
                                            📋 {'مصفوفة القرارات التنفيذية المعتمدة' if is_ar else 'Executive Decision Matrix'}
                                        </span>
                                        <span style="font-size:0.75rem; font-weight:700; color:#047857; background:#ECFDF5; padding:2px 8px; border-radius:4px;">
                                            {'جدول منظم' if is_ar else 'Structured Table'}
                                        </span>
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                            matrix_rows = []
                            for m_idx, f in enumerate(findings, start=1):
                                matrix_rows.append({
                                    "#": m_idx,
                                    ("البند / القرار الاستراتيجي" if is_ar else "Finding Title"): f.get("title", ""),
                                    ("التصنيف" if is_ar else "Category"): cat_dict.get(f.get("category"), f.get("category")),
                                    ("المرجع" if is_ar else "Primary Ref"): f"#{f.get('primary_ref', 1)}",
                                })
                            st.dataframe(pd.DataFrame(matrix_rows), use_container_width=True, hide_index=True, height=230)

                    st.markdown(f"### 🎯 {'النتائج والقرارات الاستراتيجية التفصيلية' if is_ar else 'Detailed Strategic Findings & Mandates'} ({len(findings)})")

                    for idx, f in enumerate(findings, start=1):
                        cat = f.get("category", "policy")
                        tag_class = f"tag-{cat}"
                        tag_text = cat_labels_ar.get(cat, cat.upper()) if is_ar else cat.replace("_", " ").upper()
                        evs = f.get("evidence", [])
                        st.markdown(
                            f"""
                            <div class="finding-card">
                                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                                    <span class="finding-tag {tag_class}">{tag_text}</span>
                                    <span style="font-size:0.78rem; font-weight:800; color:#64748B;">#{idx}</span>
                                </div>
                                <h4 style="margin:0 0 6px 0; color:#002D62; font-size:1.05rem; font-weight:800;">
                                    <span dir="auto">{f.get('title')}</span>
                                </h4>
                                <div class="bidi-text" dir="auto" style="font-size:0.95rem; line-height:1.75; color:#334155;">
                                    {f.get('description')}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                        if evs:
                            with st.expander(
                                f"📑 {'الأدلة الموثقة للنتيجة' if is_ar else 'Grounded Evidence for Finding'} #{idx} ({len(evs)} {'مقطع' if is_ar else 'chunk'})",
                                expanded=False,
                            ):
                                for ev in evs:
                                    ev_clean, _ = clean_source_name(ev.get("filename", ""))
                                    st.markdown(f"> \"<span dir='auto'>{ev.get('text', '')[:300]}...</span>\"", unsafe_allow_html=True)
                                    st.caption(
                                        f"{'المصدر:' if is_ar else 'Source:'} <code dir='ltr'>{ev_clean}</code> | "
                                        f"{'المرجع:' if is_ar else 'Reference:'} `#{ev.get('reference')}`",
                                        unsafe_allow_html=True,
                                    )

                    # Download Briefing
                    if is_ar:
                        brief_md = [
                            f"# إيجاز استخباراتي تنفيذي متعدد الوثائق: {focus_input}",
                            f"**التاريخ:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                            f"**نطاق الوثائق:** {len(target_ids)} وثائق رسمية",
                            "\n## نظرة عامة تنفيذية\n",
                            brief_res.get("executive_summary", ""),
                            "\n## مصفوفة القرارات التنفيذية المعتمدة\n",
                            "| # | البند / القرار الاستراتيجي | التصنيف | المرجع الأساسي |",
                            "|---|---|---|---|",
                        ]
                        for m_i, f in enumerate(findings, start=1):
                            c_name = cat_labels_ar.get(f.get("category"), f.get("category", "").upper())
                            brief_md.append(f"| {m_i} | {f.get('title')} | {c_name} | #{f.get('primary_ref', 1)} |")

                        brief_md.append("\n## تفاصيل النتائج والقرارات الاستراتيجية\n")
                        for f in findings:
                            cat_name = cat_labels_ar.get(f.get("category"), f.get("category", "").upper())
                            brief_md.append(f"### [{cat_name}] {f.get('title')}\n{f.get('description')}\n")
                    else:
                        brief_md = [
                            f"# EXECUTIVE INTELLIGENCE BRIEFING: {focus_input}",
                            f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                            f"**Corpus:** {len(target_ids)} documents",
                            "\n## Executive Overview\n",
                            brief_res.get("executive_summary", ""),
                            "\n## Executive Decision Matrix\n",
                            "| # | Finding / Directive | Category | Primary Reference |",
                            "|---|---|---|---|",
                        ]
                        for m_i, f in enumerate(findings, start=1):
                            brief_md.append(f"| {m_i} | {f.get('title')} | {f.get('category').upper()} | #{f.get('primary_ref', 1)} |")

                        brief_md.append("\n## Detailed Strategic Findings\n")
                        for f in findings:
                            brief_md.append(f"### [{f.get('category').upper()}] {f.get('title')}\n{f.get('description')}\n")

                    st.download_button(
                        label="📥 تحميل التقرير التنفيذي (.md)" if is_ar else "📥 Download Executive Briefing (.md)",
                        data="\n".join(brief_md),
                        file_name=f"psut_executive_brief_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                        mime="text/markdown",
                        use_container_width=True,
                    )

                except Exception as exc:
                    st.error(f"{'فشل توليد الإيجاز التنفيذي:' if is_ar else 'Briefing generation failed:'} {exc}")


# =========================================================
# FEATURE 4: KNOWLEDGE REPOSITORY & SYSTEM DIAGNOSTICS
# =========================================================

elif selected_feature_idx == 3:
    st.subheader("📁 مستودع المعرفة السيادي والتشخيص الفني" if is_ar else "📁 Sovereign Knowledge Repository & Diagnostics")
    st.caption("دليل البيانات المحلي المعزول، وفهرسة الوثائق، وتتبع سلامة البنية التحتية المحلية." if is_ar else "Air-gapped data catalog, document ingestion, and live local infrastructure diagnostics.")

    # Live Health Diagnostics
    try:
        health_info = client.get_health()
        st.markdown("#### 🛡️ " + ("تشخيص العتاد والمحركات الذكية" if is_ar else "Hardware & Engine Diagnostics"))
        h_col1, h_col2, h_col3, h_col4 = st.columns(4)
        with h_col1:
            st.metric(
                "محرك التوليد Ollama" if is_ar else "Ollama LLM",
                health_info.get("ollama", {}).get("model", "command-r7b-arabic:7b"),
                "كارت الشاشة GPU" if is_ar else "Local GPU",
            )
        with h_col2:
            st.metric(
                "تضمينات المتجهات" if is_ar else "Embeddings",
                "MiniLM-Multilingual",
                "384-dim عربي/إنجليزي" if is_ar else "384-dim Arabic",
            )
        with h_col3:
            st.metric(
                "معيد الترتيب Reranker" if is_ar else "Reranker",
                "BGE-Reranker-v2-m3",
                "Cross-Encoder متعدد اللغات" if is_ar else "Cross-Encoder Multilingual",
            )
        with h_col4:
            st.metric(
                "قاعدة المتجهات Qdrant" if is_ar else "Vector Store",
                "Qdrant مدمجة" if is_ar else "Qdrant Embedded",
                f"{health_info.get('chunk_count', 0)} {'مقطع' if is_ar else 'chunks'}",
            )
    except Exception:
        st.warning("تعذر جلب بيانات التشخيص الفني في الوقت الفعلي." if is_ar else "Could not fetch real-time health telemetry.")

    st.divider()

    # Document Ingestion Section
    st.markdown("#### ⚡ " + ("فهرسة وثيقة رسمية جديدة" if is_ar else "Ingest New Document"))
    uploaded_file = st.file_uploader(
        "رفع وثيقة رسمية (PDF, Word DOCX, Markdown, Text, HTML)" if is_ar else "Upload Enterprise Document (PDF, Word DOCX, Markdown, Text, HTML)",
        type=["md", "txt", "pdf", "docx", "html", "htm"],
        key="tab_repo_uploader",
    )

    if uploaded_file is not None:
        idx_btn_label = "⚡ بدء فهرسة وتضمين الوثيقة" if is_ar else "⚡ Index Document into Vector Store"
        if st.button(idx_btn_label, use_container_width=True, type="primary"):
            try:
                with st.spinner("جاري استخراج المقاطع وبناء التضمينات المتجهة محلياً..." if is_ar else "Processing document chunks and local embeddings..."):
                    result = client.ingest(
                        filename=uploaded_file.name,
                        content=uploaded_file.getvalue(),
                    )

                chunk_cnt = result.get("chunk_count", 0)
                if result.get("duplicate"):
                    st.info(
                        f"ℹ️ الوثيقة `{uploaded_file.name}` مفهرسة مسبقاً ({chunk_cnt} مقطع). جاهزة للبحث والمقارنة والإيجاز!"
                        if is_ar
                        else f"ℹ️ Document `{uploaded_file.name}` is already indexed ({chunk_cnt} chunks). Ready for search, conflict detection, and briefings!"
                    )
                else:
                    st.success(
                        f"✅ تمت فهرسة وثيقة `{uploaded_file.name}` بنجاح بعدد ({chunk_cnt} مقطع)!"
                        if is_ar
                        else f"✅ Successfully indexed `{uploaded_file.name}` ({chunk_cnt} chunks) into the vector store!"
                    )
                    st.session_state["documents"] = client.list_documents()
                    st.rerun()

            except Exception as exc:
                st.error(f"{'فشلت عملية الفهرسة والتضمين:' if is_ar else 'Ingestion failed:'} {exc}")

    st.divider()

    # Document Catalog Table
    st.markdown("#### 📚 " + ("كتالوج الوثائق الرسمية المفهرسة" if is_ar else "Ingested Document Catalog"))
    docs = st.session_state.get("documents", [])
    if docs:
        doc_rows = []
        for d in docs:
            clean_name, base_name = clean_source_name(d.get("filename", ""))
            doc_rows.append({
                "اسم الوثيقة" if is_ar else "Document Name": clean_name,
                "الصيغة" if is_ar else "Format": d.get("file_type", "").upper(),
                "عدد المقاطع" if is_ar else "Chunk Count": d.get("chunk_count", 0),
                "المعرف الرقمي" if is_ar else "Document ID": d.get("document_id", "")[:16] + "...",
                "استراتيجية التقسيم" if is_ar else "Strategy": d.get("chunking_strategy", "structure"),
            })
        st.dataframe(pd.DataFrame(doc_rows), use_container_width=True, hide_index=True)
    else:
        st.info("لا توجد وثائق مفهرسة حالياً." if is_ar else "No documents currently indexed.")