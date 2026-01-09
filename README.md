# K’KOO – Trust-Driven Commerce Infrastructure for African Realities

**Current date: January 09, 2026**  
**Version: Production-Ready Backend (Django 6.0)**

## Straight Talk Upfront
K’KOO is **not** another e-commerce app.

It is a **trust-driven commerce infrastructure** built for the realities of informal sellers, fragmented logistics, low-trust environments, and mobile-money-first economies in Africa.

Core promise (non-negotiable):
1. You get **exactly** what you ordered  
2. You get it **on time**  
3. If anything goes wrong, **the platform takes responsibility**

Every line of code, every model, every view enforces this promise — even when it hurts short-term margins.

## What We’ve Built So Far (End-to-End Trust Infrastructure)

| Component          | Status      | Key Features Delivered                                                                 |
|--------------------|-------------|----------------------------------------------------------------------------------------|
| **Users**          | Complete    | Phone-first OTP login, Buyer & Seller profiles, KYC verification, admin ban/suspend   |
| **Catalog**        | Complete    | Verified brands, product verification workflow, SKU variants, media verification     |
| **Cart**           | Complete    | Persistent cart, add/update/remove/clear, real-time incentive preview                 |
| **Promotions**     | Complete    | Admin-only time-bound deals, discount codes, priority, burn tracking, no stacking    |
| **Orders**         | Complete    | Immutable cart snapshot, escrow hold, strict state machine, delivery proof mandatory |
| **Incentives**     | Complete    | Promotion + discount code + loyalty points applied at checkout, full snapshot        |

## Key Operational Discipline

- **Platform absorbs all discounts** (promotion, code, loyalty) → seller always gets full base price
- **No stacking** — highest priority promotion wins
- **Burn tracking** on every promotion/code use
- **Evidence mandatory** for delivered status and disputes
- **Atomic checkout** — incentives, stock, order creation in one transaction
- **Immutable snapshot** — original/discount/final total + applied incentives stored forever

## Tech Stack

- Django 6.0
- Django REST Framework
- SQLite (dev) → PostgreSQL (production ready)
- PhoneNumberField for Africa-first identity
- JSONField for flexible specs & snapshots

## Project Structure

```
kkoo/
├── users/              # Identity, KYC, profiles
├── catalog/            # Verified products, brands, media
├── cart/               # Persistence + incentive preview
├── promotions/         # Admin-controlled deals & codes
├── orders/             # Escrow, state machine, delivery proof
└── kkoo/               # Settings, urls
```

## Running the Project

```bash
# Clone & setup
git clone <repo>
cd kkoo
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Migrate
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run
python manage.py runserver
```

## API Endpoints (Key Ones)

- `GET /api/v1/cart/` – View cart with incentives
- `POST /api/v1/orders/checkout/` – Full checkout with promotion/code/loyalty
- `GET /api/v1/orders/` – List user orders
- Admin: `/admin/` – Full governance (verify products, manage promotions)

## What’s Missing (Next Priorities)

| Feature                     | Impact if Delayed                     | Priority |
|-----------------------------|---------------------------------------|----------|
| Payments (M-Pesa webhook)   | No real money flow                    | Critical |
| Logistics & Rider Assignment| “On time” promise breaks              | Critical |
| Referral Reward on Completion| Zero-CAC growth stalled               | High     |
| Recommendation Engine       | Lower retention                       | High     |
| Notifications (SMS/WhatsApp)| Missed updates → trust erosion         | Medium   |
| Admin Analytics Dashboard   | Blind growth → margin bleed           | Medium   |

## Final Call-Out (No Filter)

If you chase features, growth hacks, or global scale too early — you lose.

If you nail trust, control execution, and respect unit economics — you earn the right to scale.

K’KOO is built to start local in Dar es Salaam, operate with iron discipline, and compound trust until it becomes the default way people buy in Africa.

This is infrastructure, not an app.

**Built with discipline. Ready for money.**

Your move: payments or logistics?