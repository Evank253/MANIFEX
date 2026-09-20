from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable

from .companion import HumanAICompanion
from .consent import ConsentManager
from .credentials import Credential
from .discovery import DiscoveryEngine, DiscoveryObservation
from .evidence import EvidenceChain
from .learning import AssessmentResult, LearningEngine, LearningObjective
from .life_log import LifeEntry, LifeLog
from .models import EvidenceState, HumanDecision, Record, RecordKind, World
from .passport import HumanCapabilityPassport
from .professional import Opportunity, ProfessionalProfile, match_capabilities


@dataclass
class CompanionRuntime:
    subject_id: str
    companion: HumanAICompanion = field(init=False)
    consent: ConsentManager = field(default_factory=ConsentManager)
    learning: LearningEngine = field(default_factory=LearningEngine)
    discovery: DiscoveryEngine = field(default_factory=DiscoveryEngine)
    life_log: LifeLog = field(init=False)
    passport: HumanCapabilityPassport = field(init=False)
    professional: ProfessionalProfile = field(init=False)
    credentials: dict[str, Credential] = field(default_factory=dict)
    evidence_chains: dict[str, EvidenceChain] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.companion = HumanAICompanion(self.subject_id)
        self.life_log = LifeLog(self.subject_id)
        self.passport = HumanCapabilityPassport(self.subject_id)
        self.professional = ProfessionalProfile(self.subject_id)

    def now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def add_life_entry(self, entry: LifeEntry) -> None:
        self.life_log.add(entry)
        self.companion.record(Record(entry.entry_id, self.subject_id, World.PERSONAL, RecordKind.MEMORY, {"content": entry.content}, EvidenceState.REPORTED, self._provenance(entry.entry_id)))

    def add_learning_objective(self, objective: LearningObjective) -> None:
        self.learning.add_objective(objective)

    def assess(self, result: AssessmentResult) -> None:
        self.learning.record_assessment(result)
        self.companion.record(Record(result.assessment_id, self.subject_id, World.DEVELOPMENT, RecordKind.ASSESSMENT, {"capability_id": result.capability_id, "score": result.score, "passed": result.passed, "raw_result_id": result.raw_result_id}, EvidenceState.ASSESSED, self._provenance(result.assessment_id)))

    def discover(self, observation: DiscoveryObservation) -> None:
        self.discovery.observe(observation)

    def register_evidence_chain(self, evidence_id: str, chain: EvidenceChain) -> None:
        chain.validate()
        self.evidence_chains[evidence_id] = chain

    def create_credential(self, credential: Credential, evidence_states: dict[str, EvidenceState], requirements_passed: set[str], human_approved: bool) -> None:
        credential.validate(evidence_states, requirements_passed, human_approved)
        self.credentials[credential.credential_id] = credential
        self.passport.credentials.append(credential.credential_id)

    def build_capability_match(self, opportunity: Opportunity, demonstrated: dict[str, tuple[str, ...]]):
        return match_capabilities(opportunity, demonstrated)

    def authorize(self, decision: HumanDecision) -> None:
        self.companion.authorize_consequential_action(decision)

    def _provenance(self, source_id: str):
        from .models import Provenance
        return Provenance(source_id, "runtime", source_id, self.now(), "HUMAN_OR_SYSTEM")
