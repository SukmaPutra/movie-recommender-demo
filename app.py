"""Demo sidang: rekomendasi film FunkSVD dengan penjelasan post-hoc."""

from __future__ import annotations

import html
from pathlib import Path

import pandas as pd
import streamlit as st

DATA_PATH = Path(__file__).resolve().parent / "data" / "demo_data.csv"
REQUIRED_COLUMNS = [
    "UserID",
    "Peringkat",
    "Judul",
    "Evidence",
    "Penjelasan",
    "Genre",
    "SkorPrediksi",
]
ORIGINAL_COLUMNS = ["UserID", "Peringkat", "Judul", "Evidence", "Penjelasan"]
EVIDENCE_ORDER = [
    "Genre Preference",
    "Genre Frequency",
    "Item Quality",
    "Recent Preference",
    "Fallback generik",
]
EXPECTED_ROWS = 59810
EXPECTED_USERS = 5981

FIDELITY_ROWS = [
    {"Komponen": "Genre Preference", "Mentah": -0.040, "Centered": -0.041, "n": 58676},
    {"Komponen": "Genre Frequency", "Mentah": -0.087, "Centered": 0.058, "n": 59810},
    {"Komponen": "Recent Preference", "Mentah": 0.228, "Centered": 0.037, "n": 59810},
    {"Komponen": "Rating rata-rata film", "Mentah": 0.102, "Centered": 0.308, "n": 59810},
    {"Komponen": "Popularitas film", "Mentah": -0.004, "Centered": -0.041, "n": 59810},
    {"Komponen": "Latent Similarity", "Mentah": 0.005, "Centered": -0.061, "n": 59810},
]
RANKING_ROWS = [
    {"Metrik": "Precision@10", "Model": 0.0357, "Acak": 0.0053},
    {"Metrik": "Recall@10", "Model": 0.0228, "Acak": 0.0028},
    {"Metrik": "NDCG@10", "Model": 0.0393, "Acak": None},
    {"Metrik": "HR@10", "Model": 0.2312, "Acak": 0.0505},
]

