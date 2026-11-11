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
EVIDENCE_COLOR = {
    "Genre Preference": "#A78BFA",
    "Genre Frequency": "#60A5FA",
    "Item Quality": "#FBBF24",
    "Recent Preference": "#34D399",
    "Fallback generik": "#94A3B8",
}
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


def inject_css() -> None:
    st.markdown(
        """
        <style>
        .block-container { padding-top: 1.4rem; max-width: 1180px; }
        .hero {
            background: radial-gradient(1200px 420px at 10% -10%, rgba(167,139,250,.35), transparent 55%),
                        radial-gradient(900px 380px at 100% 0%, rgba(96,165,250,.22), transparent 50%),
                        linear-gradient(180deg, #171722 0%, #101018 100%);
            border: 1px solid rgba(255,255,255,.08);
            border-radius: 22px;
            padding: 2rem 2.1rem 1.6rem;
            margin-bottom: 1.2rem;
        }
        .kicker { letter-spacing: .16em; text-transform: uppercase; color: #C4B5FD; font-size: .78rem; margin: 0; }
        .hero h1 { margin: .35rem 0 .6rem; font-size: 2.5rem; line-height: 1.1; }
        .hero p { color: #D4D4D8; font-size: 1.05rem; max-width: 760px; }
        .poster {
            height: 92px; border-radius: 14px; display: flex; align-items: flex-end;
            padding: .7rem .8rem; font-weight: 700; letter-spacing: .04em; color: white;
            margin-bottom: .7rem;
        }
        .badge {
            display: inline-block; border-radius: 999px; padding: .18rem .65rem;
            font-size: .78rem; font-weight: 650; color: #0B0B10; margin: .15rem 0 .35rem;
        }
        .flow { display: flex; flex-wrap: wrap; gap: .45rem; align-items: center; margin: .6rem 0 1rem; }
        .flow span {
            background: #1C1C28; border: 1px solid rgba(255,255,255,.08);
            border-radius: 12px; padding: .55rem .75rem; font-size: .92rem;
        }
        .flow i { color: #A78BFA; font-style: normal; }
        .rule { border-left: 3px solid #A78BFA; padding: .2rem 0 .2rem .9rem; margin-bottom: .85rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


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


def poster_html(title: str) -> str:
    hue = sum(ord(char) for char in title) % 360
    initials = "".join(part[0] for part in title.replace(",", " ").split()[:2]).upper()
    safe_initials = html.escape(initials or "FL")
    return (
        f'<div class="poster" style="background: linear-gradient(135deg, hsl({hue},62%,42%), hsl({(hue + 40) % 360},55%,22%));">'
        f"{safe_initials}</div>"
    )


def badge_html(evidence: str) -> str:
    color = EVIDENCE_COLOR.get(evidence, "#E4E4E7")
    return f'<span class="badge" style="background:{color}">{html.escape(evidence)}</span>'


def format_genre(value: object) -> str:
    if pd.isna(value) or str(value).strip() == "":
        return "Genre tidak tersedia"
    return str(value).replace("|", " · ")


def format_score(value: object) -> str | None:
    if pd.isna(value):
        return None
    return f"{float(value):.2f}"


_dialog_decorator = getattr(st, "dialog", getattr(st, "experimental_dialog", None))


def render_movie_detail(row: pd.Series | dict) -> None:
    st.markdown(poster_html(row["Judul"]), unsafe_allow_html=True)
    st.markdown(f"### #{int(row['Peringkat'])} · {row['Judul']}")
    st.markdown(badge_html(row["Evidence"]), unsafe_allow_html=True)
    st.write(f"**Genre:** {format_genre(row['Genre'])}")
    score = format_score(row["SkorPrediksi"])
    if score:
        st.write(f"**Skor prediksi model (`est_clipped`):** {score}")
    st.divider()
    st.markdown("##### Mengapa film ini direkomendasikan?")
    st.info(row["Penjelasan"])
    st.caption("Penjelasan disusun secara post-hoc berbasis aturan dari hasil eksperimen.")


if _dialog_decorator:
    @_dialog_decorator("Detail Rekomendasi")
    def open_movie_dialog(row_dict: dict) -> None:
        render_movie_detail(row_dict)
else:
    open_movie_dialog = None


def page_home(frame: pd.DataFrame) -> None:
    st.markdown(
        """
        <section class="hero">
          <p class="kicker">Demo skripsi · MovieLens 1M</p>
          <h1>ReelExplain</h1>
          <p>Sistem rekomendasi film collaborative filtering berbasis FunkSVD,
          dilengkapi penjelasan post-hoc berbasis aturan. Peringkat film berasal dari model.
          Penjelasan disusun setelah rekomendasi terbentuk dan tidak mengubah urutan tersebut.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )
    coverage = (frame["Evidence"] != "Fallback generik").mean() * 100
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Pengguna", f"{frame['UserID'].nunique():,}".replace(",", "."))
    c2.metric("Rekomendasi", f"{len(frame):,}".replace(",", "."))
    c3.metric("Kategori evidence", str(frame["Evidence"].nunique()))
    c4.metric("Evidence non-fallback", f"{coverage:.2f}%".replace(".", ","))

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
        counts = frame["Evidence"].value_counts().reindex(EVIDENCE_ORDER)
        st.bar_chart(counts, color="#A78BFA", height=260)
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
            st.session_state.detail_rank = None
            st.rerun()
    with pick:
        user_id = st.selectbox("UserID", user_ids, key="user_id")

    if st.session_state.get("bound_user") != user_id:
        st.session_state.detail_rank = None
        st.session_state.bound_user = user_id

    user_df = frame[frame["UserID"] == user_id].sort_values("Peringkat")
    if user_df.empty:
        st.error(f"UserID {user_id} tidak ditemukan dalam hasil eksperimen.")
        return

    variety = user_df["Evidence"].value_counts().reindex(EVIDENCE_ORDER, fill_value=0)
    st.markdown("#### Profil pengguna")
    p1, p2, p3 = st.columns(3)
    p1.metric("User ID", str(int(user_id)))
    p2.metric("Jumlah rekomendasi", str(len(user_df)))
    p3.metric("Jenis evidence pada Top-10", str(int((variety > 0).sum())))
    st.bar_chart(variety, color="#60A5FA", height=180)
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
        shown = shown[shown["Judul"].str.contains(query.strip(), case=False, na=False)]
    st.markdown(f"#### Katalog · {len(shown)} dari {len(user_df)} film")
    if shown.empty:
        st.info("Tidak ada film yang cocok dengan pencarian atau filter pada pengguna ini.")
    else:
        for start in range(0, len(shown), 2):
            columns = st.columns(2)
            for column, (_, row) in zip(columns, shown.iloc[start : start + 2].iterrows()):
                with column:
                    with st.container(border=True):
                        st.markdown(poster_html(row["Judul"]), unsafe_allow_html=True)
                        st.markdown(f"**#{int(row['Peringkat'])} · {row['Judul']}**")
                        st.caption(format_genre(row["Genre"]))
                        st.markdown(badge_html(row["Evidence"]), unsafe_allow_html=True)
                        score = format_score(row["SkorPrediksi"])
                        if score:
                            st.caption(f"Skor prediksi model {score}")
                        if st.button(
                            "Lihat penjelasan",
                            key=f"detail-{int(user_id)}-{int(row['Peringkat'])}",
                            use_container_width=True,
                        ):
                            if open_movie_dialog is not None:
                                open_movie_dialog(row.to_dict())
                            else:
                                st.session_state.detail_rank = int(row["Peringkat"])

    if open_movie_dialog is None:
        rank = st.session_state.get("detail_rank")
        detail = user_df[user_df["Peringkat"] == rank]
        if rank is not None and not detail.empty:
            row = detail.iloc[0]
            st.markdown("#### Detail rekomendasi")
            with st.container(border=True):
                render_movie_detail(row)


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
        """
        <div class="flow">
          <span>Riwayat pengguna</span><i>→</i>
          <span>Ekstraksi evidence</span><i>→</i>
          <span>Evaluasi threshold</span><i>→</i>
          <span>Pemilihan aturan prioritas</span><i>→</i>
          <span>Kalimat penjelasan</span>
        </div>
        """,
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
    for name, text in rules:
        st.markdown(
            f'<div class="rule">{badge_html(name)}<div>{html.escape(text)}</div></div>',
            unsafe_allow_html=True,
        )
    st.markdown(
        """
        **Urutan prioritas:** Genre Preference > Genre Frequency > Item Quality > Recent Preference > Fallback generik.

        **Latent Similarity** adalah klausa tambahan, bukan kategori yang mengganti evidence utama.
        Klausa ditambahkan bila cosine similarity faktor laten item sekurang-kurangnya 0,5
        terhadap film yang pernah disukai pengguna. Pada hasil eksperimen, klausa ini menyertai 44,58% rekomendasi.
        """
    )
    st.markdown("#### Contoh kalimat dari dataset")
    st.info(
        'Direkomendasikan karena Anda sering menilai film bergenre Drama. '
        'Film ini juga mirip dengan "Schindler\'s List (1993)" yang pernah Anda sukai.'
    )
    st.caption("Contoh untuk pengguna 1, peringkat 1: Shawshank Redemption, The (1994), evidence Genre Frequency.")


