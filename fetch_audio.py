"""Fetch the episode audio from the public podcast feed (not stored in the repo)."""
import os, re, html, urllib.request

FEED = "https://rss.podplaystudio.com/1103.xml"
TITLE = "Det Brændende Lig"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio", "episode.mp3")

os.makedirs(os.path.dirname(OUT), exist_ok=True)
feed = urllib.request.urlopen(FEED, timeout=60).read().decode("utf-8", "ignore")
for item in feed.split("<item>")[1:]:
    t = html.unescape(re.sub(r"<!\[CDATA\[|\]\]>", "", re.search(r"<title>(.*?)</title>", item, re.S).group(1))).strip()
    if t == TITLE:
        url = html.unescape(re.search(r'<enclosure[^>]*url="([^"]+)"', item).group(1))
        urllib.request.urlretrieve(url, OUT)
        print("saved", OUT)
        break
else:
    raise SystemExit("episode not found in feed")
