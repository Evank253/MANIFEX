from dataclasses import dataclass


@dataclass(frozen=True)
class CompanionConstitution:
    human_sovereignty: bool = True
    non_manipulation: bool = True
    non_diagnosis: bool = True
    privacy_by_default: bool = True
    explicit_consent: bool = True
    reversible_actions: bool = True
    human_approval_for_consequential_actions: bool = True
    no_emotional_dependency: bool = True
    no_automatic_personal_to_professional_crossover: bool = True

    def validate(self) -> None:
        required = {
            "human_sovereignty": self.human_sovereignty,
            "non_manipulation": self.non_manipulation,
            "non_diagnosis": self.non_diagnosis,
            "privacy_by_default": self.privacy_by_default,
            "explicit_consent": self.explicit_consent,
            "reversible_actions": self.reversible_actions,
            "human_approval_for_consequential_actions": self.human_approval_for_consequential_actions,
            "no_emotional_dependency": self.no_emotional_dependency,
            "no_automatic_personal_to_professional_crossover": self.no_automatic_personal_to_professional_crossover,
        }
        failed = [name for name, enabled in required.items() if not enabled]
        if failed:
            raise ValueError(f"constitutional invariants disabled: {', '.join(failed)}")


CONSTITUTION = CompanionConstitution()
CONSTITUTION.validate()
