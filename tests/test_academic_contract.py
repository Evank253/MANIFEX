from dataclasses import FrozenInstanceError
import unittest
from manifex_core.academic_contract import AppendOnlyHistory,AssessmentResult,AssessmentSpecification,Benchmark,CanonicalReference,ContractError,HistoricalLineage,QualificationStatus,recompute_qualification,validate_lineage
H='a'*64; B='b'*64
class AcademicContractTests(unittest.TestCase):
 def setUp(self):
  self.discipline=CanonicalReference('Discipline','math','1',H); self.domain=CanonicalReference('Domain','calculus','1',H); self.concept=CanonicalReference('Concept','derivatives','1',H)
  self.spec=AssessmentSpecification('CALC-APP-001','2','calculus.derivatives.application',self.discipline,self.domain,(self.concept,),'application','E4')
  self.benchmark=Benchmark('CALC-APP-001-B1','2',self.spec.reference,(),B,H,True,B)
  self.evaluation=CanonicalReference('EvaluationSpecification','eval-1','1',H)
  self.result=AssessmentResult('result-1','1',self.spec.reference,self.benchmark.reference,self.evaluation,(),'RUN-TEST-001')
  self.replication=CanonicalReference('ReplicationResult','rep-1','1',H); self.verification=CanonicalReference('VerificationEvidence','ver-1','1',H); self.qualification=CanonicalReference('Qualification','qual-1','1',H)
 def test_immutable(self):
  with self.assertRaises(FrozenInstanceError): self.spec.assessment_id='changed'
 def test_reference_is_not_ownership(self): self.assertEqual(self.concept.object_type,'Concept')
 def test_sealed_benchmark_identity(self): self.assertTrue(self.benchmark.sealed); self.assertEqual(self.benchmark.seal_hash,self.benchmark.content_hash)
 def test_exact_versions(self): self.assertEqual(self.result.assessment_ref.version,'2'); self.assertEqual(self.result.benchmark_ref.version,'2')
 def test_append_only(self):
  h=AppendOnlyHistory(); h.append(self.result.reference)
  with self.assertRaises(ContractError): h.append(self.result.reference)
 def test_complete_lineage(self):
  l=HistoricalLineage(self.spec.capability_id,self.qualification,self.verification,self.replication,self.result.reference,self.benchmark.reference,self.spec.reference,self.concept)
  refs=(self.qualification,self.verification,self.replication,self.result.reference,self.benchmark.reference,self.spec.reference,self.concept)
  self.assertTrue(validate_lineage(l,refs)); self.assertEqual(recompute_qualification(lineage=l,references=refs,replication_agrees=True,verification_independent=True,benchmark_valid=True,evidence_present=True),QualificationStatus.QUALIFIED)
 def test_missing_lineage_is_not_measured(self):
  l=HistoricalLineage(self.spec.capability_id,self.qualification,self.verification,self.replication,self.result.reference,self.benchmark.reference,self.spec.reference,CanonicalReference('Concept','missing','1',H))
  refs=(self.qualification,self.verification,self.replication,self.result.reference,self.benchmark.reference,self.spec.reference)
  self.assertEqual(recompute_qualification(lineage=l,references=refs,replication_agrees=True,verification_independent=True,benchmark_valid=True,evidence_present=True),QualificationStatus.NOT_MEASURED)
 def test_failed_predicate_is_not_missing_evidence(self):
  l=HistoricalLineage(self.spec.capability_id,self.qualification,self.verification,self.replication,self.result.reference,self.benchmark.reference,self.spec.reference,self.concept)
  refs=(self.qualification,self.verification,self.replication,self.result.reference,self.benchmark.reference,self.spec.reference,self.concept)
  self.assertEqual(recompute_qualification(lineage=l,references=refs,replication_agrees=False,verification_independent=True,benchmark_valid=True,evidence_present=True),QualificationStatus.NOT_QUALIFIED)
