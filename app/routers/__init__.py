from fastapi import APIRouter
from backend.app.routers.auth import router as auth_router
from backend.app.routers.users import router as users_router
from backend.app.routers.missions import router as missions_router
from backend.app.routers.documents import router as documents_router
from backend.app.routers.collaboration import router as collaboration_router
from backend.app.routers.messages import router as messages_router
from backend.app.routers.marketplace import router as marketplace_router
from backend.app.routers.purchases import router as purchases_router
from backend.app.routers.notifications import router as notifications_router
from backend.app.routers.settings import router as settings_router
from backend.app.routers.legal import router as legal_router
from backend.app.routers.audit import router as audit_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(missions_router)
api_router.include_router(documents_router)
api_router.include_router(collaboration_router)
api_router.include_router(messages_router)
api_router.include_router(marketplace_router)
api_router.include_router(purchases_router)
api_router.include_router(notifications_router)
api_router.include_router(settings_router)
api_router.include_router(legal_router)
api_router.include_router(audit_router)
