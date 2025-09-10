import requests
import feedparser
from flask import Blueprint, request, Response
from bs4 import BeautifulSoup
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
        # Caso seja um link de feed válido (termina com /rss)
        if url.endswith("/rss"):
            feed = feedparser.parse(url)

            rss_items = []
            for entry in feed.entries:
                link = entry.get("link", "")
                if not link.startswith("http"):
                    link = urljoin(url, link)

                if hasattr(entry, "published_parsed") and entry.published_parsed:
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
                    <title>{feed.feed.get("title", "Google News RSS")}</title>
                    <link>{feed.feed.get("link", url)}</link>
                    <description>{feed.feed.get("description", "RSS feed convertido")}</description>
                    <lastBuildDate>{format_datetime(datetime.utcnow())}</lastBuildDate>
                    {''.join(rss_items)}
                </channel>
            </rss>"""

            return Response(rss_xml, mimetype="application/rss+xml")

        # Caso contrário, é página HTML → scraping
        else:
            response = requests.get(url)
            if response.status_code != 200:
                return Response(f"<error>Erro ao acessar URL: {response.status_code}</error>", mimetype="application/xml", status=500)

            soup = BeautifulSoup(response.text, "lxml")
            articles = soup.select("article h3 a")

            rss_items = []
            for a in articles:
                title = a.get_text(strip=True)
                link = urljoin("https://news.google.com", a.get("href"))

                rss_items.append(f"""
                    <item>
                        <title>{title}</title>
                        <link>{link}</link>
                        <description>{title}</description>
                        <pubDate>{format_datetime(datetime.utcnow())}</pubDate>
                    </item>
                """)

            rss_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
            <rss version="2.0">
                <channel>
                    <title>Google News Página Convertida</title>
                    <link>{url}</link>
                    <description>RSS gerado a partir de {url}</description>
                    <lastBuildDate>{format_datetime(datetime.utcnow())}</lastBuildDate>
                    {''.join(rss_items)}
                </channel>
            </rss>"""

            return Response(rss_xml, mimetype="application/rss+xml")

    except Exception as e:
        return Response(f"<error>{str(e)}</error>", mimetype="application/xml", status=500)