# ---------------------------------------------------------------------------
# Token desain (tema terang). Tiga lapis:
#   PRIMITIVE : nilai mentah. Satu-satunya tempat hex.
#   SEMANTIC  : peran warna yang dipakai komponen.
#   Komponen  : kelas .re-* di CSS_COMPONENTS, hanya membaca variabel semantic.
# Font stack memakai font desain bila tersedia, lalu jatuh ke font sistem.
# ---------------------------------------------------------------------------
PRIMITIVE = {
    "paper": "#FAF8F4",
    "white": "#FFFFFF",
    "sand": "#F3EFE8",
    "sand-line": "#D9D3C7",
    "stone-line": "#8F887A",
    "ink-900": "#1D1B18",
    "ink-700": "#504B44",
    "ink-500": "#6B655B",
    "terracotta-600": "#A8452A",
    "terracotta-100": "#F4E4DD",
}
SEMANTIC = {
    "bg": "paper",
    "bg-raised": "white",
    "bg-sunken": "sand",
    "text": "ink-900",
    "text-2": "ink-700",
    "text-muted": "ink-500",
    "line": "sand-line",
    "line-strong": "stone-line",
    "accent": "terracotta-600",
    "accent-soft": "terracotta-100",
}
FONT_SERIF = '"Source Serif 4", Georgia, "Times New Roman", serif'
FONT_SANS = '"IBM Plex Sans", "Segoe UI", system-ui, sans-serif'
FONT_MONO = '"IBM Plex Mono", ui-monospace, Consolas, monospace'
TYPE_SCALE = {
    "caption": "0.8125rem",
    "small": "0.875rem",
    "body": "1rem",
    "lead": "1.125rem",
    "h4": "1.125rem",
    "h3": "1.5rem",
    "title": "2.5rem",
    "figure": "2.5rem",
}
SPACE = {"1": "0.25rem", "2": "0.5rem", "3": "0.75rem", "4": "1rem", "6": "1.5rem", "8": "2rem", "12": "3rem"}
EVIDENCE_SHAPE = {
    "Genre Preference": "pref",
    "Genre Frequency": "freq",
    "Item Quality": "qual",
    "Recent Preference": "recent",
    "Fallback generik": "fallback",
}
CSS_COMPONENTS = """
.stApp { background: var(--bg); color: var(--text); font-family: var(--font-sans); }
.stApp [data-testid="stMarkdownContainer"] p,
.stApp [data-testid="stMarkdownContainer"] li { line-height: 1.65; }
.stApp h1, .stApp h2, .stApp h3, .stApp h4 {
  font-family: var(--font-serif); font-weight: 500; color: var(--text); letter-spacing: -0.005em;
}
.stApp h3 { font-size: var(--fs-h3) !important; }
.stApp h4 { font-size: var(--fs-h4) !important; margin-top: var(--sp-6); }
.stApp [data-testid="stCaptionContainer"],
.stApp [data-testid="stCaptionContainer"] * { color: var(--text-muted) !important; opacity: 1 !important; }
.block-container { max-width: 1080px; padding-top: var(--sp-8); padding-bottom: var(--sp-12); }
[data-testid="stSidebar"] { background: var(--bg-sunken); border-right: 1px solid var(--line); }
[data-testid="stSidebar"][aria-expanded="true"] { width: 16rem !important; }

.stApp button, .stApp input, .stApp textarea { font-family: var(--font-sans); }
.stApp input, .stApp textarea, .stApp [data-baseweb="select"] > div {
  border-color: var(--line-strong) !important; background: var(--bg-raised) !important;
}
.stApp [data-testid="stBaseButton-secondary"] {
  background: transparent; border: 1px solid var(--line-strong); color: var(--text);
}
.stApp [data-testid="stBaseButton-secondary"]:hover { border-color: var(--accent); color: var(--accent); }
.stApp [data-baseweb="tag"],
.stApp [data-testid="stMultiSelectTagsContainer"] > span > span { background: var(--accent-soft) !important; }
.stApp [data-baseweb="tag"], .stApp [data-baseweb="tag"] span,
.stApp [data-testid="stMultiSelectTagsContainer"] > span > span,
.stApp [data-testid="stMultiSelectTagsContainer"] > span > span * { color: var(--accent) !important; }
.stApp a { color: var(--accent); }
.stApp :focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }

.re-serif { font-family: var(--font-serif); }
.re-num { font-family: var(--font-sans); font-weight: 500; font-variant-numeric: tabular-nums lining-nums; letter-spacing: -0.01em; }
.re-muted { color: var(--text-muted); }

.re-mark {
  display: inline-block; width: 0.62em; height: 0.62em; margin-right: 0.5em;
  background: var(--accent); vertical-align: 0.02em; flex: none;
}
.re-mark--pref { border-radius: 50%; }
.re-mark--freq { transform: rotate(45deg) scale(0.82); }
.re-mark--qual { clip-path: polygon(50% 0, 100% 100%, 0 100%); }
.re-mark--fallback { background: none; border: 1.5px solid var(--text-muted); border-radius: 50%; box-sizing: border-box; }

.re-kicker { font-size: var(--fs-small); color: var(--text-muted); margin: 0 0 var(--sp-2); }
.re-title { font-family: var(--font-serif); font-weight: 500; font-size: var(--fs-title); line-height: 1.1; margin: 0 0 var(--sp-3); }
.re-lead { font-size: var(--fs-lead); color: var(--text-2); max-width: 42rem; line-height: 1.65; margin: 0; }
.re-finding {
  display: flex; align-items: baseline; gap: var(--sp-4); flex-wrap: wrap;
  border-top: 1px solid var(--line-strong); padding-top: var(--sp-4); margin: var(--sp-6) 0 var(--sp-4);
}
.re-big { font-size: var(--fs-figure); line-height: 1; color: var(--text); }
.re-finding-text { color: var(--text-2); max-width: 32rem; }
.re-figs { display: flex; flex-wrap: wrap; row-gap: var(--sp-4); margin: var(--sp-4) 0 var(--sp-6); }
.re-fig { padding: 0 var(--sp-8) 0 var(--sp-6); border-left: 1px solid var(--line-strong); }
.re-fig:first-child { padding-left: 0; border-left: 0; }
.re-val { font-size: 1.75rem; line-height: 1.2; color: var(--text); }
.re-lab { font-size: var(--fs-caption); color: var(--text-muted); }

.re-profile { display: flex; align-items: center; gap: var(--sp-4); flex-wrap: wrap; color: var(--text-2); margin: var(--sp-4) 0 var(--sp-2); }
.re-strip { display: inline-flex; gap: 3px; }
.re-cell {
  width: 1.5rem; height: 1.5rem; border: 1px solid var(--line-strong); border-radius: 3px;
  display: inline-flex; align-items: center; justify-content: center; background: var(--bg-raised);
}
.re-cell .re-mark { margin: 0; }

.re-list { border-top: 1px solid var(--line-strong); margin-top: var(--sp-2); }
.re-item {
  display: grid; grid-template-columns: 2.75rem minmax(0, 1fr) 11rem; gap: var(--sp-4);
  padding: var(--sp-4) 0; border-bottom: 1px solid var(--line);
}
.re-rank { font-size: 1.9rem; line-height: 1; color: var(--text); }
.re-movie { font-family: var(--font-serif); font-size: var(--fs-lead); line-height: 1.3; color: var(--text); }
.re-genre { font-size: var(--fs-caption); color: var(--text-muted); margin: 2px 0 var(--sp-2); }
.re-why { color: var(--text); line-height: 1.65; margin: 0; }
.re-u-main, .re-u-latent {
  text-decoration-line: underline; text-decoration-thickness: 1.5px;
  text-decoration-color: var(--accent); text-underline-offset: 3px;
}
.re-u-latent { text-decoration-style: dashed; }
.re-meta {
  display: flex; flex-direction: column; align-items: flex-end; gap: var(--sp-1);
  text-align: right; font-size: var(--fs-caption); color: var(--text-2);
}
.re-score { color: var(--text-muted); }
.re-legend { font-size: var(--fs-caption); color: var(--text-muted); margin-top: var(--sp-2); }

.re-flow { display: flex; flex-wrap: wrap; gap: var(--sp-1) 0.375rem; align-items: center; margin: var(--sp-4) 0 var(--sp-6); }
.re-flow span {
  border: 1px solid var(--line-strong); border-radius: 6px; padding: 0.35rem 0.55rem;
  font-size: var(--fs-caption); background: var(--bg-raised); white-space: nowrap;
}
.re-flow i { color: var(--text-muted); font-style: normal; }
.re-ladder { border-top: 1px solid var(--line-strong); margin-bottom: var(--sp-4); }
.re-step {
  display: grid; grid-template-columns: 2rem 12.5rem minmax(0, 1fr); gap: var(--sp-3);
  padding: var(--sp-3) 0; border-bottom: 1px solid var(--line); align-items: baseline;
}
.re-n { font-family: var(--font-serif); font-size: var(--fs-h4); color: var(--text); }
.re-example { border-top: 1px solid var(--line-strong); padding-top: var(--sp-4); margin-top: var(--sp-2); line-height: 1.7; }

.re-bars {
  display: grid; grid-template-columns: minmax(9.5rem, max-content) minmax(0, 1fr) auto;
  gap: var(--sp-3) var(--sp-3); align-items: center; font-size: var(--fs-small); margin-bottom: var(--sp-4);
}
.re-bar { display: block; height: 0.625rem; background: var(--bg-sunken); border-radius: 2px; position: relative; }
.re-fill { display: block; position: absolute; left: 0; top: 0; bottom: 0; background: var(--accent); border-radius: 2px; }
.re-bar--muted .re-fill { background: var(--text-muted); }
.re-pair { display: grid; gap: 4px; }
.re-vals { text-align: right; color: var(--text-2); white-space: nowrap; }
.re-keys { display: flex; gap: var(--sp-4); font-size: var(--fs-caption); color: var(--text-2); margin: var(--sp-2) 0; }
.re-sw { display: inline-block; width: 0.7rem; height: 0.7rem; margin-right: 0.4rem; vertical-align: -0.05rem; border-radius: 2px; background: var(--accent); }
.re-sw--muted { background: var(--text-muted); }
.re-sw--raw { background: none; border: 2px solid var(--accent); border-radius: 50%; box-sizing: border-box; }
.re-sw--cen { border-radius: 50%; }

.re-dots {
  display: grid; grid-template-columns: minmax(9.5rem, max-content) minmax(0, 1fr) auto;
  gap: 0 var(--sp-3); align-items: center; font-size: var(--fs-small); margin-bottom: var(--sp-4);
}
.re-dots > * { padding: var(--sp-2) 0; border-top: 1px solid var(--line); }
.re-track { position: relative; height: 1.25rem; }
.re-track::before { content: ""; position: absolute; left: 0; right: 0; top: 50%; border-top: 1px solid var(--line-strong); }
.re-zero { position: absolute; top: 0; bottom: 0; width: 0; border-left: 1px solid var(--text-2); }
.re-dot { position: absolute; top: 50%; border-radius: 50%; box-sizing: border-box; }
.re-dot--raw { width: 1rem; height: 1rem; margin: -0.5rem 0 0 -0.5rem; border: 2px solid var(--accent); }
.re-dot--cen { width: 0.6rem; height: 0.6rem; margin: -0.3rem 0 0 -0.3rem; background: var(--accent); }
.re-axis { position: relative; height: 1.1rem; font-size: var(--fs-caption); color: var(--text-muted); }
.re-axis span { position: absolute; top: 0; transform: translateX(-50%); }

@media (max-width: 760px) {
  .re-item { grid-template-columns: 2.25rem minmax(0, 1fr); }
  .re-meta { grid-column: 2; align-items: flex-start; text-align: left; }
  .re-step { grid-template-columns: 1.5rem minmax(0, 1fr); }
  .re-step > :nth-child(3) { grid-column: 2; }
  .re-bars, .re-dots { grid-template-columns: minmax(0, 1fr) auto; }
  .re-bars > :nth-child(3n + 1), .re-dots > :nth-child(3n + 1) { grid-column: 1; }
  .re-bars > :nth-child(3n + 2), .re-dots > :nth-child(3n + 2) { grid-column: 1 / -1; }
  .re-bars > :nth-child(3n + 3), .re-dots > :nth-child(3n + 3) { grid-column: 2; }
  .re-fig { padding: 0 var(--sp-4); }
}
"""


