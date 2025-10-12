// src/pages/NewsPage.jsx

import React, { useState, useEffect } from "react";
import HeaderNewsPage from "../components/NewsPage/HeaderNewsPage";
import NewsPageSkeleton from "../components/NewsPage/NewsPageSkeleton";
import { useParams } from "react-router-dom";

const MOCK_ARTICLE_HTML =
  '<div><p>Swan Bitcoin CEO Cory Klippsten said Bitcoin&#8217;s price volatility may not be over after the cryptocurrency briefly fell to $102,000 on Friday, following US President Donald Trump&#8217;s announcement of a 100% tariff on Chinese imports.</p><p>&#8220;If the broader risk-off mood holds, Bitcoin can get dragged around a bit before it finds support and starts to decouple again,&#8221; Klippsten told Cointelegraph on Friday.</p><p>Klippsten said that Bitcoiners should expect some turbulence over the coming days. &#8220;Macro-driven dips like this usually wash out leveraged traders and weak hands, then reset positioning for the next leg up,&#8221; Klippsten said. </p><h2>$8 billion wiped out in crypto market</h2><p>Over the past 24 hours, around $2.19 billion in Bitcoin (<a href="/bitcoin-price">BTC</a>) long positions have been liquidated, contributing to a total of $8.02 billion in long liquidations across the broader crypto market, <a href="https://www.coinglass.com/LiquidationData" rel="noopener nofollow" target="_blank" title="null">according</a> to CoinGlass.</p><p>&#8220;We&#8217;ve got a little panic in the markets right now, classic macro whiplash. Trump and China are trading tariff threats, equities are off, and traders are scrambling to derisk,&#8221; Klippsten added.</p><p>Cointelegraph head of markets Ray Salmond said that leveraged traders &#8220;were totally caught off guard&#8221; as Trump&#8217;s tariff announcement &#8220;sent shockwaves across the crypto market.&#8221; </p><img alt="" src="https://s3.cointelegraph.com/uploads/2025-10/0199d06a-562f-7306-8ef4-0c2c873da518" title="">Bitcoin has slightly recovered trading at $113,270 at the time of publication. Source: <a href="https://coinmarketcap.com/currencies/bitcoin/" rel="nofollow noopener" target="_blank" title="https://coinmarketcap.com/currencies/bitcoin/">CoinMarketCap</a><p>Salmond explained that Bitcoin&#8217;s price dislocation between crypto exchange Coinbase, where the BTC/USD pair fell to $107,000 and and crypto exchange Binance perpetual futures, where the BTC/USDT pair crashed to $102,000, &#8220;really illustrates the severity of the cascading liquidations and how stops were completely obliterated.&#8221;</p><p>Salmond pointed to liquidation heatmap data from Hyblock, which shows &#8220;literally all downside long liquidity absorbed, with a liquidation cluster $102,000 to $97,000 remaining.&#8221;</p><img alt="" src="https://s3.cointelegraph.com/uploads/2025-10/0199d06c-3632-726e-8ee2-510b20e31040" title="">Bitcoin liquidation heatmap, 7-day look back. Source Hyblock<p>It&#8217;s not the first time Bitcoin has dropped sharply after a Trump tariff announcement. In April, Trump&#8217;s <a href="https://cointelegraph.com/news/trump-liberation-day-tariffs-markets-recession" title="null">first tariff announcements</a> sent shockwaves through crypto markets and sparked fears of a recession. </p><p>On Feb. 1, when Trump signed an executive order to impose import tariffs on goods from China, Canada, and Mexico, Bitcoin fell below $100,000.</p><h2>Bitcoin analysts are staying optimistic</h2><p>Several Bitcoin analysts say the most recent price drop could present a buying opportunity.</p><p>Bitwise Invest senior investment strategist Juan Leon <a href="https://x.com/singularity7x/status/1976701760459981295" rel="noopener nofollow" target="_blank" title="null">said</a> in an X post that &#8220;the best time to buy BTC has tended to be when it is being dragged down by broader markets.&#8221;</p><p><strong>Related: </strong><a href="https://cointelegraph.com/news/bitcoin-mayer-multiple-btc-price-can-180k-before-overbought" title="null"><strong>Bitcoin Mayer Multiple: BTC price can hit $180K before being &#8216;overbought&#8217;</strong></a></p><p>Meanwhile, Bitwise Invest chief investment officer Matt Hougan <a href="https://x.com/Matt_Hougan/status/1976761321778794541" rel="nofollow noopener" target="_blank" title="https://x.com/Matt_Hougan/status/1976761321778794541">reminded</a> his 85,900 X followers of a typical pattern among market participants, noting that while many say they&#8217;ll buy Bitcoin during a price pullback, they often hesitate when it happens because &#8220;the market doesn&#8217;t &#8216;feel&#8217; good at that point.&#8221;</p><p>&#8220;It never feels good when you buy the dip. The dip comes when sentiment drops. Writing the number down can be a good form of discipline,&#8221; Hougan said.</p><p><strong>Magazine: </strong><a href="https://cointelegraph.com/magazine/europe-chat-control-germany-oppose-scan-messages/" title="null"><strong>EU&#8217;s privacy-killing Chat Control bill delayed &#8212; but fight isn&#8217;t over</strong></a></p></div>';

