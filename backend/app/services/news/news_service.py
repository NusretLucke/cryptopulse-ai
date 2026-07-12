"""News Service - Abruf und KI-Analyse von Krypto-Nachrichten"""

import httpx
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.models.database import NewsArticle
from app.services.analysis.sentiment_analysis import SentimentAnalyzer


class NewsService:
    """Krypto-Nachrichten abrufen und mit KI analysieren"""

    TOP_COINS = ["bitcoin", "ethereum", "solana", "cardano", "ripple",
                 "polkadot", "chainlink", "avalanche", "dogecoin", "polygon"]

    def __init__(self):
        self.sentiment_analyzer = SentimentAnalyzer()

    async def fetch_crypto_news(self, limit: int = 20) -> list[dict]:
        """Aktuelle Krypto-Nachrichten abrufen (CryptoCompare API)"""
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                url = "https://min-api.cryptocompare.com/data/v2/news/"
                params = {"lang": "EN", "limit": limit, "sortOrder": "popular"}
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("Data", [])
            except Exception as e:
                print(f"Fehler beim News-Abruf: {e}")

        # Fallback: Dummy-News für Entwicklung
        return self._get_dummy_news()

    def _get_dummy_news(self) -> list[dict]:
        """Dummy-Nachrichten für Entwicklung ohne API-Key"""
        return [
            {
                "id": "1", "title": "Bitcoin erreicht neuen Monatshöchststand nach positiven Wirtschaftsdaten",
                "body": "Bitcoin ist um 5% gestiegen, da die US-Arbeitsmarktdaten besser als erwartet ausfielen. Analysten sehen Potenzial für weitere Gewinne.",
                "source": "CryptoNews", "url": "https://example.com/news/1",
                "published_on": int(datetime.utcnow().timestamp()),
                "categories": "BTC, Markets",
            },
            {
                "id": "2", "title": "Ethereum-Entwickler kündigen wichtiges Netzwerk-Upgrade an",
                "body": "Das Ethereum-Team hat ein bedeutendes Protokoll-Upgrade angekündigt, das die Skalierbarkeit verbessern und die Gas-Gebühren senken soll.",
                "source": "CoinDesk", "url": "https://example.com/news/2",
                "published_on": int(datetime.utcnow().timestamp()) - 3600,
                "categories": "ETH, Technology",
            },
            {
                "id": "3", "title": "SEC verschiebt Entscheidung über Bitcoin-ETF erneut",
                "body": "Die US-Börsenaufsicht SEC hat ihre Entscheidung über mehrere Bitcoin-ETF-Anträge erneut verschoben, was zu kurzfristiger Unsicherheit führt.",
                "source": "Reuters", "url": "https://example.com/news/3",
                "published_on": int(datetime.utcnow().timestamp()) - 7200,
                "categories": "BTC, Regulation",
            },
            {
                "id": "4", "title": "Solana verzeichnet Rekord bei täglichen Transaktionen",
                "body": "Das Solana-Netzwerk hat einen neuen Rekord bei den täglichen Transaktionen aufgestellt, was auf eine steigende Akzeptanz hindeutet.",
                "source": "The Block", "url": "https://example.com/news/4",
                "published_on": int(datetime.utcnow().timestamp()) - 14400,
                "categories": "SOL, Adoption",
            },
            {
                "id": "5", "title": "Krypto-Marktkapitalisierung übersteigt 2,5 Billionen Dollar",
                "body": "Der gesamte Kryptomarkt hat einen Meilenstein erreicht, da institutionelle Investoren weiterhin in digitale Vermögenswerte investieren.",
                "source": "Bloomberg", "url": "https://example.com/news/5",
                "published_on": int(datetime.utcnow().timestamp()) - 21600,
                "categories": "Markets, Institutional",
            },
        ]

    async def fetch_and_analyze(self, db: AsyncSession):
        """Nachrichten abrufen und mit KI analysieren"""
        articles = await self.fetch_crypto_news()

        for article in articles:
            # Prüfen ob bereits vorhanden
            result = await db.execute(
                select(NewsArticle).where(NewsArticle.url == article.get("url", ""))
            )
            if result.scalar_one_or_none():
                continue

            # Text für Analyse
            text = f"{article.get('title', '')} {article.get('body', '')}"

            # KI-Sentiment-Analyse
            sentiment = self.sentiment_analyzer.analyze_text(text)
            coins = self.sentiment_analyzer.extract_coins(text, self.TOP_COINS)
            categories = self.sentiment_analyzer.classify_categories(text)
            impact = self.sentiment_analyzer.calculate_impact_score(
                sentiment, source_authority=0.6
            )

            published = datetime.fromtimestamp(
                article.get("published_on", int(datetime.utcnow().timestamp()))
            )

            news = NewsArticle(
                source=article.get("source", "Unknown"),
                title=article.get("title", ""),
                url=article.get("url", ""),
                content_summary=article.get("body", "")[:500],
                published_at=published,
                sentiment_score=sentiment["score"],
                sentiment_label=sentiment["label"],
                impact_score=impact,
                relevant_coins=coins,
                categories=categories,
                is_analyzed=True,
            )
            db.add(news)

        await db.commit()

    async def get_recent_news(self, db: AsyncSession, limit: int = 20) -> list[NewsArticle]:
        """Aktuelle analysierte Nachrichten abrufen"""
        result = await db.execute(
            select(NewsArticle)
            .order_by(desc(NewsArticle.published_at))
            .limit(limit)
        )
        return result.scalars().all()

    async def get_news_by_sentiment(
        self, db: AsyncSession, sentiment: str = "positiv", limit: int = 10
    ) -> list[NewsArticle]:
        """Nachrichten nach Stimmung filtern"""
        result = await db.execute(
            select(NewsArticle)
            .where(NewsArticle.sentiment_label == sentiment)
            .order_by(desc(NewsArticle.impact_score))
            .limit(limit)
        )
        return result.scalars().all()