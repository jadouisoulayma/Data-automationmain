"""
Pipeline de traitement produits — traduit depuis le notebook
workflow_produits_complet_version_final.ipynb

Ce module expose une seule fonction publique :
    run_pipeline(input_path, backoffice_path, training_path, output_dir, progress_cb=None)

qui exécute toutes les étapes dans l'ordre et renvoie le chemin du fichier Excel final.

progress_cb(pct: int, message: str)  — callback optionnel pour la progression.
"""

import os
import re
import io
import random
import logging
import pandas as pd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constantes : Mapping état brut → valeur PrestaShop (notebook cell 12)
# ---------------------------------------------------------------------------
CONDITION_MAPPING = {
    # ── NEUF ──
    "N":            "Neuf",
    "N/SANS BOITE": "Neuf",
    "NSB":          "Neuf",
    "NEUF":         "Neuf",
    "DEFAULT":      "Neuf",
    # ── COMME NEUF ──
    "NOP":          "Comme neuf",
    "NWB":          "Comme neuf",
    "CN":           "Comme neuf",
    "USEDCN":       "Comme neuf",
    # ── OCCASION ──
    "USEDA":        "Occasion",
    "USEDB":        "Occasion",
    "USEBC":        "Occasion",
    "USEDC":        "Occasion",
    "USEDBC":       "Occasion",
    "OBESB":        "Occasion",
    "OAP":          "Occasion",
    "O":            "Occasion",
    "OCCASION":     "Occasion",
    # ── RECONDITIONNÉ ──
    "RECNEUF":      "reconditionné",
    "RECMINT":      "reconditionné",
    "RECTBE":       "reconditionné",
    "RECBE":        "reconditionné",
    "RECEC":        "reconditionné",
}
CONDITION_DEFAUT = "Neuf"  # valeur par défaut si le code n'est pas reconnu

# ---------------------------------------------------------------------------
# Constantes : Textes SEO High-Tech Moving (notebook cell 18)
# ---------------------------------------------------------------------------
ACCROCHES = [
    "Nous vous proposons en liquidation exceptionnelle : <strong>{NOM}</strong>.",
    "Découvrez dès maintenant <strong>{NOM}</strong>, disponible en stock limité.",
    "Profitez d'une offre exceptionnelle sur <strong>{NOM}</strong>.",
    "En exclusivité chez High-Tech Moving : <strong>{NOM}</strong>.",
]

# ---------------------------------------------------------------------------
# Constantes : Calcul prix (notebook cell 20)
# ---------------------------------------------------------------------------
TAUX_TVA = 1.20

# ---------------------------------------------------------------------------
# Constantes : Colonnes finales export (notebook cell 24)
# ---------------------------------------------------------------------------
COLONNES_FINALES = [
    "NOM DU PRODUIT", "ean", "sku", "etat", "quantite", "id_tax_rules_group",
    "idMarqueSite", "idCategorySite", "description", "recap",
    "price_particulier", "price_profesionnel", "image_urls",
    "meta_title", "meta_description", "meta_keywords", "mot_clés", "actif",
]


# ---------------------------------------------------------------------------
# Helpers partagés
# ---------------------------------------------------------------------------

def _p(cb, pct, msg):
    """Appelle le callback de progression si fourni."""
    logger.info("[%3d%%] %s", pct, msg)
    if cb:
        cb(pct, msg)


def _trouver_colonne(nom_cherche, colonnes):
    """Recherche insensible à la casse."""
    mapping = {c.lower().strip(): c for c in colonnes}
    return mapping.get(nom_cherche.lower().strip())


def _lire_fichier(chemin):
    ext = os.path.splitext(chemin)[1].lower()
    if ext in (".xlsx", ".xls"):
        return pd.read_excel(chemin)
    df_best = None
    for sep, eng in [(";", "c"), (",", "c"), ("\t", "c"),
                     (";", "python"), (",", "python"), ("\t", "python"), (None, "python")]:
        try:
            c = pd.read_csv(chemin, sep=sep, engine=eng)
        except Exception:
            continue
        if df_best is None or c.shape[1] > df_best.shape[1]:
            df_best = c
        if df_best is not None and df_best.shape[1] > 1:
            break
    if df_best is None:
        raise ValueError(f"Impossible de lire : {chemin}")
    return df_best


