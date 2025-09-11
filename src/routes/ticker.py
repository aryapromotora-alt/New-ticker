import feedparser
import requests
from flask import Blueprint, request, Response
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode, urljoin
from email.utils import format_datetime
from datetime import datetime
from xml.sax.saxutils import escape

ticker_bp = Blueprint("ticker", __name__)

def make_rss_url(url: str) -> str:
    """
    Converte URLs do Google News para o formato /rss/...
    Ex:
    https://news.google.com/topics/CAAq.../sections/CAQi...
    -> https://news.google.com/rss/topics/CAAq.../sections/CAQi...?hl=pt-BR&gl=BR&ceid=BR:pt-419
    """
    parsed = urlparse(url)
    netloc = parsed.netloc or "news.google.com"
    scheme = parsed.scheme or "https"
    path = parsed.path or "/"

    # se já for rss, apenas ajusta query
    if path.startswith("/rss"):
        rss_path = path
    else:
        # coloca /rss antes do path
        # evita duplicar /rss se o usuário já colocou
        rss_path = "/rss" + path

    qs = parse_qs(parsed.query)
    # defaults (modifique se quiser outros padrões)
    qs.setdefault("hl", ["pt-BR"])
    qs.setdefault("gl", ["BR"])
    qs.setdefault("ceid", ["BR:pt-419"])

    new_query = urlencode(qs, doseq=True)
    rss_url = urlunparse((scheme, netloc, rss_path, "", new_query, ""))

    return rss_url

@ticker_bp.route("/convert", methods=["GET"])
def convert_to_rss():
    url = request.args.get("url")
    if not url:
        return Response("<error>URL is required</error>", mimetype="application/xml", status=400)

    try:
        rss_url = make_rss_url(url)

        # buscar com User-Agent para evitar respostas em HTML
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        }
        resp = requests.get(rss_url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return Response(f"<error>Erro ao buscar RSS ({resp.status_code})</error>",
                            mimetype="application/xml", status=502)

        feed = feedparser.parse(resp.content)

        if not feed.entries:
            return Response("<error>Não foi possível gerar RSS válido.</error>",
                            mimetype="application/xml", status=400)

        rss_items = []
        base = f"{urlparse(rss_url).scheme}://{urlparse(rss_url).netloc}"

        for entry in feed.entries:
            # link absoluto (alguns itens têm "./read/..." no Google News)
            raw_link = entry.get("link", "")
            link = urljoin(base, raw_link)

            # pubDate
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                pub_date = format_datetime(datetime(*entry.published_parsed[:6]))
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                pub_date = format_datetime(datetime(*entry.updated_parsed[:6]))
            else:
                pub_date = format_datetime(datetime.utcnow())

            title = escape(entry.get("title", "Sem título"))
            description = escape(entry.get("summary", "") or entry.get("description", ""))
            source = escape(entry.get("source", "") if isinstance(entry.get("source"), str) else "")

            rss_items.append(f"""
                <item>
                    <title>{title}</title>
                    <link>{escape(link)}</link>
                    <description>{description}</description>
                    <pubDate>{pub_date}</pubDate>
                </item>
            """)

        rss_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>{escape(feed.feed.get("title", "Feed convertido"))}</title>
                <link>{escape(feed.feed.get("link", url))}</link>
                <description>{escape(feed.feed.get("description", "RSS feed convertido"))}</description>
                <lastBuildDate>{format_datetime(datetime.utcnow())}</lastBuildDate>
                {''.join(rss_items)}
            </channel>
        </rss>"""

        return Response(rss_xml, mimetype="application/rss+xml")

    except Exception as e:
        return Response(f"<error>{escape(str(e))}</error>", mimetype="application/xml", status=500)
