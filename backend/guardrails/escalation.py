from app.schemas import QueryResponse


class EscalationEngine:
    WEAK_CONFIDENCE_MSG = (
        "⚠️ I'm not fully confident in this answer. "
        "It has been escalated to a human support agent who will follow up shortly."
    )

    def apply(self, response: QueryResponse) -> QueryResponse:
        if response.escalated:
            response.answer = (
                f"{self.WEAK_CONFIDENCE_MSG}\n\nHere's what I found:\n\n{response.answer}"
            )
        return response
