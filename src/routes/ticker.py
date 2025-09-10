import feedparser
from flask import Blueprint, request, Response
from urllib.parse import urljoin
from email.utils import format_datetime
from datetime import datetime, timezone

ticker_bp = Blueprint("ticker", __name__)

@ticker_bp.route("/convert", methods=["GET"])
def convert_to_rss():
    url = request.args.get("url")
    if not url:
        return Response("<error>URL is required</error>", mimetype="application/xml", status=400)

    try:
        feed = feedparser.parse(url)
        base_link = "https://news.google.com"  # corrige ./read/...

        rss_items = []
        for entry in feed.entries:
            # Corrige link relativo
            link = urljoin(base_link, entry.get("link", ""))

            # PubDate sempre em UTC RFC 822
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                pub_date = format_datetime(datetime(*entry.published_parsed[:6], tzinfo=timezone.utc))
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                pub_date = format_datetime(datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc))
            else:
                pub_date = format_datetime(datetime.now(timezone.utc))

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
                <lastBuildDate>{format_datetime(datetime.now(timezone.utc))}</lastBuildDate>
                {''.join(rss_items)}
            </channel>
        </rss>"""

        return Response(rss_xml, mimetype="application/rss+xml")

    except Exception as e:
        return Response(f"<error>{str(e)}</error>", mimetype="application/xml", status=500)
