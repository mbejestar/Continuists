# CONTINUUM PLATFORM BACKEND
> *"The files remain. The context doesn't."*

Continuum is a production-grade knowledge-preservation and knowledge-marketplace platform designed to preserve the human, scientific, and technical context behind projects before knowledge is lost through retirements, career changes, or deaths. Continuum allows eligible Missions to be evaluated and sold through a controlled, cryptographically protected knowledge marketplace.

---

## Architecture & Technology Stack

* **Language**: Python 3.10+
* **Framework**: FastAPI (Async REST API with Pydantic v2 validation)
* **ORM & Database**: SQLAlchemy 2.0 (Asyncpg) + PostgreSQL 15+
* **Database Migrations**: Alembic
* **Authentication**: Bcrypt password hashing + JWT Access (60 min) & Refresh (30 days) tokens
* **Identity**: Permanent Continuum ID generation (`CNT-XXXX-XXXX`) independent of personal identifiers (POPIA compliant)
* **Storage Layer**: Clean Storage Abstraction (Local / AWS S3 / MinIO) — metadata stored in PostgreSQL; large documents stored in object storage
* **Payment Layer**: South African Gateway Abstraction (Paystack / Ozow / Stripe) with automatic 8% direct and 15% assisted platform fee splits
* **Biometric Layer**: Privacy-first KYC Abstraction without raw biometric template storage (POPIA Section 26 Special Personal Information)

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Frontend                        │
│          HTML5 / CSS3 / Vanilla JS / Fetch API              │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTPS / JSON REST
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Application Engine                │
│  - JWT Bearer Authentication                                │
│  - Strict Server-Side Data Masking & Authorization Checks   │
│  - 50MB Free Tier Quota & Unlimited Premium Enforcement     │
│  - Immutable Audit Logging Service (POPIA Audit Trail)      │
└──────────────┬──────────────────────────────┬───────────────┘
               │ SQLAlchemy 2.0 (asyncpg)     │ Storage Interface
               ▼                              ▼
┌──────────────────────────────┐ ┌────────────────────────────┐
│      PostgreSQL Database     │ │   Cloud Object Storage     │
│  - 17 Relational Tables      │ │   (S3 / Vault Bucket)      │
│  - UUID Primary Keys         │ │   - Large Documents        │
│  - Strict Cascade & Indexes  │ │   - SHA-256 Verified Files │
└──────────────────────────────┘ └────────────────────────────┘
```

---

## Directory Structure

```
backend/
├── alembic.ini                   # Database migration configuration
├── requirements.txt              # Production Python package dependencies
├── schema.sql                    # Pure PostgreSQL DDL reference
├── .env.example                  # Environment variables template
├── README.md                     # Architecture and setup documentation
├── alembic/
│   ├── env.py                    # Alembic async migration environment
│   ├── script.py.mako            # Migration file template
│   └── versions/
│       └── 0001_initial_continuum_schema.py # Initial full schema migration
├── app/
│   ├── main.py                   # FastAPI application initialization & middleware
│   ├── core/
│   │   ├── config.py             # Pydantic BaseSettings & env loading
│   │   ├── database.py           # Async SQLAlchemy engine & session factory
│   │   ├── security.py           # Password hashing, tokens & CNT ID generator
│   │   ├── permissions.py        # Strict server-side authorization & masking
│   │   ├── storage.py            # Object storage abstraction & quota validator
│   │   ├── payment.py            # Payment gateway & fee calculation (8% vs 15%)
│   │   ├── biometric.py          # POPIA-compliant zero-raw-storage face recovery
│   │   └── audit.py              # Security audit logging engine
│   ├── models/                   # 12 SQLAlchemy ORM models
│   │   ├── user.py               # User & UserSettings
│   │   ├── mission.py            # Mission (11 fields, private default)
│   │   ├── document.py           # MissionDocument metadata & SHA-256
│   │   ├── collaboration.py      # Collaborators & Requests
│   │   ├── message.py            # Messages & Notifications
│   │   ├── marketplace.py        # MarketplaceListing & 10-point Evaluation
│   │   ├── purchase.py           # Purchases & MissionAccess grants
│   │   ├── succession.py         # Succession Contacts & Inactivity Release
│   │   ├── legal.py              # Ownership Declarations & Agreements
│   │   └── audit.py              # AuditLog
│   ├── schemas/                  # Pydantic v2 Request & Response schemas
│   └── routers/                  # REST endpoints
│       ├── auth.py               # Register, login, refresh, logout
│       ├── users.py              # Me, public profile, POPIA export
│       ├── missions.py           # CRUD, publish, archive, discovery
│       ├── documents.py          # Upload (50MB quota check), list, delete
│       ├── collaboration.py      # Requests, invitations, accept/decline
│       ├── messages.py           # Mission-context messaging
│       ├── marketplace.py        # Listing, 10-dimension evaluation, fee preview
│       ├── purchases.py          # Purchase access, license selection
│       ├── notifications.py      # In-app notifications
│       ├── settings.py           # Appearance (Dark mode), R100/mo Go Premium
│       ├── legal.py              # Ownership declaration, agreement consent
│       └── audit.py              # Audit trail retrieval
├── api_examples/
│   └── frontend_fetch_examples.js # Production Vanilla JS client example
└── tests/
    ├── test_permissions.py       # Full permission & masking tests
    └── test_standalone_logic.py  # Zero-dependency Python unit tests
```

---

## Key Domain Rules

### 1. Mission Privacy & Marketplace Masking
* Every Mission is **PRIVATE** by default.
* In public marketplace areas, unauthenticated visitors or unpurchased buyers can **ONLY** see:
  - Mission Heading
  - Problem Statement
  - Non-confidential summary and industry
* Full findings, lessons learned, formulas, technical details, and documents are **cryptographically protected and redacted on the server**.

### 2. Marketplace Fees
* Direct Transaction (buyer discovered independently): **Continuum 8%**, Seller 92%.
* Assisted Transaction (Continuum introduced buyer): **Continuum 15%**, Seller 85%.
* Backend calculates fees automatically. Never trust client values.

### 3. Storage Quotas
* Free tier: **50 MB** cumulative storage per Mission.
* Premium tier (R100 / month): **Unlimited** mission documents (with standard 1 GB single file infrastructure limit).

### 4. POPIA Compliance (South Africa)
* Permanent Continuum IDs (e.g. `CNT-7F42-91K8`) are generated with cryptographically secure random entropy and never contain email or personal data.
* Exact user residential addresses are never exposed publicly.
* Facial/biometric recovery is strictly opt-in and operates via ephemeral Zero-Knowledge or external KYC token without raw biometric storage.
* Full audit trail stored in `audit_logs`.

---

## Installation & Running

```bash
# 1. Setup Virtual Environment
python3 -m venv venv
source venv/bin/activate

# 2. Install Dependencies
pip install -r backend/requirements.txt

# 3. Configure Environment
cp backend/.env.example backend/.env

# 4. Run Migrations
alembic -c backend/alembic.ini upgrade head

# 5. Start Development Server
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# 6. Run Automated Tests
python3 -m unittest backend/tests/test_standalone_logic.py
```