# ── Etape 1 : Nettoyage + fusion doublons ──────────────────────────────────
def etape1_nettoyage(df_brut, cb=None):
    _p(cb, 5, "Etape 1 : Nettoyage + fusion des doublons...")
    df_brut = df_brut.copy()
    df_brut.columns = df_brut.columns.str.strip()
    cn  = _trouver_colonne("NOM DU PRODUIT", df_brut.columns) or _trouver_colonne("name", df_brut.columns)
    ce  = _trouver_colonne("EAN", df_brut.columns) or _trouver_colonne("ean", df_brut.columns)
    cet = _trouver_colonne("etat", df_brut.columns)
    cp  = _trouver_colonne("pc", df_brut.columns)
    cpv = _trouver_colonne("prixVente", df_brut.columns)
    cq  = _trouver_colonne("quantite", df_brut.columns)
    for lbl, col in [("NOM DU PRODUIT", cn), ("EAN", ce), ("etat", cet),
                     ("pc", cp), ("prixVente", cpv), ("quantite", cq)]:
        if col is None:
            raise ValueError(f"Colonne obligatoire introuvable : {lbl}")
    df = df_brut.rename(columns={
        cn: "NOM DU PRODUIT", ce: "EAN", cet: "etat", cp: "pc", cpv: "prixVente", cq: "quantite"
    })
    df["NOM DU PRODUIT"] = df["NOM DU PRODUIT"].astype(str).str.strip()
    df["etat"] = df["etat"].astype(str).str.strip().str.upper()
    for col in ["pc", "prixVente"]:
        df[col] = (df[col].astype(str)
                   .str.replace("\u20ac", "", regex=False)
                   .str.replace("\u00a0", "", regex=False)
                   .str.replace(" ", "", regex=False)
                   .str.replace(",", ".", regex=False))
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["quantite"] = pd.to_numeric(df["quantite"], errors="coerce").fillna(0)
    nb_av = len(df)
    df_c = (df.groupby(["NOM DU PRODUIT", "EAN", "etat", "pc", "prixVente"],
                       as_index=False, dropna=False)
              .agg({"quantite": "sum"}))
    stats = {"lignes_avant": nb_av, "lignes_apres_fusion": len(df_c),
             "doublons_fusionnes": nb_av - len(df_c)}
    logger.info("Etape1: %d->%d lignes", nb_av, len(df_c))
    return df_c, stats


# ── Etape 1bis : Controle qualite ──────────────────────────────────────────
def etape1bis_controle_qualite(df_clean, cb=None):
    _p(cb, 12, "Etape 1bis : Controle qualite quantite/pc/prixVente...")
    def _ctrl(v, n):
        if pd.isna(v):
            return f"{n} vide"
        try:
            x = float(str(v).replace(",", "."))
        except Exception:
            return f"{n} non numerique"
        if x < 0:
            return f"{n} negatif"
        if x == 0:
            return f"{n} = 0"
        return None
    df_c = df_clean.copy()
    for col in ["quantite", "pc", "prixVente"]:
        df_c[f"_e_{col}"] = df_c[col].apply(lambda v, c=col: _ctrl(v, c))
    def _msg(row):
        e = [row[f"_e_{c}"] for c in ["quantite", "pc", "prixVente"] if pd.notna(row[f"_e_{c}"])]
        return " ; ".join(e) if e else None
    df_c["Erreur"] = df_c.apply(_msg, axis=1)
    mask = df_c["Erreur"].notna()
    df_ok  = df_clean.loc[~mask].copy()
    df_err = df_clean.loc[mask].copy()
    df_err["Erreur"] = df_c.loc[mask, "Erreur"].values
    t = len(df_clean)
    stats = {"total": t, "correctes": len(df_ok), "erreurs": len(df_err),
             "taux_erreur": round(len(df_err) / t * 100, 2) if t else 0}
    logger.info("Etape1bis: %d ok, %d erreurs", len(df_ok), len(df_err))
    return df_ok.reset_index(drop=True), df_err, stats


