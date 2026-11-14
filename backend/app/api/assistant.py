from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.assistant_service import build_assistant_response
from app.services.analysis_service import get_analysis_for_user

router = APIRouter()


class AssistantAskRequest(BaseModel):
    question: str


@router.post("/{analysis_id}/ask")
def ask_assistant(
    analysis_id: int,
    payload: AssistantAskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_analysis_for_user(db, analysis_id, current_user.id)
    return build_assistant_response(db, payload.question, analysis_id)
