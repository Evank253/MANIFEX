from dataclasses import dataclass, field


@dataclass(frozen=True)
class Opportunity:
    opportunity_id: str
    title: str
    required_capabilities: tuple[str, ...]


@dataclass
class ProfessionalProfile:
    subject_id: str
    shared_record_ids: list[str] = field(default_factory=list)

    def share(self, record_ids: list[str]) -> None:
        for record_id in record_ids:
            if record_id not in self.shared_record_ids:
                self.shared_record_ids.append(record_id)


@dataclass(frozen=True)
class CapabilityMatch:
    opportunity_id: str
    matched_capabilities: tuple[str, ...]
    evidence_ids: tuple[str, ...]


def match_capabilities(opportunity: Opportunity, demonstrated: dict[str, tuple[str, ...]]) -> CapabilityMatch:
    matched = tuple(cap for cap in opportunity.required_capabilities if cap in demonstrated)
    evidence = tuple(evidence_id for cap in matched for evidence_id in demonstrated[cap])
    return CapabilityMatch(opportunity.opportunity_id, matched, evidence)