# ── Etape 1ter : Comparaison backoffice ───────────────────────────────────
def etape1ter_backoffice(df_clean, df_bo, cb=None):
    _p(cb, 20, "Etape 1ter : Comparaison avec le backoffice...")
    df_bo = df_bo.copy()
    df_bo.columns = df_bo.columns.str.strip()
    cn = (_trouver_colonne("name", df_bo.columns)
          or _trouver_colonne("NOM DU PRODUIT", df_bo.columns))
    ce = (_trouver_colonne("ean13", df_bo.columns)
          or _trouver_colonne("EAN", df_bo.columns)
          or _trouver_colonne("ean", df_bo.columns))
    if cn is None or ce is None:
        logger.warning("Colonnes backoffice introuvables - comparaison ignoree")
        dc2 = df_clean.copy()
        return dc2, pd.DataFrame(), dc2, {"dupliques": 0, "nouveaux": len(dc2)}
    df_bo = df_bo.rename(columns={cn: "name", ce: "ean13"})
    df_c = df_clean.copy()
    df_c["EAN"] = df_c["EAN"].astype(str).str.replace(".0", "", regex=False).str.strip()
    df_c["_nc"] = df_c["NOM DU PRODUIT"].astype(str).str.lower().str.strip()
    df_bo["ean13"] = df_bo["ean13"].astype(str).str.replace(".0", "", regex=False).str.strip()
    df_bo["_nc"]   = df_bo["name"].astype(str).str.lower().str.strip()
    df_bo_k = df_bo[["_nc", "ean13"]].drop_duplicates()
    dm = df_c.merge(df_bo_k, left_on=["_nc", "EAN"], right_on=["_nc", "ean13"],
                    how="left", indicator=True)
    co = [c for c in df_c.columns if c != "_nc"]
    df_dup = dm.loc[dm["_merge"] == "both",      co].copy()
    df_new = dm.loc[dm["_merge"] == "left_only", co].copy()
    stats = {"dupliques": len(df_dup), "nouveaux": len(df_new)}
    logger.info("Etape1ter: %d dupliques, %d nouveaux", len(df_dup), len(df_new))
    return df_new.reset_index(drop=True), df_dup, df_new, stats


# ── Etape 1qua : Mapping etat ─────────────────────────────────────────────
def etape1qua_mapping_etat(df_clean, cb=None):
    _p(cb, 28, "Etape 1qua : Mapping etat -> valeurs PrestaShop...")
    df_clean = df_clean.copy()
    df_clean["etat_brut"] = df_clean["etat"].astype(str).str.strip().str.upper()
    non_rec = sorted(set(df_clean["etat_brut"]) - set(CONDITION_MAPPING.keys()))
    if non_rec:
        logger.warning("Codes etat non reconnus (defaut '%s'): %s", CONDITION_DEFAUT, non_rec)
    df_clean["etat"] = df_clean["etat_brut"].apply(
        lambda v: CONDITION_MAPPING.get(v, CONDITION_DEFAUT))
    return df_clean


# ── Etape 2 : EAN-13 + longueur champs ───────────────────────────────────
def etape2_ean_longueur(df_clean, cb=None):
    _p(cb, 35, "Etape 2 : Correction EAN-13 + longueur champs (<= 128)...")
    df_clean = df_clean.copy()
    nb_c, nb_a, anom = 0, 0, []
    def _fix(v):
        nonlocal nb_c, nb_a
        if pd.isna(v):
            return v
        t = str(v).strip()
        if t.endswith(".0"):
            t = t[:-2]
        ch = "".join(c for c in t if c.isdigit())
        if not ch:
            return v
        if len(ch) < 13:
            nb_c += 1
            return ch.zfill(13)
        if len(ch) > 13:
            nb_a += 1
            anom.append(ch)
            return ch
        return ch
    df_clean["EAN"] = df_clean["EAN"].apply(_fix)
    for col in ["NOM DU PRODUIT"]:
        if col in df_clean.columns:
            m = df_clean[col].astype(str).str.len() > 128
            df_clean.loc[m, col] = df_clean.loc[m, col].astype(str).str[:128]
    logger.info("Etape2: EAN corriges=%d anomalies=%d", nb_c, nb_a)
    return df_clean, nb_c, nb_a, anom


