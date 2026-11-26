"""Chargement des fichiers bruts dans DuckDB."""
import logging
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
DB_PATH = ROOT / "data" / "warehouse.duckdb"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def load_file(con: duckdb.DuckDBPyConnection, path: Path) -> int:
    """Charge un fichier dans raw.fuel_prices, dans une transaction."""
    source = f"read_csv('{path.as_posix()}', delim=';', header=true, all_varchar=true)"
    select = (
        f"SELECT *, '{path.name}' AS _source_file, current_timestamp AS _loaded_at "
        f"FROM {source}"
    )
    con.execute("BEGIN")
    try:
        con.execute(f"CREATE TABLE IF NOT EXISTS raw.fuel_prices AS {select} LIMIT 0")
        con.execute(f"INSERT INTO raw.fuel_prices BY NAME {select}")
        rows = con.execute(
            "SELECT count(*) FROM raw.fuel_prices WHERE _source_file = ?", [path.name]
        ).fetchone()[0]
        con.execute(
            "INSERT INTO raw.loaded_files (file_name, row_count) VALUES (?, ?)",
            [path.name, rows],
        )
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
    return rows


def load() -> int:
    """Charge les fichiers bruts qui ne l'ont pas encore été."""
    files = sorted(RAW_DIR.glob("fuel_prices_*.csv"))
    con = duckdb.connect(str(DB_PATH))
    try:
        con.execute("CREATE SCHEMA IF NOT EXISTS raw")
        con.execute("""
            CREATE TABLE IF NOT EXISTS raw.loaded_files (
                file_name VARCHAR PRIMARY KEY,
                row_count BIGINT,
                loaded_at TIMESTAMP DEFAULT current_timestamp
            )
        """)
        already_loaded = {
            row[0] for row in con.execute("SELECT file_name FROM raw.loaded_files").fetchall()
        }
        new_files = [f for f in files if f.name not in already_loaded]

        if not new_files:
            logger.info("Aucun nouveau fichier à charger")
            return 0

        for path in new_files:
            rows = load_file(con, path)
            logger.info("Chargé : %s (%d lignes)", path.name, rows)
        return len(new_files)
    finally:
        con.close()


if __name__ == "__main__":
    load()