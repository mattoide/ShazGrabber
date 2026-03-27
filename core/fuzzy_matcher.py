import re, unicodedata
from rapidfuzz import fuzz, process

def _norm(s):
    s = s.lower()
    s = re.sub(r"[^\w\s]", " ", s, flags=re.UNICODE)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def match_library(shazam_songs, local_files, threshold=72):
    """
    Confronta le canzoni Shazam con i file locali.
    Ritorna tre liste: matched, missing, ambiguous.
    """
    local_names  = [f["name"] for f in local_files]
    local_norms  = [_norm(n) for n in local_names]

    matched   = []
    missing   = []
    ambiguous = []

    for song in shazam_songs:
        query = _norm(f"{song['title']} {song['artist']}")

        best_score = 0
        best_file  = None

        for i, ln in enumerate(local_norms):
            title_norm = _norm(song["title"])
            artist_norm = _norm(song["artist"])
            # token_set_ratio confronta parole intere, evitando falsi positivi
            # come "red" trovato dentro "bored"
            t = fuzz.token_set_ratio(title_norm, ln)
            a = fuzz.token_set_ratio(artist_norm, ln)
            score = t * 0.65 + a * 0.35
            if score > best_score:
                best_score = score
                best_file  = local_files[i]

        entry = {**song, "score": round(best_score, 1), "match": best_file}

        if best_score >= threshold:
            matched.append(entry)
        elif best_score >= threshold - 15:
            ambiguous.append(entry)
        else:
            missing.append(entry)

    return matched, missing, ambiguous
