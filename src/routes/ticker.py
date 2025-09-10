from flask import Blueprint, Response, request
import requests
from bs4 import BeautifulSoup

ticker_bp = Blueprint("ticker", __name__)

@ticker_bp.route("/convert", methods=["GET"])
def convert():
    url = request.args.get("url")

    if not url:
        return {"success": False, "error": "Parâmetro ?url= não fornecido"}, 400

    try:
        # Faz a requisição ao Google News
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        # Extrai títulos e links básicos
        items = []
        for link in soup.find_all("a", href=True)[:10]:
            title = link.get_text(strip=True)
            href = link["href"]

            if href.startswith("./"):
                href = "https://news.google.com" + href[1:]

            if title and href:
                items.append({"title": title, "link": href})

        # Monta RSS XML
        rss_items = ""
        for item in items:
            rss_items += f"""
                <item>
                    <title>{item['title']}</title>
                    <link>{item['link']}</link>
                </item>
            """

        rss_feed = f"""<?xml version="1.0" encoding="UTF-8" ?>
            <rss version="2.0">
                <channel>
                    <title>Google News RSS</title>
                    <link>{url}</link>
                    <description>Feed convertido do Google News</description>
                    {rss_items}
                </channel>
            </rss>
        """

        return Response(rss_feed, mimetype="application/rss+xml")

    except Exception as e:
        return {"success": False, "error": str(e)}, 500
