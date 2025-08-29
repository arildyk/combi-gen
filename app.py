import itertools
import io
import math
import streamlit as st
import pandas as pd

st.set_page_config(page_title="CombiGen", page_icon="🎲", layout="wide")
st.title("🎲 CombiGen")
st.caption("Générateur simple de combinaisons avec estimation en direct.")

# Bornes
MAX_NUMBERS = 20
MAX_COMBI_SIZE = 20
WARN_THRESHOLD = 200_000
PREVIEW_ROWS = 1_000

# ---------- Utilitaires ----------
def parse_numbers(s: str):
    raw = [x.strip() for x in s.replace(";", ",").replace("\n", ",").split(",")]
    nums, errs = [], []
    for x in raw:
        if not x:
            continue
        try:
            v = int(x) if x.replace("-", "", 1).isdigit() else float(x)
            nums.append(v)
        except Exception:
            errs.append(x)
    return nums, errs

def nCr(n, r):
    try:
        return math.comb(n, r)
    except AttributeError:
        if r < 0 or r > n: return 0
        r = min(r, n - r); num = den = 1
        for i in range(1, r+1):
            num *= n - (r - i); den *= i
        return num // den

def format_big(n: int) -> str:
    return f"{n:,}".replace(",", " ")

def iter_with_progress(it, total, update_every=5000, desc="Génération…"):
    progress = st.progress(0, text=desc)
    out = []
    for i, tup in enumerate(it, start=1):
        out.append(tup)
        if i % update_every == 0 or i == total:
            progress.progress(min(i / total, 1.0), text=f"{desc} {format_big(i)}/{format_big(total)}")
    progress.empty()
    return out

# ---------- Sidebar (réglages) ----------
with st.sidebar:
    st.header("Réglages")
    s_numbers = st.text_area("Liste de nombres", value="1, 2, 3, 4", height=120,
                             help="Séparateurs: virgule, point-virgule ou retour à la ligne.")
    de_dupe = st.checkbox("Supprimer les doublons (conserve l'ordre)", value=True)
    all_lengths = st.checkbox("Toutes les longueurs (1..N)", value=False)
    r = st.number_input("Taille r", min_value=1, value=2, step=1, max_value=MAX_COMBI_SIZE,
                        help="Ignoré si 'Toutes les longueurs' est coché.")
    only_preview = st.checkbox(f"Afficher un aperçu (≤ {PREVIEW_ROWS} lignes)", value=True)

# ---------- Estimation en direct ----------
numbers_preview, errs_preview = parse_numbers(s_numbers)
if de_dupe:
    seen = set()
    numbers_preview = [x for x in numbers_preview if (x not in seen and not seen.add(x))]
N_preview = len(numbers_preview)

cols = st.columns(2)
cols[0].metric("N (éléments)", N_preview)
cols[1].metric("Longueur", f"1..{min(N_preview, MAX_COMBI_SIZE)}" if all_lengths else f"r = {min(r, MAX_COMBI_SIZE)}")

if errs_preview:
    st.warning(f"Valeurs ignorées (non numériques) : {', '.join(errs_preview)}")

est_total = 0
if N_preview == 0:
    st.info("Saisissez des nombres pour obtenir l’estimation.")
elif N_preview > MAX_NUMBERS:
    st.error(f"Trop d’éléments : {N_preview} (limite {MAX_NUMBERS}).")
else:
    max_len = min(N_preview, MAX_COMBI_SIZE)
    if all_lengths:
        est_total = sum(nCr(N_preview, k) for k in range(1, max_len + 1))
        st.metric("Estimation (1..N)", format_big(est_total))
    else:
        if r > max_len:
            st.warning(f"r doit être ≤ {max_len} (N={N_preview}, limite={MAX_COMBI_SIZE}).")
        else:
            est_total = nCr(N_preview, r)
            st.metric("Estimation (r)", format_big(est_total))
    if est_total > WARN_THRESHOLD:
        st.warning("Beaucoup de résultats : préférez l’aperçu et le téléchargement CSV.")

st.divider()

# ---------- Action ----------
col_go, col_dl = st.columns([1, 1])
go = col_go.button("🚀 Générer")
dl_placeholder = col_dl.empty()

if go:
    # Validation
    numbers, errors = parse_numbers(s_numbers)
    if de_dupe:
        seen = set()
        numbers = [x for x in numbers if (x not in seen and not seen.add(x))]
    if not numbers:
        st.error("Aucun nombre valide fourni."); st.stop()
    N = len(numbers)
    if N > MAX_NUMBERS:
        st.error(f"Trop d’éléments ! Maximum {MAX_NUMBERS} (vous avez {N})."); st.stop()
    if not all_lengths and (r < 1 or r > min(N, MAX_COMBI_SIZE)):
        st.error(f"r doit être entre 1 et {min(N, MAX_COMBI_SIZE)}."); st.stop()

    st.subheader("Résultats")

    # Génération
    with st.spinner("Calcul…"):
        if all_lengths:
            max_len = min(N, MAX_COMBI_SIZE)
            grand_total = sum(nCr(N, k) for k in range(1, max_len + 1))
            progress = st.progress(0, text="Préparation…")
            results, done_before = [], 0
            for k in range(1, max_len + 1):
                it = itertools.combinations(numbers, k)
                k_total = nCr(N, k)
                j = 0
                for tup in it:
                    results.append(tup)
                    j += 1
                    if j % 5000 == 0 or j == k_total:
                        progress.progress((done_before + j) / grand_total,
                                          text=f"Génération k={k} • {format_big(done_before + j)}/{format_big(grand_total)}")
                done_before += k_total
            progress.empty()
        else:
            it = itertools.combinations(numbers, r)
            total = nCr(N, r)
            results = iter_with_progress(it, total, update_every=5000, desc="Génération…")

    st.success(f"{format_big(len(results))} combinaisons générées.")
    st.caption(f"Liste nettoyée ({N} éléments) : {numbers}")

    # Aperçu + téléchargement
    df = pd.DataFrame(results)
    if only_preview and len(df) > PREVIEW_ROWS:
        st.caption(f"Aperçu des {PREVIEW_ROWS} premières lignes (total {format_big(len(df))}).")
        st.dataframe(df.head(PREVIEW_ROWS), use_container_width=True, height=420)
    else:
        st.dataframe(df, use_container_width=True, height=420)

    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    dl_placeholder.download_button("💾 Télécharger le CSV complet",
                                   data=csv_buf.getvalue().encode("utf-8"),
                                   file_name="resultats.csv",
                                   mime="text/csv")
