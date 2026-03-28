# SEO & Marketing Skill — App Promotion

## Trigger
Use this skill for any marketing, SEO, ASO, content, or growth tasks:
- App Store Optimization (ASO)
- Search Engine Optimization (SEO)
- Content marketing strategy
- Telegram channel growth
- Social media marketing (SMM)
- Influencer outreach
- Paid advertising (Telegram Ads, Apple Search Ads, VK Ads)
- Analytics and conversion optimization

Trigger keywords: "маркетинг", "продвижение", "SEO", "ASO", "контент", "реклама", "трафик", "конверсия", "воронка", "CPA", "CPI", "CTR", "retention"

## ASO (App Store Optimization)

### App Store (iOS)
- Title: max 30 chars, primary keyword first
- Subtitle: max 30 chars, secondary keywords
- Keywords field: 100 chars, comma-separated, no spaces after commas
- Description: 4000 chars, first 3 lines critical (visible before "more")
- Screenshots: 6.7" (1290x2796) + 5.5" (1242x2208), first 3 most important
- Preview video: 15-30 sec, show core value in first 5 sec
- Category: Medical or Lifestyle
- Localization: ru, en minimum

### RuStore (Android)
- Title: max 50 chars
- Short description: max 80 chars
- Full description: max 4000 chars
- Screenshots: min 2, max 8, 1080x1920 recommended
- Icon: 512x512 PNG
- Category: Здоровье и фитнес
- Rating: 0+ (no restricted content)

### Telegram Mini App Store
- Name: max 64 chars
- Description: max 512 chars
- Bot must have /start command
- Mini App URL must be HTTPS
- Icon: 640x640 PNG

### Keyword Research Framework
1. Seed keywords: "ветеринар", "здоровье питомца", "болезни кошек", "болезни собак"
2. Long-tail: "проверить здоровье кошки онлайн", "расшифровка анализов собаки"
3. Competitor keywords: analyze Vetsy, Petstory, TTcare listings
4. Tools: App Annie / Sensor Tower (ASO), Yandex Wordstat (SEO)
5. Prioritize by: search volume × relevance × competition

## SEO Strategy

### Technical SEO
- Landing page: vetai.ru (or .app)
- Core Web Vitals: LCP <2.5s, FID <100ms, CLS <0.1
- Mobile-first indexing (95%+ mobile traffic expected)
- Structured data: SoftwareApplication schema
- Sitemap.xml + robots.txt
- SSL/HTTPS mandatory
- Yandex Webmaster + Google Search Console

### Content SEO (Pillar Strategy)
Pillar pages (high-volume):
- "Здоровье кошек — полный гид" → 50+ related articles
- "Здоровье собак — полный гид" → 50+ related articles
- "Расшифровка анализов животных" → 20+ articles
- "Болезни кожи у кошек/собак" → 30+ articles

Cluster articles (long-tail):
- "Почему кошка чешется — 10 причин"
- "Норма лейкоцитов у собаки"
- "Как понять что кошка болеет"
- Each article → CTA to VetAI bot/app

### Content Calendar Template
- 3 articles/week (AI-assisted writing)
- 1 video/week (Reels/Shorts — pet health tips)
- Daily Telegram channel posts
- Monthly comprehensive guide

## Telegram Growth Strategy

### Channel Content Mix
- 40% полезный контент (симптомы, советы, чек-листы)
- 25% кейсы пользователей (до/после, истории)
- 20% интерактив (опросы, викторины, Q&A)
- 15% продуктовые посты (фичи, обновления, промо)

### Growth Tactics (by phase)
Phase 0 (pre-launch): seed in 10-15 pet channels, 50k₽ budget
Phase 1 (months 1-2): Telegram Ads 30k₽/mo + micro-influencers 40k₽
Phase 2 (months 3-6): referral program, gamification, B2B partnerships
Phase 3 (months 6-12): PR (vc.ru, Habr), paid scaling

### Referral Mechanics
- "Пригласи друга → +2 бесплатные проверки обоим"
- Deep link: t.me/vetai_bot?start=ref_{user_id}
- Track: referral_code in user table
- Viral coefficient target: K > 0.3

## Paid Advertising

### Telegram Ads
- Format: sponsored messages in channels
- Targeting: pet channel subscribers, 25-45, cities 500k+
- Budget: start 1000₽/day, scale to 3000₽/day
- CPA target: <50₽ per install
- A/B test: 3 creatives minimum, rotate weekly

### Apple Search Ads (iOS)
- Keywords: "ветеринар", "здоровье питомца", "анализы животных"
- Match types: exact + broad
- Budget: start $10/day
- CPI target: <$3 (≈300₽)
- Optimize for: post-install events (first diagnosis)

### VK Ads / Yandex Direct
- Retargeting: website visitors who didn't install
- Lookalike: based on existing users
- Budget: 500₽/day start

## Analytics & KPIs

### North Star Metric
- Weekly Active Diagnoses (WAD) — # of photo/lab/chat checks per week

### Funnel Metrics
- Awareness: impressions, channel subscribers
- Acquisition: installs, CPI, organic vs paid ratio
- Activation: onboarding completion rate (target >80%)
- Revenue: conversion to paid (target 15-22%), ARPU, MRR
- Retention: D1 (>60%), D7 (>40%), D30 (>25%)
- Referral: viral coefficient, referral conversion rate

### Tools
- Amplitude / Mixpanel — product analytics
- Adjust / AppsFlyer — attribution
- Yandex.Metrica — web analytics
- Telegram Bot Analytics — channel metrics

### Reporting Template
Weekly: installs, WAD, conversion, MRR, top channels
Monthly: cohort analysis, LTV update, channel ROI, content performance
Quarterly: market share estimate, competitor moves, strategy pivot review