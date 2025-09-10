from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
import hashlib
import json
import os

router = APIRouter()

# Pasta onde vamos salvar os tickers temporários
TICKER_STORAGE = "storage/tickers"
os.makedirs(TICKER_STORAGE, exist_ok=True)

@router.post("/api/news/ticker")
async def generate_ticker(request: Request):
    body = await request.json()
    items = body.get("items", [])

    if not items:
        return {"success": False, "error": "Nenhuma notícia encontrada"}

    # Gera um ID único baseado no conteúdo
    ticker_id = hashlib.md5(json.dumps(items).encode()).hexdigest()

    # Salva em JSON para poder usar no embed
    filepath = os.path.join(TICKER_STORAGE, f"{ticker_id}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False)

    # URL final do ticker
    ticker_url = f"/embed/ticker/{ticker_id}"
    return {"success": True, "url": ticker_url}


@router.get("/embed/ticker/{ticker_id}", response_class=HTMLResponse)
async def embed_ticker(ticker_id: str):
    filepath = os.path.join(TICKER_STORAGE, f"{ticker_id}.json")

    if not os.path.exists(filepath):
        return HTMLResponse("<h3>❌ Ticker não encontrado</h3>", status_code=404)

    with open(filepath, "r", encoding="utf-8") as f:
        items = json.load(f)

    # Gera HTML com ticker animado
    html_content = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>Ticker de Notícias</title>
        <style>
            body {{
                margin: 0;
                overflow: hidden;
            }}
            .ticker {{
                background: black;
                color: white;
                font-family: Arial, sans-serif;
                white-space: nowrap;
                overflow: hidden;
                box-sizing: border-box;
                width: 100%;
                height: 40px;
                line-height: 40px;
            }}
            .ticker-content {{
                display: inline-block;
                padding-left: 100%;
                animation: scroll 40s linear infinite;
            }}
            @keyframes scroll {{
                0% {{ transform: translateX(0); }}
                100% {{ transform: translateX(-100%); }}
            }}
            .news-item {{
                margin-right: 60px;
                color: #fff;
            }}
            .source {{
                color: #00bfff;
                font-weight: bold;
                margin-right: 5px;
            }}
        </style>
    </head>
    <body>
        <div class="ticker">
            <div class="ticker-content">
                {''.join([f"<span class='news-item'><span class='source'>{i['source']}</span>{i['title']}</span>" for i in items])}
            </div>
        </div>
    </body>
    </html>
    """

    return HTMLResponse(html_content)