def _root_vars() -> str:
    lines = [f"--p-{name}: {value};" for name, value in PRIMITIVE.items()]
    lines += [f"--{role}: var(--p-{prim});" for role, prim in SEMANTIC.items()]
    lines += [f"--font-serif: {FONT_SERIF};", f"--font-sans: {FONT_SANS};", f"--font-mono: {FONT_MONO};"]
    lines += [f"--fs-{name}: {value};" for name, value in TYPE_SCALE.items()]
    lines += [f"--sp-{name}: {value};" for name, value in SPACE.items()]
    return "\n  ".join(lines)


def inject_css() -> None:
    css = f":root {{\n  {_root_vars()}\n}}\n{CSS_COMPONENTS}"
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Pemformatan angka gaya Indonesia
# ---------------------------------------------------------------------------
def fmt_int(value: int | float) -> str:
    return f"{int(value):,}".replace(",", ".")


def fmt_dec(value: float, digits: int) -> str:
    return f"{value:.{digits}f}".replace(".", ",")


def fmt_signed(value: float, digits: int = 3) -> str:
    return f"{value:+.{digits}f}".replace("-", "−").replace(".", ",")


def fmt_pct(value: float) -> str:
    return f"{value * 100:.2f}%".replace(".", ",")


@st.cache_data
def load_demo() -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset tidak ditemukan: {DATA_PATH}")
    frame = pd.read_csv(DATA_PATH)
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Kolom hilang: {', '.join(missing)}")
    if len(frame) != EXPECTED_ROWS:
        raise ValueError(f"Jumlah baris {len(frame):,}, diharapkan {EXPECTED_ROWS:,}.")
    if frame["UserID"].nunique() != EXPECTED_USERS:
        raise ValueError("Jumlah pengguna tidak sesuai hasil penelitian (5.981).")
    sizes = frame.groupby("UserID").size()
    if not (sizes == 10).all():
        raise ValueError("Ada pengguna yang tidak memiliki tepat 10 rekomendasi.")
    if sorted(frame["Peringkat"].unique()) != list(range(1, 11)):
        raise ValueError("Peringkat harus bernilai 1 sampai 10.")
    if frame[ORIGINAL_COLUMNS].isna().any().any():
        raise ValueError("Ada nilai kosong pada kolom asli rekomendasi.")
    unknown = sorted(set(frame["Evidence"]) - set(EVIDENCE_ORDER))
    if unknown:
        raise ValueError(f"Kategori evidence tidak dikenal: {unknown}")
    return frame.sort_values(["UserID", "Peringkat"]).reset_index(drop=True)


