# CryptoPulse AI — Architektur-Dokument

## Technologie-Stack

| Komponente | Technologie | Begründung |
|---|---|---|
| Backend | Python 3.11+ / FastAPI | Async-native, WebSocket-Support, perfekt für AI/ML |
| Frontend | React 18 + TypeScript + Vite | Mobile-first, extrem schnell, riesiges Ökosystem |
| Datenbank | PostgreSQL (Prod) / SQLite (Dev) + TimescaleDB für Zeitreihen | Beste Unterstützung für Finanzdaten-Zeitreihen |
| Cache | Redis | Orderbuch-Caching, Sessions, Rate-Limiting |
| ML/AI | scikit-learn, XGBoost, PyTorch, pandas, numpy | Bewährte Bibliotheken für Finanz-ML |
| Async Jobs | Celery + Redis Broker | Für Hintergrund-Analysen und Datenabruf |
| Charting | Lightweight Charts (TradingView) | Professionelle Finanz-Charts |
| CI/CD | GitHub Actions | Automatisierte Tests und Deployment |

## Systemarchitektur

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React)                      │
│  Dashboard │ Trading │ Analyse │ Portfolio │ Settings   │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP REST + WebSocket
                     ▼
┌─────────────────────────────────────────────────────────┐
│              API Gateway (FastAPI)                       │
│  Auth │ Rate Limit │ WebSocket │ REST Endpoints         │
└────────┬────────┬────────┬────────┬─────────────────────┘
         │        │        │        │
         ▼        ▼        ▼        ▼
┌──────────┐ ┌────────┐ ┌────────┐ ┌──────────────┐
│ Market   │ │ On-Chain│ │ Sentiment│ │ Trading      │
│ Service  │ │ Service │ │ Service │ │ Engine       │
└──────────┘ └────────┘ └────────┘ └──────────────┘
         │        │        │        │
         ▼        ▼        ▼        ▼
┌─────────────────────────────────────────────────────────┐
│              AI/ML Engine (Kern)                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────────┐    │
│  │ Prediction│ │ Decision │ │ Reinforcement        │    │
│  │ Models   │ │ Scoring  │ │ Learning (kontinuierl)│    │
│  └──────────┘ └──────────┘ └──────────────────────┘    │
└─────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│              Datenbanken                                 │
│  PostgreSQL │ TimescaleDB │ Redis │ Filesystem          │
└─────────────────────────────────────────────────────────┘
```

## KI-Modell-Konzept

### 1. Marktprognose (Ensemble-Methoden)
- XGBoost für kurzfristige Preisprognosen (1-24h)
- LSTM (PyTorch) für mittelfristige Trends (1-7 Tage)
- Random Forest für Volatilitätsprognosen

### 2. Sentiment-Analyse
- Fine-Tuned Transformer-Modell (FinBERT) für News/Social Media
- Stimmungsanalyse in 5 Sprachen (DE, EN, TR, IT, AR)

### 3. Entscheidungsfindung (Multi-Faktor-Scoring)
Gesamtscore = w1 * Marktanalyse + w2 * OnChain + w3 * Technik + w4 * News + w5 * Sentiment + w6 * Risiko + w7 * Historie

### 4. Kontinuierliches Lernen
- Jeder Trade (auch Paper-Trades) trainiert das Modell nach
- Selbstkontrolle: Wenn Trefferquote < 45% → reduzierte Empfehlungen
- Automatische Feature-Wichtung-Anpassung

## Sicherheitskonzept

- API-Schlüsselverschlüsselung mit Fernet (AES-256)
- Binance-API: Nur Read + Trading (keine Auszahlungen)
- Not-Aus-Schalter (Emergency Kill Switch)
- Vollständige Audit-Logs aller Aktionen
- JWT-Authentifizierung mit Kurzzeit-Tokens