# ── Etape 3 : Prediction ML ───────────────────────────────────────────────
def etape3_ml(df_clean, df_tr, cb=None):
    _p(cb, 42, "Etape 3 : Prediction ML idMarqueSite + idCategorySite...")
    from sklearn.pipeline import Pipeline as SKP
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.svm import LinearSVC
    from sklearn.linear_model import LogisticRegression, SGDClassifier
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import LabelEncoder
    from sklearn.metrics import accuracy_score

    df_tr = df_tr.copy()
    df_tr.columns = df_tr.columns.str.strip()
    cn = _trouver_colonne("name", df_tr.columns) or _trouver_colonne("NOM DU PRODUIT", df_tr.columns)
    cm = _trouver_colonne("id_marque", df_tr.columns) or _trouver_colonne("idmarquesite", df_tr.columns)
    cc = _trouver_colonne("id_category", df_tr.columns) or _trouver_colonne("idcategorysite", df_tr.columns)
    if not all([cn, cm, cc]):
        logger.warning("Colonnes ML introuvables - prediction desactivee")
        df_clean = df_clean.copy()
        df_clean["idMarqueSite"] = 0
        df_clean["idCategorySite"] = 0
        return df_clean, "N/A", "N/A", 0.0, 0.0

    df_t = df_tr.dropna(subset=[cn, cm, cc]).copy()
    Xt = df_t[cn].astype(str)

    def _modeles():
        # SVC et SGD sont tres rapides, RF est bon, LR est stable
        # XGBoost retire car incompatible Python 3.14
        m = {
            "SVC": LinearSVC(max_iter=2000),
            "Logistic Regression": LogisticRegression(max_iter=500),
            "Naive Bayes": MultinomialNB(),
            "SGD": SGDClassifier(loss="hinge", max_iter=500, random_state=42),
            "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1),
        }
        return m

    def _best(X, y):
        le = LabelEncoder()
        ye = le.fit_transform(y.astype(str))
        sc, pi = {}, {}
        for nom, mo in _modeles().items():
            try:
                p = SKP([("tf", TfidfVectorizer(ngram_range=(1, 3), min_df=1)), ("mo", mo)])
                p.fit(X, ye)
                s = accuracy_score(ye, p.predict(X))
                sc[nom] = s
                pi[nom] = p
                logger.info("  ML %s -> %.2f%%", nom, s * 100)
            except Exception as e:
                logger.warning("  ML %s echec: %s", nom, e)
        if not sc:
            raise RuntimeError("Aucun modele ML entraine")
        best = max(sc, key=sc.get)
        logger.info("Meilleur modele: %s (%.2f%%)", best, sc[best] * 100)
        return pi[best], le, best, sc[best]

    _p(cb, 44, "Etape 3 : Entrainement idMarqueSite...")
    pm, lm, nm_m, am = _best(Xt, df_t[cm])
    _p(cb, 47, f"Etape 3 : Best marque={nm_m} ({am*100:.1f}%). Entrainement idCategorySite...")
    pc2, lc, nm_c, ac = _best(Xt, df_t[cc])
    _p(cb, 50, f"Etape 3 : Best cat={nm_c} ({ac*100:.1f}%). Prediction en cours...")

    df_clean = df_clean.copy()
    Xp = df_clean["NOM DU PRODUIT"].astype(str)
    df_clean["idMarqueSite"]   = lm.inverse_transform(pm.predict(Xp))
    df_clean["idCategorySite"] = lc.inverse_transform(pc2.predict(Xp))
    logger.info("Etape3: marque=%s %.2f%%, cat=%s %.2f%%", nm_m, am * 100, nm_c, ac * 100)
    return df_clean, nm_m, nm_c, am, ac


# ── Etape 4 : Textes High-Tech Moving ────────────────────────────────────
_DESC = (
    "<p><strong>Bonjour et bienvenue chez High-Tech Moving !</strong></p>"
    "<p>{ACCROCHE}</p>"
    "<p><strong>Etat :</strong> {ETAT}</p>"
    "<p>Facture incluse<br>Garantie constructeur</p>"
    "<p>Plus de produits sur : <strong>www.hightechmoving.com</strong></p>"
    "<p>Contact : +33 6 11 87 70 10 / +33 1 71 60 53 88</p>"
    "<h3>Pourquoi choisir High-Tech Moving ?</h3>"
    "<ul><li>10 ans d'expertise</li><li>Produits authentiques</li>"
    "<li>Tarifs imbattables</li><li>Service client reactif</li></ul>"
    "<h3>Ou nous trouver ?</h3>"
    "<p><strong>High-Tech Moving</strong><br>7B Rue Michel Chasles, 75012 Paris</p>"
    "<ul><li>Metros : 1 et 14</li><li>RER : A et D</li><li>Bus : 57 et 56</li></ul>"
    "<p>Ouvert tous les jours de 10h a 20h</p>"
    "<p><strong>Stock limite - Profitez de cette offre !</strong></p>"
)
_RECAP = (
    '<table style="border:1px solid #ddd;border-collapse:collapse;width:100%;font-family:Arial,sans-serif;">'
    '<thead><tr>'
    '<th style="padding:8px;background:#f2f2f2;text-align:left;">Attribut</th>'
    '<th style="padding:8px;background:#f2f2f2;text-align:left;">Valeur</th>'
    '</tr></thead><tbody>'
    '<tr><td style="padding:8px;font-weight:bold;">Nom</td><td style="padding:8px;">{NOM}</td></tr>'
    '<tr><td style="padding:8px;font-weight:bold;">Etat</td><td style="padding:8px;">{ETAT}</td></tr>'
    '<tr><td style="padding:8px;font-weight:bold;">EAN</td><td style="padding:8px;">{EAN}</td></tr>'
    '<tr><td style="padding:8px;font-weight:bold;">Prix</td><td style="padding:8px;">{PRIX} EUR</td></tr>'
    '</tbody></table>'
)