def example_user_id(frame: pd.DataFrame) -> int:
    variety = frame.groupby("UserID")["Evidence"].nunique()
    return int(variety[variety == variety.max()].index.min())


def format_genre(value: object) -> str:
    if pd.isna(value) or str(value).strip() == "":
        return "Genre tidak tersedia"
    return str(value).replace("|", " · ")


def format_score(value: object) -> str | None:
    if pd.isna(value):
        return None
    return f"{float(value):.2f}"


# ---------------------------------------------------------------------------
# Komponen tampilan (HTML tanpa indentasi agar tidak dibaca sebagai blok kode)
# ---------------------------------------------------------------------------
def evidence_label(evidence: str) -> str:
    shape = EVIDENCE_SHAPE.get(evidence, "fallback")
    return f'<span class="re-mark re-mark--{shape}" aria-hidden="true"></span>{html.escape(evidence)}'


def _sentence_end(text: str, start: int) -> int:
    """Indeks titik akhir kalimat, mengabaikan titik di dalam tanda kutip."""
    in_quote = False
    for index in range(start, len(text)):
        char = text[index]
        if char == '"':
            in_quote = not in_quote
        elif char == "." and not in_quote and (index + 1 == len(text) or text[index + 1] == " "):
            return index
    return len(text)


def explanation_html(text: object) -> str:
    """Escape kalimat penjelasan dan garis bawahi evidence utama serta klausa latent.

    Teks tidak diubah. Bila format kalimat tidak dikenali, teks tampil polos."""
    raw = str(text)
    prefix = "Direkomendasikan karena "
    latent_at = raw.find("mirip dengan")
    spans: list[tuple[int, int, str]] = []
    if raw.startswith(prefix):
        main_end = _sentence_end(raw, len(prefix))
        if 0 <= latent_at < main_end:
            main_end = latent_at
        while main_end > len(prefix) and raw[main_end - 1] in " ,":
            main_end -= 1
        spans.append((len(prefix), main_end, "re-u-main"))
    if latent_at != -1:
        spans.append((latent_at, _sentence_end(raw, latent_at), "re-u-latent"))
    spans.sort()
    if any(spans[i][1] > spans[i + 1][0] for i in range(len(spans) - 1)):
        return html.escape(raw)
    parts, cursor = [], 0
    for start, end, css_class in spans:
        parts.append(html.escape(raw[cursor:start]))
        parts.append(f'<span class="{css_class}">{html.escape(raw[start:end])}</span>')
        cursor = end
    parts.append(html.escape(raw[cursor:]))
    return "".join(parts)


