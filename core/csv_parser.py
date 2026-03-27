import csv, html as html_lib, re

def parse_shazam_csv(filepath):
    """
    Legge un CSV esportato dall'app Shazam.
    Formato atteso: Index, TagTime, Title, Artist, URL, TrackKey
    Restituisce lista di dict e toglie duplicati.
    """
    songs = []
    seen  = set()

    with open(filepath, encoding="utf-8-sig", errors="replace") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 4:
                continue
            # Salta intestazioni
            if row[0] in ("Index", "Shazam Library") or not row[0].strip():
                continue
            try:
                int(row[0])
            except ValueError:
                continue

            title  = html_lib.unescape(row[2].strip())
            artist = html_lib.unescape(row[3].strip())
            url    = row[4].strip() if len(row) > 4 else ""
            date   = row[1].strip() if len(row) > 1 else ""

            if not title or not artist:
                continue

            key = (title.lower(), artist.lower())
            if key not in seen:
                seen.add(key)
                songs.append({
                    "title":  title,
                    "artist": artist,
                    "url":    url,
                    "date":   date,
                })

    return songs