def page_evaluation(frame: pd.DataFrame) -> None:
    st.subheader("Evaluasi model")
    st.caption("Angka berikut disalin dari output notebook eksperimen pada protokol Full Unseen.")

    st.markdown("#### Prediksi rating")
    a, b = st.columns(2)
    a.metric("RMSE uji", "0,8731")
    b.metric("MAE uji", "0,6867")
    st.caption("RMSE mengukur rata-rata simpangan kuadrat prediksi terhadap rating uji. MAE mengukur rata-rata selisih absolutnya. Keduanya pada skala rating 1–5.")

    st.markdown("#### Pemeringkatan Full Unseen")
    ranking = pd.DataFrame(
        [
            {"Metrik": "Precision@10", "Model": 0.0357, "Acak": 0.0053},
            {"Metrik": "Recall@10", "Model": 0.0228, "Acak": 0.0028},
            {"Metrik": "NDCG@10", "Model": 0.0393, "Acak": None},
            {"Metrik": "HR@10", "Model": 0.2312, "Acak": 0.0505},
        ]
    )
    st.dataframe(ranking, hide_index=True, use_container_width=True)
    st.caption(
        "Precision@10 adalah proporsi film relevan di dalam 10 rekomendasi. "
        "Recall@10 adalah proporsi film uji yang relevan dan berhasil masuk Top-10. "
        "NDCG@10 memperhitungkan posisi film relevan. "
        "HR@10 adalah proporsi pengguna yang mendapat sekurang-kurangnya satu film relevan. "
        "Kolom acak adalah ekspektasi pemeringkatan acak pada kandidat Full Unseen. "
        "Nilainya kecil karena kandidat per pengguna sangat banyak, rata-rata sekitar 3.535 film."
    )

    st.markdown("#### Explainability")
    counts = frame["Evidence"].value_counts().reindex(EVIDENCE_ORDER)
    distribution = pd.DataFrame(
        {
            "Evidence": counts.index,
            "Jumlah": counts.values,
            "Persen": (counts.values / len(frame) * 100).round(2),
        }
    )
    e1, e2 = st.columns(2)
    e1.metric("Coverage non-fallback", "94,58%")
    e2.metric("Rekomendasi dengan klausa latent", "44,58%")
    st.bar_chart(counts, color="#34D399", height=240)
    st.dataframe(distribution, hide_index=True, use_container_width=True)
    st.caption("Coverage 94,58% berarti 5,42% rekomendasi memakai Fallback generik. Distribusi di atas dihitung dari CSV dan sesuai Tabel 4.18.")

    st.markdown("#### Fidelity")
    st.markdown(
        "Fidelity pada penelitian ini adalah korelasi Spearman antara komponen evidence dan `score_raw` model, "
        "bukan satu angka lolos atau gagal. Centered berarti skor prediksi dikurangi rata-rata skor pengguna tersebut."
    )
    fidelity = pd.DataFrame(FIDELITY_ROWS)
    st.dataframe(fidelity, hide_index=True, use_container_width=True)
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
        page_icon=":movie_camera:",
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
