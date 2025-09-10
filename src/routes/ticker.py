import feedparser
from flask import Blueprint, request, Response
from urllib.parse import urlencode
from email.utils import format_datetime
from datetime import datetime

ticker_bp = Blueprint("ticker", __name__)

def make_rss_url(url: str) -> str:
    """
    Se for um link normal do Google News, converte para formato RSS.
    """
    if "news.google.com" in url and "output=rss" not in url:
        # Extrai idioma e país se existirem
        if "hl=" not in url:
            url += "&hl=pt-BR"
        if "gl=" not in url:
            url += "&gl=BR"
        if "ceid=" not in url:
            url += "&ceid=BR:pt-419"

        # Força saída RSS
        if "?" in url:
            url += "&output=rss"
        else:
            url += "?output=rss"

    return url

@ticker_bp.route("/convert", methods=["GET"])
def convert_to_rss():
    url = request.args.get("url")
    if not url:
        return Response("<error>URL is required</error>", mimetype="application/xml", status=400)

    try:
        rss_url = make_rss_url(url)
        feed = feedparser.parse(rss_url)

        if not feed.entries:
            return Response("<error>Não foi possível gerar RSS válido.</error>", mimetype="application/xml", status=400)

        rss_items = []
        for entry in feed.entries:
            pub_date = format_datetime(
                datetime(*entry.published_parsed[:6])
            ) if hasattr(entry, "published_parsed") else format_datetime(datetime.utcnow())

            rss_items.append(f"""
                <item>
                    <title>{entry.get("title", "Sem título")}</title>
                    <link>{entry.get("link", "")}</link>
                    <description>{entry.get("summary", "")}</description>
                    <pubDate>{pub_date}</pubDate>
                </item>
            """)

        rss_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>{feed.feed.get("title", "Feed convertido")}</title>
                <link>{feed.feed.get("link", url)}</link>
                <description>{feed.feed.get("description", "RSS feed convertido")}</description>
                <lastBuildDate>{format_datetime(datetime.utcnow())}</lastBuildDate>
                {''.join(rss_items)}
            </channel>
        </rss>"""

        return Response(rss_xml, mimetype="application/rss+xml")

    except Exception as e:
        return Response(f"<error>{str(e)}</error>", mimetype="application/xml", status=500)
