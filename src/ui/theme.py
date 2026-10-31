"""Visual theme, layout CSS and shared header markup."""
from __future__ import annotations

import gradio as gr

from src.config import APP_NAME, APP_TAGLINE, DISTRICT, ROLE_BANNER, SIMULATED_BANNER

CSS = """
:root { --bhd-navy:#0b2545; --bhd-teal:#0f766e; --bhd-teal-soft:#ccfbf1; --bhd-ink:#0f172a; }
.gradio-container { max-width: 1500px !important; }
#bhd-header {
  background: linear-gradient(120deg,#0b2545 0%,#10395f 55%,#0f766e 100%);
  color:#fff; border-radius:16px; padding:22px 26px; margin-bottom:14px;
}
#bhd-header .brand { font-size:26px; font-weight:750; letter-spacing:.2px; }
#bhd-header .tag { opacity:.92; margin-top:4px; font-size:14px; }
#bhd-header .meta { margin-top:10px; font-size:12px; opacity:.8; }
.bhd-banner {
  border-radius:10px; padding:9px 13px; font-size:12.5px; font-weight:600;
  background:#fef3c7; color:#78350f; border:1px solid #fcd34d; margin-bottom:8px;
}
.bhd-role { background:#e0f2fe; color:#075985; border:1px solid #7dd3fc; }
.bhd-kpi-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(165px,1fr)); gap:12px; margin:6px 0 14px; }
.bhd-kpi { background:#fff; border:1px solid #e2e8f0; border-left:5px solid var(--bhd-teal);
  border-radius:12px; padding:13px 15px; box-shadow:0 1px 2px rgba(15,23,42,.05); }
.bhd-kpi .v { font-size:26px; font-weight:750; color:var(--bhd-navy); line-height:1.1; }
.bhd-kpi .l { font-size:11.5px; text-transform:uppercase; letter-spacing:.45px; color:#64748b; margin-top:3px; }
.bhd-kpi.alert { border-left-color:#dc2626; }
.bhd-kpi.warn { border-left-color:#d97706; }
.bhd-section { font-size:15px; font-weight:700; color:var(--bhd-navy); margin:8px 0 2px; }
.bhd-note { font-size:12px; color:#475569; background:#f8fafc; border:1px dashed #cbd5e1;
  border-radius:10px; padding:9px 12px; margin:6px 0; }
.bhd-emergency { background:#fef2f2; border:1px solid #fca5a5; color:#991b1b;
  border-radius:10px; padding:11px 14px; font-weight:600; margin:8px 0 12px; }
.bhd-alert-row { display:flex; gap:10px; align-items:flex-start; padding:8px 10px;
  border-bottom:1px solid #eef2f7; font-size:13px; }
.bhd-pill { font-size:10.5px; font-weight:700; padding:2px 8px; border-radius:999px; white-space:nowrap; }
.bhd-pill.High { background:#fee2e2; color:#991b1b; }
.bhd-pill.Medium { background:#fef3c7; color:#92400e; }
.bhd-pill.Info { background:#e0f2fe; color:#075985; }
#bhd-nav label { font-size:13px; }
#bhd-nav .wrap { display:flex; flex-direction:column; gap:2px; max-height:70vh; overflow-y:auto; }
#bhd-nav label { border-radius:9px; padding:4px 8px; }
.bhd-detail { background:#fff; border:1px solid #e2e8f0; border-radius:12px; padding:14px 16px;
  font-size:13px; line-height:1.62; color:#334155; }
.bhd-detail .t { font-size:16px; font-weight:750; color:var(--bhd-navy); margin-bottom:6px; }
.bhd-detail .f { margin-top:8px; color:#92400e; font-size:12px; }
.bhd-status { display:inline-block; background:#e0f2fe; color:#075985; border:1px solid #7dd3fc;
  border-radius:999px; padding:1px 8px; font-size:11px; font-weight:650; }
.bhd-chip { display:inline-block; background:#f1f5f9; color:#334155; border:1px solid #e2e8f0;
  border-radius:999px; padding:2px 9px; margin:2px 4px 2px 0; font-size:11.5px; }
footer { display:none !important; }
"""


def header_html() -> str:
    return f"""
    <div id="bhd-header">
      <div class="brand">{APP_NAME}</div>
      <div class="tag">{APP_TAGLINE}</div>
      <div class="meta">Enterprise healthcare operations workspace &nbsp;·&nbsp; Demo geography: {DISTRICT} &nbsp;·&nbsp; Citizens use the dedicated Citizen Portal</div>
    </div>
    <div class="bhd-banner">{SIMULATED_BANNER}</div>
    """


def role_banner_html(role: str) -> str:
    return (
        f'<div class="bhd-banner bhd-role">{ROLE_BANNER} &nbsp;|&nbsp; Acting as: '
        f"<b>{role}</b>. Role switching is a demonstration control only.</div>"
    )


def gradio_theme() -> gr.Theme:
    return gr.themes.Soft(
        primary_hue="teal",
        secondary_hue="blue",
        neutral_hue="slate",
        radius_size=gr.themes.sizes.radius_md,
        font=["Inter", "system-ui", "sans-serif"],
    ).set(
        button_primary_background_fill="#0f766e",
        button_primary_background_fill_hover="#0d5f59",
        block_title_text_weight="600",
    )
