from dataclasses import dataclass
from typing import Protocol, Sequence

from .models import HumanDecision


class CompanionProvider(Protocol):
    def respond(self, messages: Sequence[str], context: Sequence[str] = ()) -> str: ...


@dataclass(frozen=True)
class ProviderResponse:
    text: str
    provider_id: str
    model_id: str
    source_ids: tuple[str, ...] = ()


class GovernedProvider:
    def __init__(self, provider: CompanionProvider, provider_id: str, model_id: str) -> None:
        self.provider = provider
        self.provider_id = provider_id
        self.model_id = model_id

    def respond(self, messages: Sequence[str], context: Sequence[str] = ()) -> ProviderResponse:
        text = self.provider.respond(messages, context)
        if not isinstance(text, str) or not text.strip():
            raise ValueError('provider must return non-empty text')
        return ProviderResponse(text, self.provider_id, self.model_id)

    def consequential_action(self, decision: HumanDecision) -> None:
        if not decision.authorized or decision.decided_by != 'HUMAN':
            raise PermissionError('provider cannot authorize consequential actions')
