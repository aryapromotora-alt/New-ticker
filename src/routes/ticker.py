import requests
from bs4 import BeautifulSoup
from flask import Blueprint, request, Response
from email.utils import format_datetime
from datetime import datetime

ticker_bp = Blueprint("ticker", __name__)

def extract_google_news(url: str):
    """Extrai notícias de qualquer página do Google News (tópicos/seções)."""
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=10)

    if r.status_code != 200:
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    items = []

    # Seleciona links de manchetes
    for a in soup.select("a.DY5T1d"):
        title = a.get_text(strip=True)
        link = "https://news.google.com" + a["href"][1:] if a["href"].startswith(".") else a["href"]

        items.append({
            "title": title,
            "link": link,
            "pubDate": format_datetime(datetime.utcnow())
        })

    return items


@ticker_bp.route("/convert", methods=["GET"])
def convert_to_rss():
    url = request.args.get("url")
    if not url:
        return Response("<error>URL é obrigatória</error>", mimetype="application/xml", status=400)

    try:
        items = extract_google_news(url)

        if not items:
            return Response("<error>Não foi possível gerar RSS válido.</error>", mimetype="application/xml", status=400)

        rss_items = "".join([
            f"""
            <item>
                <title>{i['title']}</title>
                <link>{i['link']}</link>
                <description>{i['title']}</description>
                <pubDate>{i['pubDate']}</pubDate>
            </item>
            """ for i in items
        ])

        rss_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Google News Convertido</title>
                <link>{url}</link>
                <description>Feed convertido de {url}</description>
                <lastBuildDate>{format_datetime(datetime.utcnow())}</lastBuildDate>
                {rss_items}
            </channel>
        </rss>"""

        return Response(rss_xml, mimetype="application/rss+xml")

    except Exception as e:
        return Response(f"<error>{str(e)}</error>", mimetype="application/xml", status=500)
