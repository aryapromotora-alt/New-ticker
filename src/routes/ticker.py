import feedparser
from flask import Blueprint, request, Response
from urllib.parse import urljoin
from email.utils import format_datetime
from datetime import datetime

# Cria o Blueprint
ticker_bp = Blueprint("ticker", __name__)

# Endpoint de conversão RSS
@ticker_bp.route("/convert", methods=["GET"])
def convert_to_rss():
    url = request.args.get("url")
    if not url:
        return Response("<error>URL is required</error>", mimetype="application/xml", status=400)

    try:
        feed = feedparser.parse(url)

        # Cabeçalho do XML RSS
        rss_items = []
        for entry in feed.entries:
            # Constrói link absoluto (caso venha ./read/...)
            link = urljoin(feed.feed.get("link", url), entry.get("link", ""))

            # pubDate formatado para padrão RSS
            if "published_parsed" in entry and entry.published_parsed:
                pub_date = format_datetime(datetime(*entry.published_parsed[:6]))
            else:
                pub_date = format_datetime(datetime.utcnow())

            rss_items.append(f"""
                <item>
                    <title>{entry.get("title", "Sem título")}</title>
                    <link>{link}</link>
                    <description>{entry.get("summary", "")}</description>
                    <pubDate>{pub_date}</pubDate>
                </item>
            """)

        rss_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>{feed.feed.get("title", "No title")}</title>
                <link>{feed.feed.get("link", url)}</link>
                <description>{feed.feed.get("description", "RSS feed convertido")}</description>
                <lastBuildDate>{format_datetime(datetime.utcnow())}</lastBuildDate>
                {''.join(rss_items)}
            </channel>
        </rss>"""

        return Response(rss_xml, mimetype="application/rss+xml")

    except Exception as e:
        return Response(f"<error>{str(e)}</error>", mimetype="application/xml", status=500)
