import requests
from flask import Blueprint, request, Response
from email.utils import format_datetime
from datetime import datetime
from xml.sax.saxutils import escape

ticker_bp = Blueprint("ticker", __name__)

# Coloque sua chave da GNews API aqui
GNEWS_API_KEY = "5e9d7297212a7bfb8d6ff360e51bcacf"

def fetch_news_from_gnews(query=None, country="br", lang="pt", max_results=10):
    """Busca notícias usando a API oficial GNews."""
    url = "https://gnews.io/api/v4/top-headlines"
    params = {
        "apikey": GNEWS_API_KEY,
        "lang": lang,
        "country": country,
        "max": max_results
    }
    if query:
        params["q"] = query

    r = requests.get(url, params=params, timeout=10)
    if r.status_code != 200:
        return []

    data = r.json()
    return data.get("articles", [])


@ticker_bp.route("/convert", methods=["GET"])
def convert_to_rss():
    """Converte notícias em RSS pronto para o ticker."""
    query = request.args.get("q")  # opcional (ex: politica, esporte etc.)

    try:
        articles = fetch_news_from_gnews(query=query)

        if not articles:
            return Response("<error>Nenhuma notícia encontrada.</error>", mimetype="application/xml", status=404)

        rss_items = ""
        for art in articles:
            title = escape(art.get("title", "Sem título"))
            link = art.get("url", "#")
            description = escape(art.get("description", "") or "")
            pub_date = art.get("publishedAt")
            try:
                pub_date = format_datetime(datetime.strptime(pub_date, "%Y-%m-%dT%H:%M:%SZ"))
            except Exception:
                pub_date = format_datetime(datetime.utcnow())

            rss_items += f"""
            <item>
                <title>{title}</title>
                <link>{link}</link>
                <description>{description}</description>
                <pubDate>{pub_date}</pubDate>
            </item>
            """

        rss_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Notícias via GNews</title>
                <link>https://gnews.io/</link>
                <description>Manchetes do Brasil</description>
                <lastBuildDate>{format_datetime(datetime.utcnow())}</lastBuildDate>
                {rss_items}
            </channel>
        </rss>"""

        return Response(rss_xml, mimetype="application/rss+xml")

    except Exception as e:
        return Response(f"<error>{str(e)}</error>", mimetype="application/xml", status=500)
