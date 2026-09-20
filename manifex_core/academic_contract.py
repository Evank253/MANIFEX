from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import hashlib,json
from typing import Iterable,Mapping

class ContractError(ValueError): pass
class StateClass(str,Enum): HISTORICAL='historical'; DERIVED='derived'
class QualificationStatus(str,Enum): QUALIFIED='QUALIFIED'; NOT_QUALIFIED='NOT_QUALIFIED'; NOT_MEASURED='NOT_MEASURED'; FAILED='FAILED'; BLOCKED='BLOCKED'; QUARANTINED='QUARANTINED'
class Owner(str,Enum): EDUCATION='education'; ASSESSMENT='assessment'; EVIDENCE='evidence'; TWIN='twin'; VERIFICATION='verification'; MASTERY='mastery'; QUALIFICATION='qualification'; INTELLIGENCE='intelligence'; ROUTER='router'
HISTORICAL_OBJECTS=frozenset({'AssessmentSpecification','Benchmark','BenchmarkItem','AssessmentResult','ResultItem','AssessmentEvidence','ReplicationResult','VerificationEvidence'})
DERIVED_OBJECTS=frozenset({'MasteryAssessment','MasteryRecord','Qualification','CapabilityAvailability','RoutingEligibility'})
OWNER_BY_OBJECT={**{x:Owner.EDUCATION for x in ('EducationalSystem','InstitutionType','EducationLevel','Discipline','Domain','Concept','Prerequisite','LearningObjective','Pedagogy','Curriculum','Assessment','Skill','Competency','LearningPath','TeachingStrategy','Misconception')},**{x:Owner.ASSESSMENT for x in ('AssessmentSpecification','Benchmark','BenchmarkItem','EvaluationSpecification','RubricCriterion','BenchmarkValidityReport','AssessmentResult','ResultItem')},'AssessmentEvidence':Owner.EVIDENCE,'ReplicationResult':Owner.TWIN,'VerificationEvidence':Owner.VERIFICATION,'MasteryAssessment':Owner.MASTERY,'MasteryRecord':Owner.MASTERY,'Qualification':Owner.QUALIFICATION,'CapabilityAvailability':Owner.INTELLIGENCE,'RoutingEligibility':Owner.ROUTER}

def canonical_hash(value):
 def n(x):
  if isinstance(x,Enum): return x.value
  if hasattr(x,'__dataclass_fields__'): return {k:n(getattr(x,k)) for k in x.__dataclass_fields__}
  if isinstance(x,Mapping): return {str(k):n(v) for k,v in sorted(x.items(),key=lambda p:str(p[0]))}
  if isinstance(x,(tuple,list,set,frozenset)): return sorted((n(v) for v in x),key=lambda v:json.dumps(v,sort_keys=True,separators=(',',':')))
  return x
 return hashlib.sha256(json.dumps(n(value),sort_keys=True,separators=(',',':')).encode()).hexdigest()

@dataclass(frozen=True)
class CanonicalReference:
 object_type:str; object_id:str; version:str; content_hash:str; schema_version:str='1'; provenance_ref:str|None=None
 def __post_init__(self):
  if self.object_type not in OWNER_BY_OBJECT: raise ContractError(f'unknown object type: {self.object_type}')
  if not self.object_id or not self.version: raise ContractError('canonical reference requires id and version')
  if len(self.content_hash)!=64: raise ContractError('content_hash must be SHA-256')
  int(self.content_hash,16)

@dataclass(frozen=True)
class AssessmentSpecification:
 assessment_id:str; version:str; capability_id:str; discipline_ref:CanonicalReference; domain_ref:CanonicalReference; concept_refs:tuple[CanonicalReference,...]; dimension:str; target_level:str; prerequisite_refs:tuple[CanonicalReference,...]=(); schema_version:str='1'
 @property
 def reference(self): return CanonicalReference('AssessmentSpecification',self.assessment_id,self.version,canonical_hash(self))

@dataclass(frozen=True)
class Benchmark:
 benchmark_id:str; version:str; specification_ref:CanonicalReference; item_refs:tuple[CanonicalReference,...]; content_hash:str; rubric_hash:str; sealed:bool=False; seal_hash:str|None=None; schema_version:str='1'
 def __post_init__(self):
  if self.specification_ref.object_type!='AssessmentSpecification': raise ContractError('benchmark must reference AssessmentSpecification')
  if len(self.content_hash)!=64: raise ContractError('benchmark content_hash must be SHA-256')
  if self.sealed and self.seal_hash!=self.content_hash: raise ContractError('sealed benchmark requires seal_hash == content_hash')
 @property
 def reference(self): return CanonicalReference('Benchmark',self.benchmark_id,self.version,self.content_hash)

@dataclass(frozen=True)
class AssessmentResult:
 result_id:str; version:str; assessment_ref:CanonicalReference; benchmark_ref:CanonicalReference; evaluation_ref:CanonicalReference; result_item_refs:tuple[CanonicalReference,...]; execution_provenance:str; sealed:bool=True
 def __post_init__(self):
  if self.assessment_ref.object_type!='AssessmentSpecification' or self.benchmark_ref.object_type!='Benchmark' or self.evaluation_ref.object_type!='EvaluationSpecification': raise ContractError('assessment result references invalid object type')
  if not self.execution_provenance: raise ContractError('assessment result requires execution provenance')
 @property
 def reference(self): return CanonicalReference('AssessmentResult',self.result_id,self.version,canonical_hash(self))