def etape4_textes(df_clean, cb=None):
    _p(cb, 58, "Etape 4 : Generation description / recap / meta_title / meta_keywords...")
    df_clean = df_clean.copy()

    def _acc(nom, seed=None):
        rnd = random.Random(seed if seed is not None else abs(hash(nom)) % (2 ** 32))
        return rnd.choice(ACCROCHES).format(NOM=nom)

    def _prix_fmt(p):
        try:
            return f"{float(p):.2f}"
        except Exception:
            return "0.00"

    def _mots_cles(nom, mx=128):
        return (", ".join(str(nom).lower().split()))[:mx]

    desc, recap, mt, md, mk, mc = [], [], [], [], [], []
    for _, row in df_clean.iterrows():
        nom  = str(row["NOM DU PRODUIT"])
        etat = str(row["etat"]).capitalize()
        ean  = str(row["EAN"])
        prix = row.get("prixVente", 0)
        try:
            seed = int(str(ean).replace(".", "")[:9])
        except Exception:
            seed = None
        desc.append(_DESC.format(ACCROCHE=_acc(nom, seed), ETAT=etat))
        recap.append(_RECAP.format(NOM=nom, ETAT=etat, EAN=ean, PRIX=_prix_fmt(prix)))
        mt.append(nom[:128])
        md.append(f"{nom} - {etat}"[:128])
        mots = _mots_cles(nom)
        mk.append(mots)
        mc.append(mots)

    df_clean["description"]      = desc
    df_clean["recap"]            = recap
    df_clean["meta_title"]       = mt
    df_clean["meta_description"] = md
    df_clean["meta_keywords"]    = mk
    df_clean["mot_clés"]         = mc
    return df_clean


# ── Etape 5 : SKU + prix + TVA + actif ───────────────────────────────────
def etape5_sku_prix(df_clean, cb=None):
    _p(cb, 68, "Etape 5 : SKU + price_particulier/price_profesionnel + TVA + actif...")
    df_clean = df_clean.copy()
    df_clean["sku"] = (
        df_clean.get("etat_brut", df_clean["etat"]).astype(str)
        + "-"
        + df_clean["EAN"].astype(str)
    )
    prix = pd.to_numeric(df_clean["prixVente"], errors="coerce").fillna(0)
    df_clean["price_particulier"]  = (prix / TAUX_TVA).round(2)
    df_clean["price_profesionnel"] = (prix / TAUX_TVA).round(2)
    df_clean["id_tax_rules_group"] = 70
    df_clean["actif"] = 1
    return df_clean


