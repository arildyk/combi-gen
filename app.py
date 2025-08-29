import itertools
import io
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Générateur de combinaisons", page_icon="🎲", layout="centered")
st.title("🎲 Générateur de combinaisons")

def parse_numbers(s: str):
    # Accepte séparateurs: virgule, espace, point-virgule, retour ligne
    raw = [x.strip() for x in s.replace(";", ",").replace("\n", ",").split(",")]
    nums = []
    errs = []
    for x in raw:
        if not x:
            continue
        try:
            # int si possible, sinon float
            v = int(x) if x.isdigit() or (x.startswith("-") and x[1:].isdigit()) else float(x)
            nums.append(v)
        except Exception:
            errs.append(x)
    return nums, errs

with st.form("input"):
    st.subheader("Entrées")
    s_numbers = st.text_area("Liste de nombres", value="1, 2, 3, 4", height=100,
                             help="Ex: 1,2,3,4 ou avec des retours à la ligne.")
    r = st.number_input("Taille des combinaisons (r)", min_value=1, value=2, step=1)
    all_lengths = st.checkbox("Toutes les longueurs (1..N)", value=False)
    de_dupe = st.checkbox("Supprimer les doublons dans la liste d'entrée", value=True)
    as_permutations = st.checkbox("Utiliser des **permutations** (l’ordre compte)", value=False)
    submitted = st.form_submit_button("Générer")

if submitted:
    numbers, errors = parse_numbers(s_numbers)
    if errors:
        st.warning(f"Valeurs ignorées (non numériques): {', '.join(errors)}")
    if de_dupe:
        # Conserve l'ordre d'apparition
        seen = set()
        numbers = [x for x in numbers if (x not in seen and not seen.add(x))]

    if not numbers:
        st.error("Aucun nombre valide fourni.")
        st.stop()

    N = len(numbers)
    if not all_lengths and (r < 1 or r > N):
        st.error(f"r doit être entre 1 et {N}.")
        st.stop()

    st.write(f"**Liste nettoyée ({N} éléments)** : {numbers}")

    results = []
    if all_lengths:
        for k in range(1, N + 1):
            it = itertools.permutations(numbers, k) if as_permutations else itertools.combinations(numbers, k)
            results.extend(list(it))
    else:
        it = itertools.permutations(numbers, r) if as_permutations else itertools.combinations(numbers, r)
        results = list(it)

    st.success(f"{len(results)} {'permutations' if as_permutations else 'combinaisons'} générées.")

    # Affichage + téléchargement
    df = pd.DataFrame(results)
    st.dataframe(df, use_container_width=True)

    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        "Télécharger en CSV",
        data=csv_buf.getvalue().encode("utf-8"),
        file_name="resultats.csv",
        mime="text/csv",
    )