@dataclass(frozen=True)
class AssessmentEvidence:
 evidence_id:str; version:str; result_ref:CanonicalReference; artifact_hash:str; provenance_ref:str; independently_verified:bool=False
 @property
 def reference(self): return CanonicalReference('AssessmentEvidence',self.evidence_id,self.version,canonical_hash(self),provenance_ref=self.provenance_ref)

@dataclass(frozen=True)
class ReplicationResult:
 replication_id:str; version:str; primary_result_ref:CanonicalReference; twin_result_ref:CanonicalReference; independence_level:str; agreement:bool; comparison_hash:str; sealed:bool=True
 def __post_init__(self):
  if any(r.object_type!='AssessmentResult' for r in (self.primary_result_ref,self.twin_result_ref)): raise ContractError('replication requires AssessmentResult refs')
 @property
 def reference(self): return CanonicalReference('ReplicationResult',self.replication_id,self.version,canonical_hash(self))

@dataclass(frozen=True)
class VerificationEvidence:
 verification_id:str; version:str; replication_ref:CanonicalReference; verifier:str; independently_verified:bool; verification_hash:str
 @property
 def reference(self): return CanonicalReference('VerificationEvidence',self.verification_id,self.version,canonical_hash(self))

@dataclass(frozen=True)
class MasteryAssessment:
 mastery_assessment_id:str; target_id:str; evidence_refs:tuple[CanonicalReference,...]; assessment_refs:tuple[CanonicalReference,...]; derived_from_hash:str; evidence_grounded:bool
 @property
 def reference(self): return CanonicalReference('MasteryAssessment',self.mastery_assessment_id,'1',canonical_hash(self))

@dataclass(frozen=True)
class MasteryRecord:
 mastery_record_id:str; target_id:str; level:str; mastery_assessment_ref:CanonicalReference; evidence_refs:tuple[CanonicalReference,...]; derived_from_hash:str
 @property
 def reference(self): return CanonicalReference('MasteryRecord',self.mastery_record_id,'1',canonical_hash(self))

@dataclass(frozen=True)
class Qualification:
 qualification_id:str; capability_id:str; status:QualificationStatus; mastery_ref:CanonicalReference; assessment_ref:CanonicalReference; replication_ref:CanonicalReference; verification_ref:CanonicalReference; evidence_ref:CanonicalReference; lineage_hash:str
 @property
 def reference(self): return CanonicalReference('Qualification',self.qualification_id,'1',canonical_hash(self))

@dataclass(frozen=True)
class CapabilityAvailability:
 capability_id:str; qualification_ref:CanonicalReference; evidence_level:str; status:QualificationStatus; projection_hash:str
 @property
 def reference(self): return CanonicalReference('CapabilityAvailability',self.capability_id,'1',canonical_hash(self))

@dataclass(frozen=True)
class RoutingEligibility:
 capability_id:str; availability_ref:CanonicalReference; eligible:bool; routing_hash:str
 @property
 def reference(self): return CanonicalReference('RoutingEligibility',self.capability_id,'1',canonical_hash(self))

@dataclass(frozen=True)
class HistoricalLineage:
 capability_id:str; qualification_ref:CanonicalReference; verification_ref:CanonicalReference; replication_ref:CanonicalReference; assessment_result_ref:CanonicalReference; benchmark_ref:CanonicalReference; assessment_specification_ref:CanonicalReference; concept_ref:CanonicalReference

class AppendOnlyHistory:
 def __init__(self): self._records={}
 def append(self,ref):
  key=(ref.object_id,ref.version)
  if key in self._records: raise ContractError(f'historical record already exists: {key}')
  if ref.object_type not in HISTORICAL_OBJECTS: raise ContractError(f'{ref.object_type} is not historical state')
  self._records[key]=ref
 def contains(self,ref): return self._records.get((ref.object_id,ref.version))==ref
 def snapshot(self): return tuple(self._records.values())

def validate_lineage(lineage,references:Iterable[CanonicalReference]):
 refs={(r.object_type,r.object_id,r.version,r.content_hash) for r in references}
 chain=(lineage.qualification_ref,lineage.verification_ref,lineage.replication_ref,lineage.assessment_result_ref,lineage.benchmark_ref,lineage.assessment_specification_ref,lineage.concept_ref)
 kinds=('Qualification','VerificationEvidence','ReplicationResult','AssessmentResult','Benchmark','AssessmentSpecification','Concept')
 return all(r.object_type==k and (r.object_type,r.object_id,r.version,r.content_hash) in refs for r,k in zip(chain,kinds))

def recompute_qualification(*,lineage,references,replication_agrees,verification_independent,benchmark_valid,evidence_present):
 if not validate_lineage(lineage,references): return QualificationStatus.NOT_MEASURED
 if not all((replication_agrees,verification_independent,benchmark_valid,evidence_present)): return QualificationStatus.NOT_QUALIFIED
 return QualificationStatus.QUALIFIED