def figures_html(items: list[tuple[str, str]]) -> str:
    cells = "".join(
        f'<div class="re-fig"><div class="re-num re-val">{html.escape(value)}</div>'
        f'<div class="re-lab">{html.escape(label)}</div></div>'
        for label, value in items
    )
    return f'<div class="re-figs">{cells}</div>'


def evidence_counts(frame: pd.DataFrame) -> pd.Series:
    return frame["Evidence"].value_counts().reindex(EVIDENCE_ORDER).fillna(0).astype(int)


def evidence_bars_html(counts: pd.Series) -> str:
    total = int(counts.sum()) or 1
    top = int(counts.max()) or 1
    rows = []
    for name, count in counts.items():
        width = count / top * 100
        muted = " re-bar--muted" if name == "Fallback generik" else ""
        rows.append(
            f"<span>{evidence_label(name)}</span>"
            f'<span class="re-bar{muted}"><span class="re-fill" style="width:{width:.1f}%"></span></span>'
            f'<span class="re-vals re-num">{fmt_int(count)} · {fmt_dec(count / total * 100, 2)}%</span>'
        )
    return f'<div class="re-bars">{"".join(rows)}</div>'


def ranking_bars_html() -> str:
    rows = []
    for item in RANKING_ROWS:
        model, random = item["Model"], item["Acak"]
        scale = max(model, random or 0) or 1
        model_bar = f'<span class="re-bar"><span class="re-fill" style="width:{model / scale * 100:.1f}%"></span></span>'
        if random is None:
            random_bar = ""
            values = f"{fmt_dec(model, 4)}<br>—"
        else:
            random_bar = (
                f'<span class="re-bar re-bar--muted"><span class="re-fill" style="width:{random / scale * 100:.1f}%">'
                "</span></span>"
            )
            values = f"{fmt_dec(model, 4)}<br>{fmt_dec(random, 4)}"
        rows.append(
            f"<span>{html.escape(item['Metrik'])}</span>"
            f'<span class="re-pair">{model_bar}{random_bar}</span>'
            f'<span class="re-vals re-num">{values}</span>'
        )
    keys = (
        '<div class="re-keys"><span><span class="re-sw"></span>Model</span>'
        '<span><span class="re-sw re-sw--muted"></span>Acak</span></div>'
    )
    return f'{keys}<div class="re-bars">{"".join(rows)}</div>'


def fidelity_dots_html() -> str:
    values = [row[key] for row in FIDELITY_ROWS for key in ("Mentah", "Centered")]
    step = 0.05
    low = -(int((-(min(values) - 0.02)) / step) + 1) * step if min(values) - 0.02 < 0 else 0.0
    high = (int((max(values) + 0.02) / step) + 1) * step
    span = high - low

    def pos(value: float) -> float:
        return (value - low) / span * 100

    rows = []
    for row in FIDELITY_ROWS:
        raw, centered = row["Mentah"], row["Centered"]
        rows.append(
            f'<span>{html.escape(row["Komponen"])}</span>'
            f'<span class="re-track"><span class="re-zero" style="left:{pos(0):.1f}%"></span>'
            f'<span class="re-dot re-dot--cen" style="left:{pos(centered):.1f}%"></span>'
            f'<span class="re-dot re-dot--raw" style="left:{pos(raw):.1f}%"></span></span>'
            f'<span class="re-vals re-num">{fmt_signed(raw)} · {fmt_signed(centered)}'
            f'<br><span class="re-muted">n {fmt_int(row["n"])}</span></span>'
        )
    axis = (
        "<span></span>"
        f'<span class="re-axis"><span style="left:0;transform:none">{fmt_signed(low, 2)}</span>'
        f'<span style="left:{pos(0):.1f}%">0</span>'
        f'<span style="left:100%;transform:translateX(-100%)">{fmt_signed(high, 2)}</span></span>'
        "<span></span>"
    )
    keys = (
        '<div class="re-keys"><span><span class="re-sw re-sw--raw"></span>Mentah</span>'
        '<span><span class="re-sw re-sw--cen"></span>Centered</span></div>'
    )
    return f'{keys}<div class="re-dots">{"".join(rows)}{axis}</div>'


