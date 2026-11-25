import pandas as pd

URL = (
    "https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/"
    "prix-des-carburants-en-france-flux-instantane-v2/exports/csv"
)

df = pd.read_csv(
    URL, sep=";",
    dtype={"id": str, "cp": str, "code_departement": str, "code_region": str},
)

print("Stations uniques :", df["id"].is_unique)
print("\nTaux de valeurs manquantes (%) :")
print((df.isna().mean() * 100).round(1).sort_values(ascending=False).head(15))

prix_cols = [c for c in df.columns if c.endswith("_prix")]
print("\nStatistiques des prix :")
print(df[prix_cols].describe().round(3))

print("\nExemple de geom, prix et cp :")
print(df[["geom", "prix", "cp"]].head(3).to_string())