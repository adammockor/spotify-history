import requests

import re
import unicodedata
import logging
import humanize

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def normalize_itunes_term(text: str) -> str:
    """
    Normalize album / artist strings for iTunes Search API.
    """

    if not text:
        return ""

    # 1. Unicode → ASCII
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")

    # 2. Lowercase for consistency
    text = text.lower()

    # 3. Remove parenthetical content
    text = re.sub(r"\([^)]*\)", "", text)

    # 4. Remove common suffixes
    text = re.sub(
        r"\b(remastered|deluxe|edition|single|ep|version)\b",
        "",
        text,
    )

    # 5. Normalize separators
    text = text.replace("&", "and")

    # 6. Collapse whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def get_album_art(album: str, artist: str) -> str | None:
    r = requests.get(
        "https://itunes.apple.com/search",
        params={
            "term": f"{normalize_itunes_term(album)} {normalize_itunes_term(artist)}",
            "media": "music",
            "entity": "album",
            "limit": 5
        },
        timeout=15,
    )
    logger.info("iTunes request URL: %s", r.request.url)
    if r.status_code != 200:
        return None

    results = r.json().get("results", [])
    if results:
        logger.info(
            "iTunes results (top %d): %s",
            len(results),
            [
                {
                    "artist": item.get("artistName"),
                    "album": item.get("collectionName"),
                    "type": item.get("collectionType"),
                }
                for item in results
            ],
        )
    else:
        logger.info("iTunes results: no matches")
    if not results:
        return None

    # print(results)

    return results[0].get("artworkUrl100")



