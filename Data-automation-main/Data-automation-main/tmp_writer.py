import pathlib, textwrap
code = textwrap.dedent('''
    """
    Pipeline produits - ordre EXACT du notebook workflow_produits_complet_version_final.ipynb

    Etapes identiques au notebook:
      1    Nettoyage + fusion doublons
      1bis Controle qualite quantite/pc/prixVente
      1ter Comparaison backoffice -> produits_dupliques + produits_non_dupliques
      1qua Mapping etat -> PrestaShop
      2    EAN-13 correction + longueur champs
      3    ML prediction idMarqueSite+idCategorySite (SVC/RF/LR/NB/SGD/XGB)
      4    Textes High-Tech Moving (description/recap/meta)
      5    SKU + prix HT/TTC + TVA + actif
      6    Images Bing URLs
      7    Export produits_finaux.xlsx + fichiers intermediaires
    """
    import os, re, random, logging
    import numpy as np
    import pandas as pd

    logger = logging.getLogger(__name__)

    CONDITION_MAPPING = {
        "N":"Neuf","N/SANS BOITE":"Neuf","NSB":"Neuf","NEUF":"Neuf","DEFAULT":"Neuf",
        "NOP":"Comme neuf","NWB":"Comme neuf","CN":"Comme neuf","USEDCN":"Comme neuf",
        "USEDA":"Occasion","USEDB":"Occasion","USEBC":"Occasion","USEDC":"Occasion",
        "USEDBC":"Occasion","OBESB":"Occasion","OAP":"Occasion","O":"Occasion","OCCASION":"Occasion",
        "RECNEUF":"reconditionne","RECMINT":"reconditionne","RECTBE":"reconditionne",
        "RECBE":"reconditionne","RECEC":"reconditionne",
    }
    CONDITION_DEFAUT = "Neuf"
