from fastapi import HTTPException, status

from src.base.controllers.deps import ChatServiceDep
from src.base.models.user import User
from src.base.requests.chat_request import ChatRequest
from src.base.responses.chat_response import ChatResponse
from src.core.logging import Loggers, get_logger

logger = get_logger(Loggers.API)


class ChatController:
    def send_message(
        self,
        request: ChatRequest,
        current_user: User,
        chat_service: ChatServiceDep,
    ) -> ChatResponse:
        try:
            reply, session_id, raw = chat_service.send_message(
                user=current_user,
                message=request.message,
                session_id=request.session_id,
            )
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

        logger.info("Chat message processed: user_id=%s session_id=%s", current_user.id, session_id)
        return ChatResponse(reply=reply, session_id=session_id, raw=raw)
