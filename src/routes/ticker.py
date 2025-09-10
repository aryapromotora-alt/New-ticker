import requests
import feedparser
from flask import Blueprint, request, jsonify

# Cria o Blueprint
ticker_bp = Blueprint("ticker", __name__)

# Endpoint de conversão RSS
@ticker_bp.route("/convert", methods=["GET"])
def convert_to_rss():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "URL is required"}), 400

    try:
        feed = feedparser.parse(url)
        items = []
        for entry in feed.entries:
            items.append({
                "title": entry.get("title"),
                "link": entry.get("link"),
                "published": entry.get("published", "")
            })

        return jsonify({
            "feed_title": feed.feed.get("title", "No title"),
            "feed_link": feed.feed.get("link", ""),
            "items": items
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