def page_home(frame: pd.DataFrame) -> None:
    hr = next(row for row in RANKING_ROWS if row["Metrik"] == "HR@10")
    st.markdown(
        '<div class="re-kicker">Demo skripsi · MovieLens 1M</div>'
        '<h1 class="re-title">ReelExplain</h1>'
        '<p class="re-lead">Sistem rekomendasi film collaborative filtering berbasis FunkSVD, '
        "dilengkapi penjelasan post-hoc berbasis aturan. Peringkat film berasal dari model. "
        "Penjelasan disusun setelah rekomendasi terbentuk dan tidak mengubah urutan tersebut.</p>"
        '<div class="re-finding">'
        f'<span class="re-num re-big">{fmt_pct(hr["Model"])}</span>'
        '<span class="re-finding-text">HR@10: pengguna yang mendapat sekurang-kurangnya satu film relevan. '
        f'Pemeringkatan acak: {fmt_pct(hr["Acak"])}.</span></div>',
        unsafe_allow_html=True,
    )
    coverage = (frame["Evidence"] != "Fallback generik").mean() * 100
    st.markdown(
        figures_html(
            [
                ("Pengguna", fmt_int(frame["UserID"].nunique())),
                ("Rekomendasi", fmt_int(len(frame))),
                ("Kategori evidence", str(frame["Evidence"].nunique())),
                ("Evidence non-fallback", f"{coverage:.2f}%".replace(".", ",")),
            ]
        ),
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.15, 0.85])
    with left:
        st.subheader("Dataset dan model")
        st.markdown(
            """
            - MovieLens 1M, explicit feedback, skala rating 1–5.
            - Temporal split per pengguna: train 70%, validation 10%, test 20%.
            - Model final Surprise SVD: 150 faktor, 20 epoch, learning rate 0,02, regularisasi 0,08.
            - Model dilatih pada data train + validation.
            - Top-10 memakai protokol Full Unseen: film yang belum dinilai pengguna pada data latih.
            """
        )
    with right:
        st.subheader("Distribusi evidence")
        st.markdown(evidence_bars_html(evidence_counts(frame)), unsafe_allow_html=True)
        st.caption("Dihitung dari 59.810 rekomendasi hasil eksperimen. Sama dengan Tabel 4.18.")