# ── Etape 6 : Images Bing ─────────────────────────────────────────────────
def etape6_images(df_clean, cb=None):
    _p(cb, 75, "Etape 6 : Generation URLs images Bing...")
    from urllib.parse import quote
    df_clean = df_clean.copy()

    # ── Colonnes candidates : photo réelle (après fond blanc) ──────────────
    _COLS_PHOTO_REELLE = ["photo_reelle", "photo_reel", "image_reelle", "image_reel",
                          "real_image", "photo_url", "image_url", "photo", "image"]

    # ── Colonnes candidates : images standard Z (après photo réelle) ────────
    _COLS_IMAGES_Z = ["images_z", "image_z", "images_standard_z", "image_standard_z",
                      "standard_z", "images_std_z", "img_z", "photos_z", "photo_z"]

    cols_lower = {c.lower().strip(): c for c in df_clean.columns}

    col_reelle = None
    for candidat in _COLS_PHOTO_REELLE:
        if candidat in cols_lower:
            col_reelle = cols_lower[candidat]
            break

    col_z = None
    for candidat in _COLS_IMAGES_Z:
        if candidat in cols_lower:
            col_z = cols_lower[candidat]
            break

    def _val_ou_none(row, col):
        """Retourne la valeur de la colonne ou 'None' si absente/vide."""
        if col is None:
            return "None"
        val = row[col]
        if pd.notna(val) and str(val).strip() not in ("", "nan", "None", "none"):
            return str(val).strip()
        return "None"

    def _build_image_urls(row):
        nom = str(row["NOM DU PRODUIT"]).strip()

        # 1. Photo fond blanc — URL Bing générée automatiquement
        url_fond_blanc = f"https://www.bing.com/images/search?q={quote(nom)}&form=HDRSC2"

        # 2. Photo réelle — None si absente/vide
        url_photo_reelle = _val_ou_none(row, col_reelle)

        # 3. Images standard Z — None si absentes/vides
        url_images_z = _val_ou_none(row, col_z)

        return f"{url_fond_blanc},{url_photo_reelle},{url_images_z}"

    df_clean["image_urls"] = df_clean.apply(_build_image_urls, axis=1)
    return df_clean


# ── Etape 7 : Export Excel ────────────────────────────────────────────────
def etape7_export(df_clean, df_err, df_dup, output_dir, cb=None, input_filename="produits"):
    """
    Export des 4 fichiers Excel dans un sous-dossier daté de media/workflow/resultats/.
    Nommage des fichiers : YYYYMMDD_HHMMSS_<type>.xlsx
    Rapport final      : YYYYMMDD_HHMMSS_rapport.json
    FIFO               : conserve uniquement les 3 derniers sous-dossiers de résultats.
    """
    import datetime
    import json
    import shutil

    _p(cb, 85, "Etape 7 : Assemblage final + export Excel...")

    # ── 1. Dossier resultats — output_dir est media/workflow/resultats ────
    resultats_root = output_dir
    os.makedirs(resultats_root, exist_ok=True)

    # ── 2. Sous-dossier daté YYYY-MM-DD_HH.MM.SS ─────────────────────────
    ts      = datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S")
    run_dir = os.path.join(resultats_root, ts)
    os.makedirs(run_dir, exist_ok=True)

    # ── 3. Préparer le DataFrame final ────────────────────────────────────
    df_f = df_clean.copy()
    if "EAN" in df_f.columns:
        df_f = df_f.rename(columns={"EAN": "ean"})
    cols  = [c for c in COLONNES_FINALES if c in df_f.columns]
    extra = [c for c in df_f.columns if c not in cols
             and not c.startswith("_") and c not in ("etat_brut",)]
    df_f = df_f[cols + extra]

    # ── 4. Chemins des 4 fichiers xlsx — nommés par date ─────────────────
    pf  = os.path.join(run_dir, f"{ts}_produits_finaux.xlsx")
    pe  = os.path.join(run_dir, f"{ts}_lignes_avec_erreurs.xlsx")
    pd2 = os.path.join(run_dir, f"{ts}_produits_dupliques.xlsx")
    pn  = os.path.join(run_dir, f"{ts}_produits_non_dupliques.xlsx")

    # ── 5. Export — toujours créer les 4 fichiers ─────────────────────────
    df_f.to_excel(pf, index=False)

    df_err_out = df_err if df_err is not None and len(df_err) > 0 else pd.DataFrame(
        columns=["NOM DU PRODUIT", "EAN", "etat", "pc", "prixVente", "quantite", "Erreur"]
    )
    df_err_out.to_excel(pe, index=False)

    df_dup_out = df_dup if df_dup is not None and len(df_dup) > 0 else pd.DataFrame(
        columns=["NOM DU PRODUIT", "EAN", "etat", "pc", "prixVente", "quantite"]
    )
    df_dup_out.to_excel(pd2, index=False)

    df_nd = df_clean.copy()
    if "EAN" in df_nd.columns:
        df_nd = df_nd.rename(columns={"EAN": "ean"})
    c2 = [c for c in COLONNES_FINALES if c in df_nd.columns]
    df_nd[c2].to_excel(pn, index=False)

    # ── 6. Rapport final JSON ─────────────────────────────────────────────
    # ts = format fichier  : YYYY-MM-DD_HH-MM-SS  (compatible Windows)
    # ts_lisible = format lisible : YYYY-MM-DD HH:MM:SS  (pour le rapport/logs)
    ts_lisible = ts[:10] + " " + ts[11:].replace("-", ":")
    rapport = {
        "date_execution": ts_lisible,
        "fichier_source": os.path.basename(input_filename) if input_filename else "inconnu",
        "nb_produits_traites": len(df_f),
        "nb_lignes_erreurs":   len(df_err_out),
        "nb_dupliques":        len(df_dup_out),
        "nb_non_dupliques":    len(df_nd[c2]) if c2 else 0,
        "fichiers": {
            "produits_finaux":      os.path.basename(pf),
            "lignes_avec_erreurs":  os.path.basename(pe),
            "produits_dupliques":   os.path.basename(pd2),
            "produits_non_dupliques": os.path.basename(pn),
        },
    }
    rapport_path = os.path.join(run_dir, f"{ts}_rapport.json")
    with open(rapport_path, "w", encoding="utf-8") as fj:
        json.dump(rapport, fj, ensure_ascii=False, indent=2)

    # ── 7. FIFO : garder seulement les 3 derniers sous-dossiers ──────────
    # Trie les sous-dossiers par nom (= par date) et supprime les plus anciens
    tous_runs = sorted(
        [d for d in os.listdir(resultats_root)
         if os.path.isdir(os.path.join(resultats_root, d))],
        reverse=False   # ordre croissant : le plus ancien en premier
    )
    MAX_RESULTATS = 4
    a_supprimer = tous_runs[:-MAX_RESULTATS] if len(tous_runs) > MAX_RESULTATS else []
    for ancien in a_supprimer:
        chemin_ancien = os.path.join(resultats_root, ancien)
        try:
            shutil.rmtree(chemin_ancien)
            logger.info("FIFO: suppression ancien résultat -> %s", chemin_ancien)
        except Exception as e:
            logger.warning("FIFO: impossible de supprimer %s : %s", chemin_ancien, e)

    logger.info(
        "Etape7: %d produits -> %s | %d erreurs | %d dupliques | rapport -> %s",
        len(df_f), pf, len(df_err_out), len(df_dup_out), rapport_path
    )
    return pf, pe, pd2, pn


