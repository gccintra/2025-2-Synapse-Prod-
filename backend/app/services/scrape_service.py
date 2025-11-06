import os
import json
import logging
from datetime import datetime
from typing import Dict, Optional
import re
from urllib.parse import urlparse, urljoin

from bs4 import BeautifulSoup
import bleach
from newspaper import Article, Config
from newspaper.exceptions import ArticleException
import requests
import html # Importar para desescapar entidades HTML
from app.utils.scraping_blacklist import ScrapingBlacklist


class ScrapeService:
    """Serviço de scraping inteligente usando newspaper4k"""
    
    # Tags que realmente importam para conteúdo
    TAGS_PERMITIDAS = {
        'p', 'br',
        'strong', 'b', 'em', 'i',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ul', 'ol', 'li',
        'blockquote',
        'a', 'img',
        'figure', 'figcaption',
        'iframe',  # Mantém iframes (vídeos, tweets, etc)
        'div'  # Mantém divs (necessário para carrosséis e estrutura)
    }

    # Atributos necessários para conteúdo embarcado
    ATRIBUTOS_PERMITIDOS = {
        'a': ['href', 'target'],
        'img': ['src', 'alt', 'width', 'height', 'srcset', 'sizes'],
        'iframe': ['src', 'width', 'height', 'frameborder', 'allowfullscreen', 'allow'],
        'div': ['class', 'data-video-id', 'data-tweet-id']  # Permite class e data-video-id para placeholders
    }

    PALAVRAS_CHAVE_DE_FALHA = [
        'access denied',
        'permission denied',
        'error 403',
        'error 404',
        'page not found',
        'blocked',
        'captcha',
        'javascript required',
        'enable javascript',
        'cookies required',
        'accept cookies'
    ]
    
    # Tags que devem ser completamente removidas (incluindo conteúdo)
    TAGS_PARA_REMOVER = {
        'script', 'style', 'noscript',
        'form', 'input', 'button', 'select', 'textarea',
        'nav', 'header', 'footer', 'aside',
    }
    
    # Domínios de iframe permitidos (vídeos, social media)
    IFRAME_WHITELIST = {
        'youtube.com',
        'youtu.be',
        'youtube-nocookie.com',
        'twitter.com',
        'x.com',
        'platform.twitter.com',
        'instagram.com',
        'vimeo.com',
        'dailymotion.com',
        'twitch.tv',
        'player.twitch.tv',
        'soundcloud.com',
        'spotify.com',
        'tiktok.com',
        'facebook.com',
        'fb.watch'
    }
    
    def __init__(self, blacklist: ScrapingBlacklist):
        self.blacklist = blacklist
        
        # Configuração do newspaper4k
        self.config = Config()
        self.config.browser_user_agent = (
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/128.0.0.0 Safari/537.36'
        )
        self.config.keep_article_html = True
        self.config.fetch_images = False
        self.config.clean_article_html = False
        self.config.memoize_articles = False
        self.config.request_timeout = 15
        
    def scrape_article_content(self, url: str) -> Optional[Dict[str, str]]:
        try:
            # Verificar blacklist
            if self.blacklist.is_blocked(url):
                blocked_info = self.blacklist.get_blocked_info(url)
                reason = blocked_info.get('reason', 'N/A') if blocked_info else 'N/A'
                logging.warning(
                    f"Site bloqueado pela blacklist: {url} "
                    f"(motivo: {reason})"
                )
                return None
            
            logging.info(f"Iniciando scraping para: {url}")

            
            # Usar newspaper4k para baixar e parsear
            article = Article(url, config=self.config)
            article.download()
            article.parse()
            
            # Extrair texto em linguagem natural
            article_text = article.text
            if not article_text or len(article_text.strip()) < 100:
                logging.warning(f"Texto extraído muito curto ou vazio para {url}")
                self._add_to_blacklist(
                    url=url,
                    error_type='Empty Content',
                    error_message='Texto extraído muito curto',
                    reason='Conteúdo vazio ou insuficiente'
                )
                return None
            
            # Extrair HTML do top_node
            if article.top_node is None:
                logging.warning(f"newspaper4k não identificou top_node para {url}")
                self._add_to_blacklist(
                    url=url,
                    error_type='No Top Node',
                    error_message='Top node não identificado',
                    reason='Estrutura HTML não reconhecida'
                )
                return None
                        
            # Converter top_node para HTML string
            from lxml.etree import tostring
            try:
                raw_html = tostring(article.top_node, encoding='unicode', method='html')
            except Exception as e:
                raise ArticleException(f"Falha ao converter top_node para HTML: {e}")
            
            # Processar HTML com limpeza agressiva
            processed_html = self._process_html_aggressive(raw_html, url)
            
            # Validar conteúdo extraído
            if not self._validar_conteudo_extraido(processed_html):
                logging.warning(f"Validação de conteúdo falhou para {url}")
                self._add_to_blacklist(
                    url=url,
                    error_type='Content Validation Failed',
                    error_message='Conteúdo contém palavras-chave de falha',
                    reason='Conteúdo bloqueado ou inválido'
                )
                return None
            
            # Inserir a galeria de mídia no início do HTML processado
            
            logging.info(
                f"✓ Scraping bem-sucedido: {url} "
                f"({len(article_text)} chars text, {len(processed_html)} chars HTML)"
            )
            
            return {
                'html': processed_html,
                'raw_html': raw_html,
                'text': article_text,
                'title': article.title or 'Sem título',
                'authors': article.authors or [],
                'publish_date': article.publish_date.isoformat() if article.publish_date else None
            }
            
        except requests.exceptions.Timeout:
            error_msg = "Request timeout"
            logging.error(f"Timeout ao acessar {url}")
            self._add_to_blacklist(
                url=url,
                error_type='Timeout Error',
                error_message=error_msg,
                reason='Site demorou muito para responder'
            )
            return None
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Request error: {str(e)}"
            logging.error(f"Erro de requisição para {url}: {error_msg}")
            self._add_to_blacklist(
                url=url,
                error_type='Request Error',
                error_message=error_msg,
                reason='Erro ao fazer requisição HTTP'
            )
            return None
        
        except AttributeError as e:
            error_msg = f"Attribute error: {str(e)}"
            logging.error(f"Erro de atributo para {url}: {error_msg}")
            self._add_to_blacklist(
                url=url,
                error_type='Parse Error',
                error_message=error_msg,
                reason='Erro ao parsear estrutura do artigo'
            )
            return None
        
        except ArticleException as e:
            error_msg = f"Newspaper error: {str(e)}"
            logging.error(f"Erro do Newspaper4k para {url}: {error_msg}")
            self._add_to_blacklist(
                url=url,
                error_type='Article Exception',
                error_message=error_msg,
                reason='Falha no download ou parse do artigo'
            )
            
        except Exception as e:
            error_msg = str(e)
            logging.error(f"Erro no scraping de {url}: {error_msg}", exc_info=True)
            return None

    def _process_html_aggressive(self, html: str, base_url: str) -> str:
        """
        Processa HTML com limpeza agressiva: remove scripts, styles, classes, ids, etc.
        
        Args:
            html: HTML bruto
            base_url: URL base para resolver caminhos relativos
            
        Returns:
            HTML limpo, apenas com conteúdo relevante
        """
        # Parse com BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        # 1. REMOVER tags indesejadas (scripts, styles, etc.)
        for tag_name in self.TAGS_PARA_REMOVER:
            for tag in soup.find_all(tag_name):
                tag.decompose()


        # 3. SANITIZAR E PADRONIZAR EMBEDS
        self._sanitize_twitter_embeds(soup)
        self._sanitize_youtube_embeds(soup)
        self._filter_iframes(soup, base_url)

        

        for tag in list(soup.find_all(['div', 'p', 'figure'])):
            
            # --- 1. Lógica de "Loading" ---
            text_content = tag.get_text(strip=True).lower()
            
            # Se o conteúdo for muito curto (provavelmente só "Loading...")
            # E contiver a palavra-chave. 
            if len(text_content) < 30 and any(keyword in text_content for keyword in [
                'loading', 
                'disclaimer', 
                'read more', 
                'see also', 
                'photo by',
                'Advertisement'
            ]):
                tag.decompose()
                continue
            
            # --- 2. Lógica de remoção de Figure sem imagem real ---
           # if tag.name == 'figure':
           #      Remove se a figure não tiver um elemento de imagem que contenha src
           #     if not tag.find('img', src=True):
           #         tag.decompose()
           #         continue


        # 2. REMOVER elementos por classe/id comuns de ads e menus
        unwanted_selectors = [
            {'class': lambda x: x and (
                # Normaliza 'x' para ser uma string de classes
                class_str := (' '.join(x) if isinstance(x, list) else x).lower()
            ) and any(
                keyword in class_str
                for keyword in [
                    'ad-', 'advertisement', 'banner', 'promo',
                    'newsletter', 'sidebar', 'widget', 'comment',
                    'social-share', 'share-button',
                    'related-posts', 'recommendation',
                    'cookie', 'popup', 'modal', 'overlay', 'video', 'related'
                ]
            ) and not any(
                good_keyword in class_str
                for good_keyword in [
                    'carousel', 'slider', 'swiper',
                    'lightbox', 'image-container', 'gallery'
                ]
            )},
            {'id': lambda x: x and any(
                keyword in x.lower()
                for keyword in [
                    'ad-', 'advertisement', 'banner', 'comment', 'sidebar'
                ]
            )}
        ]
        
        for selector in unwanted_selectors:
            for element in soup.find_all(attrs=selector):
                element.decompose()


        # 4. LIDAR COM IMAGENS "LAZY-LOADING" E PLACEHOLDERS
        for img in list(soup.find_all('img')): 
            
            # Padrão 1: Promover 'data-' atributos.
            # Se 'data-src' existir, ele tem prioridade sobre o 'src' (que pode ser 1x1.gif)
            if img.has_attr('data-src'):
                img['src'] = img['data-src']
            if img.has_attr('data-srcset'):
                img['srcset'] = img['data-srcset']
            if img.has_attr('data-sizes'):
                img['sizes'] = img['data-sizes']

            # Padrão 2: Se 'src' ainda for placeholder (ou não existir), verificar <noscript>
            src_lower = img.get('src', '').lower()
            is_placeholder = not src_lower or any(p in src_lower for p in [
                '1x1.trans.gif', 'pixel.gif', 'blank.gif', 
                'spacer.gif', 'data:image/gif;base64'
            ])

            if is_placeholder:
                noscript = img.find_next_sibling('noscript')
                if noscript:
                    # Parsear o conteúdo do noscript para encontrar a img de fallback
                    noscript_content = "".join(map(str, noscript.contents))
                    noscript_soup = BeautifulSoup(noscript_content, 'html.parser')
                    noscript_img = noscript_soup.find('img')
                    
                    if noscript_img:
                        # Substituir os atributos da img "lazy" pelos do noscript
                        if noscript_img.has_attr('src'):
                            img['src'] = noscript_img['src']
                        if noscript_img.has_attr('srcset'):
                            img['srcset'] = noscript_img['srcset']
                        if noscript_img.has_attr('sizes'):
                            img['sizes'] = noscript_img['sizes']
                        
                        # Recalcular is_placeholder, pois podemos ter pego um 'src' válido
                        src_lower = img.get('src', '').lower()
                        is_placeholder = not src_lower or any(p in src_lower for p in [
                            '1x1.trans.gif', 'pixel.gif', 'blank.gif', 
                            'spacer.gif', 'data:image/gif;base64'
                        ])

            # Padrão 3: Se, depois de tudo, ainda for placeholder, remover.
            if is_placeholder:
                img.decompose()
                continue
            
            # Padrão 4: Otimizar o 'src' principal.
            # Se tivermos um srcset, vamos usá-lo para encontrar a MELHOR
            # URL e forçá-la no 'src', sobrescrevendo o 'src' de baixa resolução (ex: 400x0)
            if img.has_attr('srcset'):
                srcset = img['srcset']
                max_width = 0
                best_url = None
                
                # Tentar extrair a largura da 'src' atual para comparação
                current_src_width = 0
                src_match = re.search(r'/(\d+)x\d+/', img.get('src', ''))
                if src_match:
                    current_src_width = int(src_match.group(1))

                # Parsear o srcset
                sources = srcset.split(',')
                for source in sources:
                    parts = source.strip().split()
                    if len(parts) >= 2:
                        url = parts[0]
                        width_str = parts[-1].replace('w', '') # Pega '800' de '800w'
                        if width_str.isdigit():
                            width = int(width_str)
                            if width > max_width:
                                max_width = width
                                best_url = url
                
                # Se encontramos uma URL no srcset que é melhor que a 'src' atual
                if best_url and max_width > current_src_width:
                    img['src'] = best_url
    
        # 4. CONSERTAR caminhos relativos em imagens e links restantes
        for img in soup.find_all('img', src=True):
            img['src'] = urljoin(base_url, img['src'])
        
        for link in soup.find_all('a', href=True):
            link['href'] = urljoin(base_url, link['href'])
        
        # 5. LIMPAR atributos de todas as tags, mantendo apenas os essenciais
        for tag in soup.find_all(True):
            # Pular tags inválidas
            if not tag or not hasattr(tag, 'attrs') or tag.attrs is None:
                continue
                
            attrs_to_keep = {}
            
            if tag.name == 'a':
                if 'href' in tag.attrs:
                    attrs_to_keep['href'] = tag['href']
                if 'target' in tag.attrs:
                    attrs_to_keep['target'] = tag['target']
            
            elif tag.name == 'img':
                if 'src' in tag.attrs:
                    attrs_to_keep['src'] = tag['src']
                if 'alt' in tag.attrs:
                    attrs_to_keep['alt'] = tag['alt']
                if 'width' in tag.attrs:
                    attrs_to_keep['width'] = tag['width']
                if 'height' in tag.attrs:
                    attrs_to_keep['height'] = tag['height']
            
            elif tag.name == 'iframe':
                # Manter atributos importantes de iframes
                for attr in ['src', 'width', 'height', 'frameborder', 'allowfullscreen', 'allow']:
                    if attr in tag.attrs:
                        attrs_to_keep[attr] = tag[attr]

            elif tag.name == 'div':
                # Verificação robusta de classes (lida com string ou lista)
                classes = tag.get('class', [])
                if isinstance(classes, str):
                    classes = classes.split()  # Garante que 'classes' seja uma lista

                is_twitter_placeholder = 'twitter-placeholder' in classes
                is_youtube_placeholder = 'youtube-placeholder' in classes
        
                if(is_twitter_placeholder):
                    print(f"PRIMEIRO E UM TWITTEWR PLACEHOLDER OLHA A TAG: {tag}")

                if(is_youtube_placeholder):
                    print(f"PRIMEIRO E UM YOUTUBE PLACEHOLDER OLHA A TAG: {tag}")
                
                if is_youtube_placeholder:
                    # Preservar explicitamente class e data-video-id para o placeholder do YouTube
                    if 'class' in tag.attrs:
                        attrs_to_keep['class'] = tag['class']
                    if 'data-video-id' in tag.attrs:
                        attrs_to_keep['data-video-id'] = tag['data-video-id']
                elif is_twitter_placeholder:
                    # Preservar explicitamente class e data-tweet-id para o placeholder do Twitter
                    if 'class' in tag.attrs:
                        attrs_to_keep['class'] = tag['class']
                    if 'data-tweet-id' in tag.attrs:
                        attrs_to_keep['data-tweet-id'] = tag['data-tweet-id']
                else:
                    # Lógica existente para outros divs (carrosséis, galleries, etc.)
                    if 'class' in tag.attrs:
                        classes = tag['class'] if isinstance(tag['class'], list) else [tag['class']]
                        # Manter apenas classes que parecem úteis
                        useful_classes = [
                            c for c in classes 
                            if any(keyword in c.lower() for keyword in [
                                'carousel', 'slider', 'gallery', 'swiper',
                                'image', 'video', 'content', 'article'
                            ])
                        ]
                        if useful_classes:
                            attrs_to_keep['class'] = useful_classes
            
            # Aplicar atributos limpos
            tag.attrs = attrs_to_keep
        
        # 6. REMOVER tags vazias recursivamente (exceto img, iframe, br)
        changed = True
        while changed:
            changed = False
            for tag in soup.find_all(True):
                # Pular tags que já foram removidas ou estão inválidas
                if not tag or not hasattr(tag, 'attrs') or tag.attrs is None:
                    continue
                    
                # Verificação robusta de classes (lida com string ou lista)
                classes = tag.get('class', [])
                if isinstance(classes, str):
                    classes = classes.split()

                is_youtube_placeholder = tag.name == 'div' and 'youtube-placeholder' in classes
                is_twitter_placeholder = tag.name == 'div' and 'twitter-placeholder' in classes
 
                
                # TA REMOVENDO ANTES DISSO
                if(is_twitter_placeholder):
                    print(f"SEGUNDO E UM TWITTER PLACEHOLDER OLHA A TAG: {tag}")

                if(is_youtube_placeholder):
                    print(f"SEGUNDO E UM YOUTUBE PLACEHOLDER OLHA A TAG: {tag}")
                
                # 1. LÓGICA DE PROTEÇÃO
                # Se a tag FOR mídia ou um placeholder, PULE E NÃO FAÇA NADA.
                if tag.name in ['img', 'br', 'iframe', 'source'] or \
                   is_youtube_placeholder or is_twitter_placeholder:
                    continue

                # 2. LÓGICA DE LIMPEZA
                # (Isto só roda se a tag NÃO for protegida)

                # Verifica se a tag CONTÉM um placeholder
                has_placeholder_child = tag.find('div', class_='youtube-placeholder') or \
                                        tag.find('div', class_='twitter-placeholder')

                # Agora sim, o 'if' de remoção (o seu) funciona, pois
                # ele não está mais analisando <img>, <source>, etc.
                if not tag.get_text(strip=True) and not tag.find(['img', 'iframe', 'source']) and not has_placeholder_child:
                    print(f"TAG TA SENDO EXCLUÍDA: {tag}")
                    tag.decompose()
                    changed = True

        # 7. Converter de volta para string
        clean_html = str(soup)
        
        # 8. Sanitizar com Bleach (última camada de segurança)
        final_html = bleach.clean(
            clean_html,
            tags=self.TAGS_PERMITIDAS,
            attributes=self.ATRIBUTOS_PERMITIDOS,
            strip=True,
            strip_comments=True
        )
        
        return final_html
    
    def _sanitize_twitter_embeds(self, soup: BeautifulSoup) -> None:
        """
        Encontra embeds de tweets (iframe, divs, blockquotes) e os converte
        para placeholders padronizados. Baseado no padrão do YouTube.
        """
        tweet_ids_processados = set()

        # 1. Encontrar todos os iframes do Twitter e substituí-los por placeholders
        for iframe in soup.find_all('iframe', src=re.compile(r"twitter\.com|x\.com")):
            src = iframe.get('src', '')
            match = re.search(r"status/(\d+)", src)

            if match:
                tweet_id = match.group(1)
                if tweet_id not in tweet_ids_processados:
                    placeholder = self._create_twitter_placeholder(soup, tweet_id)
                    iframe.replace_with(placeholder)
                    tweet_ids_processados.add(tweet_id)
                else:
                    iframe.decompose()  # Remove iframe duplicado

        # 2. Encontrar divs de embed do Twitter e substituí-los por placeholders
        for twitter_div in soup.find_all('div', class_=re.compile(r'twitter-tweet|tweet-embed')):
            tweet_id = self._extract_tweet_id_from_div(twitter_div)  # (Helper)

            if tweet_id and tweet_id not in tweet_ids_processados:
                placeholder = self._create_twitter_placeholder(soup, tweet_id)
                twitter_div.replace_with(placeholder)
                tweet_ids_processados.add(tweet_id)
            elif twitter_div:
                twitter_div.decompose()  # Remove o div se for duplicado ou sem ID

        # 3. Encontrar divs com data-tweet-id (método alternativo)
        for div in soup.find_all('div', attrs={'data-tweet-id': True}):
            # Pega classes de forma robusta
            classes = div.get('class', [])
            if isinstance(classes, str):
                classes = classes.split()

            # Se já é nosso placeholder, ignora
            if 'twitter-placeholder' in classes:
                continue

            tweet_id = div.get('data-tweet-id')

            # Validação simples do ID
            if tweet_id and tweet_id.isdigit():
                if tweet_id not in tweet_ids_processados:
                    placeholder = self._create_twitter_placeholder(soup, tweet_id)
                    div.replace_with(placeholder)
                    tweet_ids_processados.add(tweet_id)
                else:
                    div.decompose()  # Remove duplicado

        # 4. Procura por blockquotes (método de embed clássico do Twitter)
        for blockquote in soup.find_all('blockquote'):
            tweet_id = self._extract_tweet_id_from_div(blockquote)  # Reutiliza o helper

            if tweet_id and tweet_id not in tweet_ids_processados:
                placeholder = self._create_twitter_placeholder(soup, tweet_id)
                print(f"PLACEHOLDER: {placeholder}")
                blockquote.replace_with(placeholder)
                #if blockquote.parent and blockquote.parent.name == 'div':
                 #   blockquote.parent.replace_with(placeholder)
               # else:
               #     blockquote.replace_with(placeholder)
                tweet_ids_processados.add(tweet_id)
            elif blockquote.find_all('a', href=re.compile(r"https?://(?:[\w-]+\.)?(?:twitter|x)\.com")):
                # Remove blockquote do Twitter sem ID válido
                blockquote.decompose()

    def _create_twitter_placeholder(self, soup: BeautifulSoup, tweet_id: str):
        """
        Cria um placeholder <div class="twitter-placeholder" data-tweet-id="...">
        para ser processado pelo frontend.
        """
        placeholder = soup.new_tag('div')
        placeholder.attrs = {'class': 'twitter-placeholder', 'data-tweet-id': tweet_id}
        return placeholder

    def _extract_tweet_id_from_div(self, twitter_div: BeautifulSoup) -> str | None:
        """Helper para extrair o tweet_id de um div com embed do Twitter."""
        # Regex para extrair o ID do tweet de uma URL
        tweet_id_re = re.compile(r"status/(\d+)")

        # Tenta pelo atributo data-tweet-id do próprio div
        tweet_id = twitter_div.get('data-tweet-id') if twitter_div else None
        if tweet_id and tweet_id.isdigit():
            return tweet_id

        # Tenta por um link interno
        link_tag = twitter_div.find('a', href=re.compile(r"https?://(?:[\w-]+\.)?(?:twitter|x)\.com")) if twitter_div else None
        if link_tag:
            href = link_tag.get('href')
            if href:
                match = tweet_id_re.search(href)
                if match:
                    return match.group(1)

        # Tenta pelo ID do próprio div (se for numérico)
        div_id = twitter_div.get('id') if twitter_div else None
        if div_id and div_id.isdigit():
            return div_id

        return None

    def _sanitize_youtube_embeds(self, soup: BeautifulSoup) -> None:
        """
        Encontra divs que são fachadas de vídeos do YouTube e os converte
        para iframes padronizados.
        """
        video_ids_processados = set()

        # 1. Encontrar todos os iframes do YouTube e substituí-los por placeholders
        for iframe in soup.find_all('iframe', src=re.compile(r"youtube\.com|youtu\.be")):
            src = iframe.get('src', '')
            match = re.search(r"(?:embed\/|v=|\/)([a-zA-Z0-9_-]{11})", src)

            if match:
                video_id = match.group(1)
                if video_id not in video_ids_processados:
                    placeholder = self._create_youtube_placeholder(soup, video_id)
                    iframe.replace_with(placeholder)
                    video_ids_processados.add(video_id)
                else:
                    iframe.decompose()  # Remove iframe duplicado

        # 2. Encontrar divs de fachada e substituí-los por placeholders
        for youtube_div in soup.find_all('div', class_=re.compile(r'youtube-video|youtube-facade')):
            video_id = self._extract_video_id_from_div(youtube_div)  # (Helper)

            if video_id and video_id not in video_ids_processados:
                placeholder = self._create_youtube_placeholder(soup, video_id)
                youtube_div.replace_with(placeholder)
                video_ids_processados.add(video_id)
            elif youtube_div:
                youtube_div.decompose()  # Remove o div se for duplicado ou sem ID

    def _create_youtube_placeholder(self, soup: BeautifulSoup, video_id: str):
        """
        Cria um placeholder <div class="youtube-placeholder" data-video-id="...">
        para ser processado pelo frontend.
        """
        placeholder = soup.new_tag('div')
        placeholder.attrs = {'class': 'youtube-placeholder', 'data-video-id': video_id}
        return placeholder

    def _extract_video_id_from_div(self, youtube_div: BeautifulSoup) -> str | None:
        """Helper para extrair o video_id de um div-fachada."""
        # Tenta pelo ID do próprio div
        video_id = youtube_div.get('id') if youtube_div else None
        if video_id and len(video_id) == 11:
            return video_id

        # Tenta por um link interno
        link_tag = youtube_div.find('a', href=re.compile(r"youtu\.be|youtube\.com")) if youtube_div else None
        if link_tag:
            href = link_tag.get('href')
            if href:
                match = re.search(r"(?:v=|\/)([a-zA-Z0-9_-]{11})", href)
                if match:
                    return match.group(1)
        return None

    def _filter_iframes(self, soup: BeautifulSoup, base_url: str) -> None:
        """
        Filtra iframes, mantendo apenas os de domínios permitidos e removendo
        os que parecem ser publicidade.
        """
        for iframe in soup.find_all('iframe'):
            src = iframe.get('src', '')
            
            is_allowed = any(domain in src.lower() for domain in self.IFRAME_WHITELIST)
            
            if not is_allowed or any(ad_keyword in src.lower() for ad_keyword in ['ad', 'doubleclick', 'adsystem']):
                iframe.decompose()
            else:
                # Garante que a URL do iframe é absoluta
                iframe['src'] = urljoin(base_url, src)

    def _validar_conteudo_extraido(self, clean_html: str) -> bool:
        """
        Valida se o conteúdo extraído não contém palavras-chave de falha.
        
        Args:
            clean_html: HTML limpo para validação
            
        Returns:
            True se o conteúdo é válido, False caso contrário
        """
        if not clean_html or len(clean_html.strip()) < 100:
            return False
        
        # Converter para lowercase para busca case-insensitive
        content_lower = clean_html.lower()
        
        # Verificar se contém palavras-chave de falha
        for keyword in self.PALAVRAS_CHAVE_DE_FALHA:
            if keyword in content_lower:
                logging.warning(
                    f"Palavra-chave de falha encontrada: '{keyword}'"
                )
                return False
        
        return True
    
    def _add_to_blacklist(
        self,
        url: str,
        error_type: str,
        error_message: str,
        reason: str
    ) -> None:
        """Helper para adicionar à blacklist"""
        self.blacklist.add_to_blacklist(
            url=url,
            error_type=error_type,
            error_message=error_message,
            reason=reason
        )