def page_recommendations(frame: pd.DataFrame, example_id: int) -> None:
    st.subheader("Rekomendasi personal")
    st.caption("Pilih UserID dari hasil eksperimen. Tiap pengguna memiliki 10 film.")

    user_ids = frame["UserID"].drop_duplicates().tolist()
    if "user_id" not in st.session_state:
        st.session_state.user_id = example_id

    pick, action = st.columns([3, 1.4])
    with action:
        st.write("")
        st.write("")
        if st.button("Contoh ragam evidence", use_container_width=True):
            st.session_state.user_id = example_id
            st.rerun()
    with pick:
        user_id = st.selectbox("UserID", user_ids, key="user_id")

    user_df = frame[frame["UserID"] == user_id].sort_values("Peringkat")
    if user_df.empty:
        st.error(f"UserID {user_id} tidak ditemukan dalam hasil eksperimen.")
        return

    variety = user_df["Evidence"].value_counts().reindex(EVIDENCE_ORDER, fill_value=0)
    strip_cells = "".join(
        f'<span class="re-cell" title="#{int(row.Peringkat)} {html.escape(row.Evidence)}">'
        f'<span class="re-mark re-mark--{EVIDENCE_SHAPE[row.Evidence]}"></span></span>'
        for row in user_df.itertuples()
    )
    strip_label = ", ".join(f"{int(row.Peringkat)} {row.Evidence}" for row in user_df.itertuples())
    st.markdown(
        '<div class="re-profile">'
        f"<span>UserID {int(user_id)} · {len(user_df)} film · {int((variety > 0).sum())} jenis evidence</span>"
        f'<span class="re-strip" role="img" aria-label="Evidence per peringkat: {html.escape(strip_label)}">'
        f"{strip_cells}</span></div>",
        unsafe_allow_html=True,
    )
    st.caption("Tidak ada nama, usia, atau jenis kelamin. Profil hanya merangkum evidence pada Top-10 pengguna ini.")

    search_col, filter_col = st.columns([1.2, 1.4])
    with search_col:
        query = st.text_input("Cari judul pada Top-10", placeholder="Ketik sebagian judul")
    with filter_col:
        selected = st.multiselect(
            "Filter evidence",
            EVIDENCE_ORDER,
            default=EVIDENCE_ORDER,
        )

    shown = user_df[user_df["Evidence"].isin(selected)]
    if query.strip():
        shown = shown[shown["Judul"].str.contains(query.strip(), case=False, na=False, regex=False)]
    st.markdown(f"#### Katalog · {len(shown)} dari {len(user_df)} film")
    if shown.empty:
        st.info("Tidak ada film yang cocok dengan pencarian atau filter pada pengguna ini.")
    else:
        items = []
        for _, row in shown.iterrows():
            score = format_score(row["SkorPrediksi"])
            score_html = (
                f'<span class="re-score">Skor prediksi model <span class="re-num">{score.replace(".", ",")}</span></span>'
                if score
                else ""
            )
            items.append(
                '<div class="re-item">'
                f'<div class="re-rank re-serif">{int(row["Peringkat"])}</div>'
                f'<div><div class="re-movie">{html.escape(str(row["Judul"]))}</div>'
                f'<div class="re-genre">{html.escape(format_genre(row["Genre"]))}</div>'
                f'<p class="re-why">{explanation_html(row["Penjelasan"])}</p></div>'
                f'<div class="re-meta"><span>{evidence_label(row["Evidence"])}</span>{score_html}</div>'
                "</div>"
            )
        st.markdown(f'<div class="re-list">{"".join(items)}</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="re-legend">Garis solid: evidence utama. Garis putus-putus: klausa kemiripan laten. '
            "Penjelasan disusun secara post-hoc berbasis aturan dari hasil eksperimen.</div>",
            unsafe_allow_html=True,
        )


def page_how() -> None:
    st.subheader("Cara kerja penjelasan")
    st.markdown(
        """
        Penjelasan bersifat post-hoc. Model SVD terlebih dahulu menghasilkan Top-10.
        Modul aturan kemudian memilih satu evidence utama dan, bila memenuhi syarat,
        menambahkan klausa kemiripan laten. Urutan film tidak berubah.
        """
    )
    st.markdown(
        '<div class="re-flow">'
        "<span>Riwayat pengguna</span><i>›</i>"
        "<span>Ekstraksi evidence</span><i>›</i>"
        "<span>Evaluasi threshold</span><i>›</i>"
        "<span>Pemilihan aturan prioritas</span><i>›</i>"
        "<span>Kalimat penjelasan</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    rules = [
        (
            "Genre Preference",
            "Skor preferensi genre pengguna paling tinggi pada film tersebut mencapai sekurang-kurangnya 0,285714.",
        ),
        (
            "Genre Frequency",
            "Pengguna sudah memberi rating pada genre itu sekurang-kurangnya 19 kali.",
        ),
        (
            "Item Quality",
            "Rata-rata rating film sekurang-kurangnya 3,7593 dan popularitasnya sekurang-kurangnya 269,5.",
        ),
        (
            "Recent Preference",
            "Sekurang-kurangnya satu rating relevan pada 10 rating terakhir pengguna terkait film ini.",
        ),
        (
            "Fallback generik",
            "Dipakai bila tidak ada aturan di atas yang terpenuhi.",
        ),
    ]
    st.markdown("#### Lima kategori evidence")
    steps = "".join(
        f'<div class="re-step"><span class="re-n">{number}</span>'
        f"<span>{evidence_label(name)}</span><span>{html.escape(text)}</span></div>"
        for number, (name, text) in enumerate(rules, start=1)
    )
    st.markdown(f'<div class="re-ladder">{steps}</div>', unsafe_allow_html=True)
    st.markdown(
        """
        **Urutan prioritas:** Genre Preference > Genre Frequency > Item Quality > Recent Preference > Fallback generik.

        **Latent Similarity** adalah klausa tambahan, bukan kategori yang mengganti evidence utama.
        Klausa ditambahkan bila cosine similarity faktor laten item sekurang-kurangnya 0,5
        terhadap film yang pernah disukai pengguna. Pada hasil eksperimen, klausa ini menyertai 44,58% rekomendasi.
        """
    )
    st.markdown("#### Contoh kalimat dari dataset")
    example = (
        'Direkomendasikan karena Anda sering menilai film bergenre Drama. '
        'Film ini juga mirip dengan "Schindler\'s List (1993)" yang pernah Anda sukai.'
    )
    st.markdown(
        f'<div class="re-example">{explanation_html(example)}'
        '<div class="re-legend">Garis solid: evidence utama. Garis putus-putus: klausa latent.</div></div>',
        unsafe_allow_html=True,
    )
    st.caption("Contoh untuk pengguna 1, peringkat 1: Shawshank Redemption, The (1994), evidence Genre Frequency.")


