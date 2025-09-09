from flask import Blueprint, request, jsonify
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse, parse_qs
import xml.etree.ElementTree as ET
from datetime import datetime

news_bp = Blueprint('news', __name__)

@news_bp.route('/convert', methods=['POST'])
def convert_news_to_rss():
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL é obrigatória'}), 400
        
        print(f"Processando URL: {url}")
        
        # Extrair notícias do Google News
        news_items = extract_news_from_google(url)
        
        print(f"Notícias extraídas: {len(news_items)}")
        
        if not news_items:
            return jsonify({'error': 'Não foi possível extrair notícias da URL fornecida'}), 400
        
        # Gerar RSS feed
        rss_content = generate_rss_feed(news_items)
        
        return jsonify({
            'success': True,
            'rss': rss_content,
            'items': news_items
        })
        
    except Exception as e:
        print(f"Erro no processamento: {str(e)}")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

def extract_news_from_google(url):
    """Extrai notícias do Google News"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        print(f"Fazendo requisição para: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        news_items = []
        
        # Buscar artigos na página do Google News - múltiplas estratégias
        articles = soup.find_all('article')
        
        if not articles:
            # Tentar outras estratégias de busca
            articles = soup.find_all('div', {'class': re.compile(r'.*article.*', re.I)})
        
        if not articles:
            # Buscar por links de notícias
            articles = soup.find_all('a', href=True)
        
        print(f"Encontrados {len(articles)} elementos para processar")
        
        for i, article in enumerate(articles[:15]):  # Limitar a 15 elementos
            try:
                # Estratégias múltiplas para extrair título
                title = None
                
                # Estratégia 1: h3, h4, h2
                title_elem = article.find(['h3', 'h4', 'h2'])
                if title_elem:
                    title = title_elem.get_text(strip=True)
                
                # Estratégia 2: texto do próprio elemento se for link
                if not title and article.name == 'a':
                    title = article.get_text(strip=True)
                
                # Estratégia 3: buscar em spans ou divs filhos
                if not title:
                    text_elem = article.find(['span', 'div'])
                    if text_elem:
                        title = text_elem.get_text(strip=True)
                
                # Extrair link
                link = ''
                if article.name == 'a':
                    link = article.get('href', '')
                else:
                    link_elem = article.find('a')
                    if link_elem:
                        link = link_elem.get('href', '')
                
                # Extrair fonte - múltiplas estratégias
                source = 'Google News'
                source_patterns = [
                    {'data-n-tid': True},
                    {'class': re.compile(r'.*source.*', re.I)},
                    {'class': re.compile(r'.*author.*', re.I)}
                ]
                
                for pattern in source_patterns:
                    source_elem = article.find('div', pattern) or article.find('span', pattern)
                    if source_elem:
                        source_text = source_elem.get_text(strip=True)
                        if source_text and len(source_text) < 50:
                            source = source_text
                            break
                
                # Extrair tempo
                time_elem = article.find('time')
                pub_date = 'Agora'
                if time_elem:
                    pub_date = time_elem.get_text(strip=True)
                
                # Validar e adicionar notícia
                if title and len(title) > 10 and len(title) < 200:
                    news_items.append({
                        'title': title,
                        'link': link,
                        'source': source,
                        'pub_date': pub_date,
                        'description': f'{title} - {source}'
                    })
                    print(f"Notícia {len(news_items)}: {title[:50]}...")
                    
            except Exception as e:
                print(f"Erro ao processar artigo {i}: {e}")
                continue
        
        # Se não encontrou notícias, tentar estratégia alternativa
        if not news_items:
            print("Tentando estratégia alternativa...")
            # Buscar por qualquer texto que pareça título de notícia
            all_text = soup.get_text()
            lines = [line.strip() for line in all_text.split('\n') if line.strip()]
            
            for line in lines[:20]:
                if len(line) > 20 and len(line) < 150 and not line.startswith('http'):
                    news_items.append({
                        'title': line,
                        'link': url,
                        'source': 'Google News',
                        'pub_date': 'Agora',
                        'description': line
                    })
                    if len(news_items) >= 5:
                        break
        
        print(f"Total de notícias extraídas: {len(news_items)}")
        return news_items
        
    except Exception as e:
        print(f"Erro ao extrair notícias: {e}")
        return []

def generate_rss_feed(news_items):
    """Gera um feed RSS a partir das notícias"""
    try:
        # Criar elemento raiz RSS
        rss = ET.Element('rss', version='2.0')
        channel = ET.SubElement(rss, 'channel')
        
        # Metadados do canal
        ET.SubElement(channel, 'title').text = 'Google News Feed'
        ET.SubElement(channel, 'description').text = 'Feed de notícias convertido do Google News'
        ET.SubElement(channel, 'link').text = 'https://news.google.com'
        ET.SubElement(channel, 'lastBuildDate').text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
        
        # Adicionar itens de notícias
        for item_data in news_items:
            item = ET.SubElement(channel, 'item')
            ET.SubElement(item, 'title').text = item_data['title']
            ET.SubElement(item, 'link').text = item_data['link']
            ET.SubElement(item, 'description').text = item_data['description']
            ET.SubElement(item, 'source').text = item_data['source']
            ET.SubElement(item, 'pubDate').text = item_data['pub_date']
        
        # Converter para string
        rss_string = ET.tostring(rss, encoding='unicode')
        return f'<?xml version="1.0" encoding="UTF-8"?>\n{rss_string}'
        
    except Exception as e:
        print(f"Erro ao gerar RSS: {e}")
        return None

