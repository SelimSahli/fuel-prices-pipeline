"""Extraction du flux instantané des prix des carburants."""
import logging
from datetime import datetime, timezone
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

URL = (
    "https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/"
    "prix-des-carburants-en-france-flux-instantane-v2/exports/csv"
)
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def build_session() -> requests.Session:
    """Session HTTP qui relance automatiquement en cas d'erreur serveur."""
    retry = Retry(total=3, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def extract() -> Path:
    """Télécharge le flux et l'enregistre tel quel dans data/raw."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = RAW_DIR / f"fuel_prices_{timestamp}.csv"

    logger.info("Téléchargement du flux depuis %s", URL)
    response = build_session().get(URL, timeout=60)
    response.raise_for_status()

    if b"id;" not in response.content[:200]:
        raise ValueError("Contenu inattendu : l'en-tête du fichier ne correspond pas")

    output.write_bytes(response.content)
    logger.info("Fichier enregistré : %s (%.1f Mo)", output, len(response.content) / 1e6)
    return output


if __name__ == "__main__":
    extract()