def page_evaluation(frame: pd.DataFrame) -> None:
    st.subheader("Evaluasi model")
    st.caption("Angka berikut disalin dari output notebook eksperimen pada protokol Full Unseen.")

    st.markdown("#### Prediksi rating")
    st.markdown(figures_html([("RMSE uji", "0,8731"), ("MAE uji", "0,6867")]), unsafe_allow_html=True)
    st.caption("RMSE mengukur rata-rata simpangan kuadrat prediksi terhadap rating uji. MAE mengukur rata-rata selisih absolutnya. Keduanya pada skala rating 1–5.")

    st.markdown("#### Pemeringkatan Full Unseen")
    st.markdown(ranking_bars_html(), unsafe_allow_html=True)
    st.caption(
        "Precision@10 adalah proporsi film relevan di dalam 10 rekomendasi. "
        "Recall@10 adalah proporsi film uji yang relevan dan berhasil masuk Top-10. "
        "NDCG@10 memperhitungkan posisi film relevan. "
        "HR@10 adalah proporsi pengguna yang mendapat sekurang-kurangnya satu film relevan. "
        "Kolom acak adalah ekspektasi pemeringkatan acak pada kandidat Full Unseen. "
        "Nilainya kecil karena kandidat per pengguna sangat banyak, rata-rata sekitar 3.535 film."
    )
    st.caption("Panjang bar dinormalkan per metrik: bar terpanjang pada tiap baris adalah nilai terbesar metrik itu.")

    st.markdown("#### Explainability")
    st.markdown(
        figures_html([("Coverage non-fallback", "94,58%"), ("Rekomendasi dengan klausa latent", "44,58%")]),
        unsafe_allow_html=True,
    )
    st.markdown(evidence_bars_html(evidence_counts(frame)), unsafe_allow_html=True)
    st.caption("Coverage 94,58% berarti 5,42% rekomendasi memakai Fallback generik. Distribusi di atas dihitung dari CSV dan sesuai Tabel 4.18.")

    st.markdown("#### Fidelity")
    st.markdown(
        "Fidelity pada penelitian ini adalah korelasi Spearman antara komponen evidence dan `score_raw` model, "
        "bukan satu angka lolos atau gagal. Centered berarti skor prediksi dikurangi rata-rata skor pengguna tersebut."
    )
    st.markdown(fidelity_dots_html(), unsafe_allow_html=True)
    st.caption("Rentang korelasi mentah: −0,087 sampai +0,228. Rentang centered: −0,061 sampai +0,308. Sumber: Tabel 4.23.")
    st.markdown(
        """
        Pada uji kontrafaktual, selisih penurunan skor prediksi antara penghapusan evidence target
        dan penghapusan genre acak adalah 0,0174 untuk preference, 0,0072 untuk frequency,
        dan 0,0096 untuk recent. Angka ini disalin dari Tabel 4.24 dan tidak dihitung ulang di aplikasi.
        """
    )


def main() -> None:
    st.set_page_config(
        page_title="ReelExplain",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_css()
    try:
        frame = load_demo()
    except (FileNotFoundError, ValueError) as error:
        st.error(str(error))
        st.stop()

    example_id = example_user_id(frame)
    st.sidebar.markdown("### ReelExplain")
    st.sidebar.caption("FunkSVD + penjelasan berbasis aturan")
    page = st.sidebar.radio(
        "Navigasi",
        ["Beranda", "Rekomendasi", "Cara Kerja", "Evaluasi"],
        label_visibility="collapsed",
    )
    st.sidebar.divider()
    st.sidebar.caption("Data rekomendasi sudah dihasilkan penelitian. Aplikasi tidak melatih ulang model.")

    if page == "Beranda":
        page_home(frame)
    elif page == "Rekomendasi":
        page_recommendations(frame, example_id)
    elif page == "Cara Kerja":
        page_how()
    else:
        page_evaluation(frame)


if __name__ == "__main__":
    main()