// Mock Data para cabeçalho da notícia
const MOCK_NEWS_DATA = {
  title:
    "How clean can a robot vacuum really get your home? Here's what users say",
  image:
    "https://www.slashgear.com/img/gallery/how-clean-can-a-robot-vacuum-really-get-your-home-heres-what-users-say/l-intro-1759837792.jpg",
  source: "SlashGear",
  date: "10 de Outubro de 2025",
};

const NewsPage = () => {
  // *TEMOS QUE FAZER* Buscar o ID com useParams() e fazer uma chamada à API aqui
  // const { newsId } = useParams();
  const [articleData, setArticleData] = useState(null);
  const [loading, setLoading] = useState(true);

  // Simulação da busca de dados da API
  useEffect(() => {
    // Simulando a busca dos dados
    setTimeout(() => {
      setArticleData({
        ...MOCK_NEWS_DATA,
        contentHtml: MOCK_ARTICLE_HTML,
      });
      setLoading(false);
    }, 800);
  }, []);

  // Função de segurança para HTML
  const createMarkup = (htmlContent) => {
    return { __html: htmlContent };
  };

  if (loading || !articleData) {
    return <NewsPageSkeleton />;
  }

  return (
    <div className="bg-white min-h-screen">
      {/* Header da Página de Notícias (mantendo o email do usuário) */}
      <HeaderNewsPage />

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 pt-10 pb-20">
        {/* Imagem de Destaque */}
        <img
          src={articleData.image}
          alt={articleData.title}
          className="w-full h-96 object-cover rounded-lg mb-8 shadow-md"
        />

        {/* Título e Metadados */}
        <div className="mb-10 border-b border-gray-300 pb-4">
          <h1 className="text-4xl font-extrabold text-gray-900 font-montserrat mb-3 leading-tight">
            {articleData.title}
          </h1>
          <p className="text-base text-gray-600 font-montserrat">
            Fonte:{" "}
            <span className="font-semibold text-black">
              {articleData.source}
            </span>{" "}
            | {articleData.date}
          </p>
        </div>

        {/* 🛑 Conteúdo do Artigo com dangerouslySetInnerHTML 🛑 */}
        <article>
          {/* A classe 'prose' do Tailwind é crucial aqui para aplicar estilos de leitura padrão ao HTML que vem da API (p, h2, img, a, etc.) */}
          <div
            className="prose prose-lg max-w-none font-montserrat text-gray-800"
            dangerouslySetInnerHTML={createMarkup(articleData.contentHtml)}
          />
        </article>
      </main>
    </div>
  );
};

export default NewsPage;
