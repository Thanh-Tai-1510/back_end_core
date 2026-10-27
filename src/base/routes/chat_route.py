from typing import Annotated

from fastapi import APIRouter

from src.base.controllers.deps import ChatServiceDep, require_permission
from src.base.controllers.chat_controller import ChatController
from src.core.permissions import PermissionCode
from src.base.models.user import User
from src.base.requests.chat_request import ChatRequest
from src.base.responses.chat_response import ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])
controller = ChatController()


@router.post("", response_model=ChatResponse)
def send_message(
    request: ChatRequest,
    current_user: Annotated[User, require_permission(PermissionCode.CHAT_SEND)],
    chat_service: ChatServiceDep,
) -> ChatResponse:
    return controller.send_message(request, current_user, chat_service)
