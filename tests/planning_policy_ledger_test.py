import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
import uuid
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "souroldgeezer-policy/skills/planning-policy/references/scripts/planning_ledger.py"
SPEC = importlib.util.spec_from_file_location("planning_ledger", SCRIPT)
ledger = importlib.util.module_from_spec(SPEC); assert SPEC.loader is not None; SPEC.loader.exec_module(ledger)

class PlanningLedgerTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name).resolve(); self.common=["--ledger-root",str(self.root),"--plan-id","approved-plan"]
        assignment={"harness":"codex","tier":"standard","model_or_alias":"inherit","effort":"inherit","worktree":".worktrees/approved-plan"}
        self.steps=json.dumps([{"id":"build","summary":"Build helper",**assignment},{"id":"verify","dependencies":["build"],**assignment}])
    def tearDown(self): self.temp.cleanup()
    def invoke(self,*args):
        with contextlib.redirect_stdout(io.StringIO()): return ledger.main(list(args))
    def output(self,*args):
        with contextlib.redirect_stdout(io.StringIO()) as out: code=ledger.main(list(args))
        return code,json.loads(out.getvalue())
    def test_v1_legacy_is_unchanged_and_disclosed(self):
        self.assertEqual(0,self.invoke(*self.common,"init","--actor","parent","--approved","--steps-json",self.steps))
        self.assertEqual(0,self.invoke(*self.common,"transition","--actor","parent","--step-id","build","--to","ready"))
        code,shown=self.output(*self.common,"show"); self.assertEqual(0,code); self.assertEqual(1,shown["legacy_schema"]); self.assertTrue(shown["rehydration_incomplete"]); self.assertEqual("legacy_unbounded",shown["retry_policy"])
    def plan(self):
        leaves=[]
        for name in ("build","verify"):
            leaves.append({"id":name,"dependencies":[] if name=="build" else ["build"],"task":"x","boundary":"x","read_set":["x"],"write_set":["x"],"settled_decisions":"x","size":"small","portable_tier":"standard","worktree_owner":"parent","acceptance_command":"true","return_contract":"bounded-step-return-v1","stop_conditions":["missing_load_bearing_information"],"work_unit_id":name,"max_attempts":2})
        value={"contract_version":2,"objective":"x","scope_summary":"x","approved_decisions":["x"],"leaves":leaves,"work_units":[{"id":"build","original_size":"small"},{"id":"verify","original_size":"small"}]}; path=self.root/"plan.json"; path.write_text(json.dumps(value)); return path,value
    def init_v2(self,run="run-a"):
        plan,_=self.plan(); assignments=json.dumps([{"step_id":x,"agent_id":str(uuid.uuid4()),"attempt_id":str(uuid.uuid4())} for x in ("build","verify")]); return self.output(*self.common,"init-v2","--actor","parent","--approved","--run-id",run,"--plan",str(plan),"--assignments-json",assignments)
    def test_v2_isolates_twenty_runs_and_requires_assignment_identity(self):
        for number in range(20): self.assertEqual(0,self.init_v2(f"run-{number}")[0])
        self.assertEqual(20,len(list((self.root/"planning-policy/ledgers/approved-plan/runs").iterdir())))
        code,payload=self.output(*self.common,"show","--run-id","run-0"); self.assertEqual(0,code); self.assertEqual(2,payload["schema_version"]); self.assertFalse(payload["rehydration_incomplete"])
        self.assertEqual(3,self.invoke(*self.common,"transition","--actor","parent","--run-id","run-0","--step-id","build","--to","ready"))
    def test_v2_return_convergence_and_tamper(self):
        self.assertEqual(0,self.init_v2()[0]); checkpoint=json.loads((self.root/"planning-policy/ledgers/approved-plan/runs/run-a/checkpoint.json").read_text()); step=checkpoint["steps"]["build"]
        self.assertEqual(0,self.invoke(*self.common,"transition","--actor","parent","--run-id","run-a","--step-id","build","--to","ready","--agent-id",step["agent_id"],"--attempt-id",step["attempt_id"]))
        self.assertEqual(0,self.invoke(*self.common,"transition","--actor","parent","--run-id","run-a","--step-id","build","--to","in_progress"))
        returned={"return_contract":"bounded-step-return-v1","plan_id":"approved-plan","run_id":"run-a","step_id":"build","attempt_id":step["attempt_id"],"agent_id":step["agent_id"],"status":"completed","changed_paths":[],"acceptance":{"command":"true","exit_code":0},"blockers":{"code":"","summary":"","evidence_path":"","sha256":""},"notes":[],"commit_hash":"a"*40,"unstarted_remainder":""}; returned_path=self.root/"return.json"; returned_path.write_text(json.dumps(returned))
        self.assertEqual(0,self.invoke(*self.common,"ingest-return","--actor","parent","--run-id","run-a","--return-file",str(returned_path)))
        plan_path=self.root/"planning-policy/ledgers/approved-plan/runs/run-a/plan.json"; plan_path.write_text("{}")
        self.assertEqual(3,self.invoke(*self.common,"validate","--run-id","run-a"))
if __name__=="__main__": unittest.main()
