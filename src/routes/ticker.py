import feedparser
from flask import Blueprint, request, Response
from urllib.parse import urljoin
from email.utils import format_datetime
from datetime import datetime

ticker_bp = Blueprint("ticker", __name__)

@ticker_bp.route("/convert", methods=["GET"])
def convert_to_rss():
    url = request.args.get("url")
    if not url:
        return Response("<error>URL is required</error>", mimetype="application/xml", status=400)

    try:
        feed = feedparser.parse(url)

        # Base do Google News (para corrigir os links ./read/...)
        base_link = "https://news.google.com"

        rss_items = []
        for entry in feed.entries:
            # Corrige link relativo -> absoluto
            raw_link = entry.get("link", "")
            link = urljoin(base_link, raw_link)

            # Usa published_parsed ou updated_parsed, senão UTC atual
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                pub_date = format_datetime(datetime(*entry.published_parsed[:6]))
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                pub_date = format_datetime(datetime(*entry.updated_parsed[:6]))
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
                <title>{feed.feed.get("title", "Feed convertido")}</title>
                <link>{feed.feed.get("link", base_link)}</link>
                <description>{feed.feed.get("description", "RSS feed convertido")}</description>
                <lastBuildDate>{format_datetime(datetime.utcnow())}</lastBuildDate>
                {''.join(rss_items)}
            </channel>
        </rss>"""

        return Response(rss_xml, mimetype="application/rss+xml")

    except Exception as e:
        return Response(f"<error>{str(e)}</error>", mimetype="application/xml", status=500)
