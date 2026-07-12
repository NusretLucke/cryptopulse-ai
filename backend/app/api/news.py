"""News & Sentiment - API Endpoints"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.schemas import NewsSentimentResponse, SocialSentimentResponse
from app.services.news.news_service import NewsService
from app.models.database import SocialSentiment
from sqlalchemy import select, desc

router = APIRouter()
news_service = NewsService()


@router.get("/news", response_model=list[NewsSentimentResponse])
async def get_news(
    sentiment: str = Query("all", pattern="^(all|positiv|neutral|negativ)$"),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """KI-analysierte Krypto-Nachrichten"""
    if sentiment == "all":
        articles = await news_service.get_recent_news(db, limit)
    else:
        articles = await news_service.get_news_by_sentiment(db, sentiment, limit)

    return [
        NewsSentimentResponse(
            source=a.source, title=a.title, url=a.url,
            sentiment_score=a.sentiment_score,
            sentiment_label=a.sentiment_label,
            impact_score=a.impact_score,
            published_at=a.published_at,
            relevant_coins=a.relevant_coins or [],
            categories=a.categories or [],
        )
        for a in articles
    ]


@router.post("/news/refresh")
async def refresh_news(db: AsyncSession = Depends(get_db)):
    """Nachrichten neu abrufen und analysieren"""
    await news_service.fetch_and_analyze(db)
    return {"message": "Nachrichten aktualisiert und analysiert"}


@router.get("/sentiment/{symbol}", response_model=list[SocialSentimentResponse])
async def get_social_sentiment(
    symbol: str,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Social-Media-Stimmung für einen Coin"""
    from app.models.database import Market
    result = await db.execute(
        select(Market).where(Market.symbol == symbol.upper())
    )
    market = result.scalar_one_or_none()
    if not market:
        return []

    sent_result = await db.execute(
        select(SocialSentiment)
        .where(SocialSentiment.market_id == market.id)
        .order_by(desc(SocialSentiment.timestamp))
        .limit(limit)
    )
    sentiments = sent_result.scalars().all()

    return [
        SocialSentimentResponse(
            platform=s.platform, sentiment_score=s.sentiment_score,
            mention_count=s.mention_count, hype_score=s.hype_score,
            bot_activity_score=s.bot_activity_score, timestamp=s.timestamp,
        )
        for s in sentiments
    ]