# ── Fonction principale ───────────────────────────────────────────────────
def run_pipeline(input_path, backoffice_path, training_path, output_dir, progress_cb=None):
    """
    Execute le pipeline dans l'ordre exact du notebook.
    Retourne un dict avec les cles :
      output_final, output_erreurs, output_dupliques, output_non_dupliques,
      stats, modele_marque, modele_categorie, acc_marque, acc_categorie, nb_produits
    """
    cb = progress_cb
    _p(cb, 0, "Demarrage du pipeline...")
    _p(cb, 2, "Chargement des fichiers...")
    dfi = _lire_fichier(input_path)
    dfb = _lire_fichier(backoffice_path)
    dft = _lire_fichier(training_path)
    _p(cb, 4, f"Fichiers charges : {len(dfi)} lignes input / {len(dfb)} backoffice / {len(dft)} training")

    df, s1            = etape1_nettoyage(dfi, cb)
    df, derr, s1b     = etape1bis_controle_qualite(df, cb)
    df, ddup, _, s1t  = etape1ter_backoffice(df, dfb, cb)
    df                = etape1qua_mapping_etat(df, cb)
    df, *_ean         = etape2_ean_longueur(df, cb)
    df, nm, nc, am, ac = etape3_ml(df, dft, cb)
    df                = etape4_textes(df, cb)
    df                = etape5_sku_prix(df, cb)
    df                = etape6_images(df, cb)
    pf, pe, pd2, pn   = etape7_export(df, derr, ddup, output_dir, cb, input_filename=input_path)

    _p(cb, 100, f"Pipeline termine - {len(df)} produits traites et exportes.")
    return {
        "output_final":         pf,
        "output_erreurs":       pe,
        "output_dupliques":     pd2,
        "output_non_dupliques": pn,
        "stats": {"etape1": s1, "etape1bis": s1b, "etape1ter": s1t},
        "modele_marque":    nm,
        "modele_categorie": nc,
        "acc_marque":       round(am * 100, 2),
        "acc_categorie":    round(ac * 100, 2),
        "nb_produits":      len(df),
    }
