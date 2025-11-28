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
import difflib
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
    
    def __init__(self):
        self.blacklist: Optional[ScrapingBlacklist] = None
        
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

    def set_blacklist(self, blacklist: ScrapingBlacklist):
        """Define a instância da blacklist a ser usada pelo serviço."""
        self.blacklist = blacklist
        logging.info("Instância da ScrapingBlacklist foi definida no ScrapeService.")
        
    def scrape_article_content(self, url: str) -> Optional[Dict[str, str]]:
        try:
            if not self.blacklist:
                raise Exception("ScrapingBlacklist não foi inicializada no ScrapeService.")
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
            
            article_text = article.text
            # 1. Checagem de Obfuscação
            if self._is_content_obfuscated(article_text):
                logging.warning(f"Conteúdo ofuscado detectado em {url}")
                return None

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
            
            # 2. Processamento com "Trim" baseado no texto
            processed_html = self._process_html_aggressive(raw_html, url, reference_text=article_text)
            
            # Validar conteúdo extraído
            # 3. Scoring System
            quality = self._calculate_quality_score(processed_html, article_text)

            if not quality['is_valid']:
                logging.warning(f"Baixa qualidade ({quality['score']}) para {url}: {quality['reasons']}")
                
                # Opcional: Tentar Fallback IA aqui se score > 20
                # if quality['score'] > 20: processed_html = self._fallback_ai_extraction(raw_html)
                
                return None # ou salvar com flag de 'revisão necessária'


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
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Request error: {str(e)}"
            logging.error(f"Erro de requisição para {url}: {error_msg}")
            # Evitar blacklist para erros genéricos de rede que podem ser temporários
            # Apenas erros persistentes ou de acesso devem ir para a blacklist
            # self._add_to_blacklist(...)
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
            error_msg = str(e).lower()
            logging.error(f"Falha de parse/download em {url}: {e}")

            # Extrair o status code da mensagem de erro, se existir
            status_match = re.search(r'status code (\d+)', error_msg)
            if status_match:
                status_code = int(status_match.group(1))
                if status_code in [401, 403]:
                    logging.warning(f"Acesso negado ({status_code}) detectado via ArticleException. Adicionando à blacklist.")
                    self._add_to_blacklist(url, f'Access Denied ({status_code})', str(e), 'Bloqueio de permissão')
                elif status_code == 404:
                    logging.info(f"Página não encontrada (404) para {url}. Ignorando sem blacklist.")
            # Adicionar verificação para mensagens de erro de proteção (ex: Cloudflare, PerimeterX)
            elif any(keyword in error_msg for keyword in ['perimeterx', 'cloudflare', 'protected by', 'access to this page has been denied']):
                logging.warning(f"Proteção anti-scraping detectada em {url}. Adicionando à blacklist.")
                self._add_to_blacklist(
                    url=url,
                    error_type='Anti-Scraping Protection',
                    error_message=str(e),
                    reason='Site protegido por serviço anti-bot'
                )
            elif 'timeout' in error_msg:
                logging.warning(f"Timeout detectado em {url} via ArticleException. Ignorando sem blacklist.")
            
            # Retorna None para qualquer ArticleException
            return None
            
        except Exception as e:
            error_msg = str(e)
            logging.error(f"Erro no scraping de {url}: {error_msg}", exc_info=True)
            return None

    def _process_html_aggressive(self, html: str, base_url: str, reference_text: str = "") -> str:
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
        self._sanitize_generic_social_embeds(soup)
        self._sanitize_twitter_embeds(soup)
        self._sanitize_youtube_embeds(soup)
        self._filter_iframes(soup, base_url)

        # Remover estruturas de anúncios aninhadas
        self._remove_deeply_nested_empty_tags(soup)
        

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

        # Cortar o final do HTML que não corresponde ao texto extraído
        self._trim_html_tail_by_content(soup, reference_text)

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
    
    def _trim_html_tail_by_content(self, soup: BeautifulSoup, reference_text: str):
        """
        Corta o HTML onde o texto do newspaper termina.
        Isso remove seções de 'comentários', 'leia mais' e rodapés que o newspaper ignorou.
        Usa difflib para uma comparação robusta.
        """
        if not reference_text or not soup.body:
            return

        # Normaliza ambos os textos para uma comparação mais limpa
        ref_text_norm = ' '.join(reference_text.split())
        soup_text_norm = ' '.join(soup.get_text().split())

        # Usa difflib para encontrar o maior bloco correspondente
        matcher = difflib.SequenceMatcher(None, soup_text_norm, ref_text_norm)
        match = matcher.find_longest_match(0, len(soup_text_norm), 0, len(ref_text_norm))

        # O ponto de corte é o final do texto correspondente no HTML
        cutoff_point = match.a + match.size

        # Encontra o elemento onde o corte deve ocorrer
        char_count = 0
        last_valid_element = None

        for element in soup.find_all(string=True):
            if not element.parent or element.parent.name in ['script', 'style']:
                continue

            text_len = len(' '.join(element.string.split()))
            if char_count + text_len >= cutoff_point:
                # Encontramos o elemento onde o texto bom termina
                last_valid_element = element
                break
            char_count += text_len

        if last_valid_element:
            # Sobe na árvore até encontrar um bloco de conteúdo (p, div, figure, etc.)
            parent_block = last_valid_element.find_parent(['p', 'div', 'figure', 'h1', 'h2', 'h3', 'ul', 'ol'])
            if parent_block:
                # Remove todos os elementos irmãos que vêm depois deste bloco
                for sibling in list(parent_block.find_next_siblings()):
                    sibling.decompose()

    def _remove_deeply_nested_empty_tags(self, soup: BeautifulSoup, max_depth=15):
        """Remove estruturas excessivamente profundas que geralmente são wrappers de anúncios"""
        def get_depth(element):
            depth = 0
            while element.parent:
                depth += 1
                element = element.parent
            return depth

        for element in soup.find_all():
            if get_depth(element) > max_depth:
                # Se for muito profundo e não tiver texto significativo próprio, remove
                if not element.get_text(strip=True):
                    element.decompose()

    def _calculate_quality_score(self, html_content: str, text_content: str) -> dict:
        score = 100
        reasons = []

        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 1. Densidade de Texto (HTML não deve ser muito maior que o texto útil)
        len_html = len(html_content)
        len_text = len(text_content)
        if len_html > 0:
            ratio = len_text / len_html
            if ratio < 0.2: # Muito código para pouco texto
                score -= 20
                reasons.append("Low text-to-code ratio")

        # 2. Estrutura Mínima
        if not soup.find(['p']):
            score -= 30
            reasons.append("No paragraphs found")
        
        # 3. Comprimento do Texto
        if len_text < 300: # Notícia muito curta
            score -= 40
            reasons.append("Text too short")

        # 4. Detecção de "Cookie Wall" ou Paywall
        text_lower = text_content.lower()
        suspicious_phrases = ['subscribe now', 'read the full story', 'accept cookies', 'register to continue']
        if any(p in text_lower for p in suspicious_phrases):
            score -= 50
            reasons.append("Possible paywall/cookie wall detected")

        return {'score': max(0, score), 'reasons': reasons, 'is_valid': score > 50}


    def _sanitize_generic_social_embeds(self, soup: BeautifulSoup):
        # TikTok
        for block in soup.find_all('blockquote', class_='tiktok-embed'):
             video_id = block.get('data-video-id')
             if video_id:
                 placeholder = self._create_generic_placeholder(soup, 'tiktok', video_id)
                 block.replace_with(placeholder)

        # Instagram
        for block in soup.find_all('blockquote', class_='instagram-media'):
             link = block.get('data-instgrm-permalink')
             if link:
                 placeholder = self._create_generic_placeholder(soup, 'instagram', link)
                 block.replace_with(placeholder)

    def _create_generic_placeholder(self, soup, platform, content_id):
        div = soup.new_tag('div')
        div['class'] = f'{platform}-placeholder'
        div[f'data-{platform}-id'] = content_id
        return div

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
        Encontra qualquer ocorrência de links do YouTube (texto, embeds, iframes)
        e os converte para um placeholder padronizado.
        """
        video_ids_processados = set()
        # Regex para encontrar qualquer URL do YouTube
        youtube_regex = re.compile(r"https?://(?:www\.)?(?:youtube\.com/(?:watch\?v=|embed/)|youtu\.be/)([a-zA-Z0-9_-]{11})")

        # 1. Busca universal por texto em todo o documento
        # Encontra todos os nós de texto que contêm uma URL do YouTube
        text_nodes = soup.find_all(string=youtube_regex)

        for node in text_nodes:
            match = youtube_regex.search(str(node))
            if match:
                video_id = match.group(1)
                if video_id not in video_ids_processados:
                    placeholder = self._create_youtube_placeholder(soup, video_id)
                    
                    # Encontra o elemento "container" mais próximo para substituir.
                    # Isso evita colocar um <div> dentro de um <a> ou <p>.
                    parent_to_replace = node.find_parent(['p', 'div', 'figure'])
                    
                    if parent_to_replace:
                        parent_to_replace.replace_with(placeholder)
                    else:
                        # Fallback: se não encontrar um pai adequado, substitui o nó de texto
                        node.replace_with(placeholder)
                        
                    video_ids_processados.add(video_id)

        # 2. Limpeza final de iframes e links que possam ter sobrado
        # Isso garante que se um vídeo já foi processado, seu iframe duplicado seja removido.
        for tag in soup.find_all(['iframe', 'a'], src=youtube_regex) if 'iframe' in soup.find_all() else soup.find_all('a', href=youtube_regex):
            url = tag.get('src') or tag.get('href', '')
            match = youtube_regex.search(url)
            if match:
                video_id = match.group(1)
                if video_id in video_ids_processados:
                    # Se o vídeo já foi convertido em placeholder, remove a tag original
                    tag.decompose()
                else:
                    # Se por algum motivo não foi pego antes, converte agora
                    placeholder = self._create_youtube_placeholder(soup, video_id)
                    tag.replace_with(placeholder)
                    video_ids_processados.add(video_id)


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

    def _is_content_obfuscated(self, text: str) -> bool:
        """
        Verifica se o conteúdo parece ofuscado ou criptografado.
        Isso é útil para detectar sites com anti-scraping que retornam texto "lixo".
        
        Args:
            text: O texto puro extraído do artigo.

        Returns:
            True se o conteúdo parece ofuscado, False caso contrário.
        """
        if not text:
            return False
        
        words = text.split()
        long_words = [w for w in words if len(w) > 30]
        
        # Se mais de 5% das palavras forem gigantescas (base64 ou hashes)
        if len(words) > 0 and (len(long_words) / len(words)) > 0.05:
            logging.warning("Detecção de ofuscamento: alta densidade de palavras longas.")
            return True
            
        # Verifica se há palavras-chave de falha no texto
        text_lower = text.lower()
        for keyword in self.PALAVRAS_CHAVE_DE_FALHA:
            if keyword in text_lower:
                logging.warning(f"Detecção de ofuscamento: palavra-chave de falha encontrada ('{keyword}').")
                return True

        return False
   
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
