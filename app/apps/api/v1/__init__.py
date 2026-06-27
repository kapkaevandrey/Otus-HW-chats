import logging

from fastapi import APIRouter

from .dialog import dialog_router


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1")

router.include_router(dialog_router)
