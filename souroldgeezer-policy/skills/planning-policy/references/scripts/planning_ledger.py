#!/usr/bin/env python3
"""Parent-owned durable ledger.  ``init`` is the legacy v1 interface; use ``init-v2``.

Every command emits one compact JSON object.  v2 state is isolated by run id
under a plan ledger and records only bounded handoffs, never agent transcripts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
V2_SCHEMA_VERSION = 2
CHECKPOINT_MAX_BYTES = 16 * 1024
RETURN_MAX_BYTES = 8 * 1024
SHOW_MAX_PROXY_TOKENS = 1200
PARENT_ACTOR = "parent"
IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
BLOCKER_CODE = re.compile(r"^blocked:[a-z][a-z0-9_]{0,63}$")
COMMIT_HASH = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
PROXY_TOKEN_RE = re.compile(r"\w+|[^\w\s]")
STATES = {"pending", "ready", "in_progress", "completed", "integrated", "blocked", "failed", "superseded", "discarded"}
TRANSITIONS = {"pending": {"ready", "superseded", "discarded"}, "ready": {"in_progress", "blocked", "superseded", "discarded"}, "in_progress": {"completed", "blocked", "failed", "superseded", "discarded"}, "blocked": {"ready", "superseded", "discarded"}, "failed": {"ready", "superseded", "discarded"}, "completed": {"integrated", "discarded"}, "integrated": set(), "superseded": set(), "discarded": set()}

class LedgerError(Exception): pass

def utc_now() -> str: return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
def emit(payload: dict[str, Any], code: int = 0) -> int:
    print(json.dumps(payload, sort_keys=True, separators=(",", ":"))); return code
def canonical(value: Any) -> bytes: return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
def sha256(value: Any) -> str: return hashlib.sha256(canonical(value)).hexdigest()
def safe_identifier(value: str, label: str) -> str:
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value): raise LedgerError(f"invalid {label}: use 1-128 letters, digits, '.', '_' or '-'")
    return value
def canonical_uuid4(value: Any, label: str) -> str:
    if not isinstance(value, str): raise LedgerError(f"{label} must be a canonical UUID4")
    try: parsed = uuid.UUID(value)
    except ValueError as exc: raise LedgerError(f"{label} must be a canonical UUID4") from exc
    if parsed.version != 4 or str(parsed) != value: raise LedgerError(f"{label} must be a canonical UUID4")
    return value
def relative_path(value: Any, label: str = "path") -> str:
    if not isinstance(value, str) or not value or len(value) > 512: raise LedgerError(f"{label} must be a bounded relative path")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts: raise LedgerError(f"{label} must be a bounded relative path")
    return value

def git_common_dir(repo_root: Path) -> Path:
    result = subprocess.run(["git", "-C", str(repo_root), "rev-parse", "--git-common-dir"], text=True, capture_output=True, check=False)
    if result.returncode: raise LedgerError("not a Git worktree; pass --ledger-root for a persistent non-Git root")
    common = Path(result.stdout.strip()); return (repo_root / common).resolve() if not common.is_absolute() else common.resolve()
def ledger_root(args: argparse.Namespace) -> Path:
    if args.ledger_root:
        supplied = Path(args.ledger_root).expanduser()
        if not supplied.is_absolute(): raise LedgerError("--ledger-root must be an absolute persistent path")
        return supplied.resolve() / "planning-policy" / "ledgers"
    return git_common_dir(Path(args.repo_root or Path.cwd()).expanduser().resolve()) / "planning-policy" / "ledgers"
def ledger_dir(args: argparse.Namespace) -> Path: return ledger_root(args) / safe_identifier(args.plan_id, "plan id")
def checkpoint_path(directory: Path, run_id: str | None = None) -> Path:
    return directory / "checkpoint.json" if run_id is None else directory / "runs" / safe_identifier(run_id, "run id") / "checkpoint.json"
def atomic_json(path: Path, payload: dict[str, Any], maximum: int = CHECKPOINT_MAX_BYTES) -> None:
    content = canonical(payload) + b"\n"
    if len(content) > maximum: raise LedgerError(f"checkpoint exceeds {maximum} bytes")
    path.parent.mkdir(parents=True, exist_ok=True); descriptor, temporary = tempfile.mkstemp(prefix=".checkpoint-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle: handle.write(content); handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)
def append_event(path: Path, event: dict[str, Any]) -> None:
    encoded = canonical(event) + b"\n"; path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("ab") as handle: handle.write(encoded); handle.flush(); os.fsync(handle.fileno())

# v1 is deliberately retained: its schema and unbounded retry policy are visible
# in read results, but its stored checkpoint remains byte-compatible with v1.
def parse_steps(raw: str) -> dict[str, dict[str, Any]]:
    try: values = json.loads(raw)
    except json.JSONDecodeError as exc: raise LedgerError(f"invalid --steps-json: {exc.msg}") from exc
    if not isinstance(values, list) or len(values) < 2: raise LedgerError("--steps-json must be a JSON list with at least two delegated steps")
    steps = {}
    for item in values:
        if not isinstance(item, dict): raise LedgerError("each step must be a JSON object")
        step_id = safe_identifier(item.get("id", ""), "step id")
        if step_id in steps: raise LedgerError(f"duplicate step id: {step_id}")
        dependencies = item.get("dependencies", [])
        if not isinstance(dependencies, list) or not all(isinstance(dep, str) for dep in dependencies): raise LedgerError(f"step {step_id} dependencies must be a list of ids")
        assignment = {}
        for field in ("harness", "tier", "model_or_alias", "effort", "worktree"):
            value = item.get(field)
            if not isinstance(value, str) or not value.strip() or len(value) > 160: raise LedgerError(f"step {step_id} requires bounded {field}")
            assignment[field] = value
        steps[step_id] = {"id": step_id, "state": "pending", "attempt": 1, "dependencies": dependencies, "summary": str(item.get("summary", ""))[:240], "evidence_paths": [], "blocker_code": "", **assignment}
    if any(step["id"] in step["dependencies"] or any(dep not in steps for dep in step["dependencies"]) for step in steps.values()): raise LedgerError("step has unknown or self dependency")
    return steps
def validate_checkpoint(data: Any) -> list[str]:
    errors=[]
    if not isinstance(data, dict): return ["checkpoint is not an object"]
    if data.get("schema_version") != SCHEMA_VERSION: errors.append("unsupported schema_version")
    try: safe_identifier(data.get("plan_id", ""), "plan id")
    except LedgerError as exc: errors.append(str(exc))
    if data.get("approved") is not True: errors.append("ledger is not approval-gated")
    steps=data.get("steps")
    if not isinstance(steps,dict) or len(steps)<2: errors.append("ledger must have at least two steps")
    elif isinstance(steps,dict):
        for sid, step in steps.items():
            if not isinstance(step,dict) or step.get("id")!=sid: errors.append(f"invalid step record: {sid}"); continue
            if step.get("state") not in STATES: errors.append(f"invalid state for {sid}")
            if not isinstance(step.get("attempt"),int) or step["attempt"]<1: errors.append(f"invalid attempt for {sid}")
            if not isinstance(step.get("dependencies"),list) or any(dep not in steps for dep in step["dependencies"]): errors.append(f"invalid dependencies for {sid}")
            for field in ("harness","tier","model_or_alias","effort","worktree"):
                if not isinstance(step.get(field),str) or not step[field].strip() or len(step[field])>160: errors.append(f"invalid {field} for {sid}")
            blocker=step.get("blocker_code")
            if not isinstance(blocker,str) or (blocker and not BLOCKER_CODE.fullmatch(blocker)): errors.append(f"invalid blocker_code for {sid}")
    if len(canonical(data)+b"\n")>CHECKPOINT_MAX_BYTES: errors.append("checkpoint exceeds 16 KiB")
    return errors
def load_v1(directory: Path) -> dict[str, Any]:
    path=checkpoint_path(directory)
    if not path.is_file(): raise LedgerError("ledger checkpoint does not exist")
    try: data=json.loads(path.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as exc: raise LedgerError(f"cannot read checkpoint: {exc}") from exc
    errors=validate_checkpoint(data)
    if errors: raise LedgerError("invalid checkpoint: "+"; ".join(errors))
    return data
def require_parent(actor:str)->None:
    if actor!=PARENT_ACTOR: raise LedgerError("only actor 'parent' may mutate a ledger")
def init(args):
    require_parent(args.actor)
    if not args.approved: raise LedgerError("--approved is required before ledger creation")
    directory=ledger_dir(args)
    if directory.exists(): raise LedgerError("ledger already exists; init is not an overwrite operation")
    steps=parse_steps(args.steps_json); now=utc_now(); data={"schema_version":1,"plan_id":args.plan_id,"approved":True,"created_at":now,"updated_at":now,"event_sequence":1,"steps":steps}
    atomic_json(checkpoint_path(directory),data); append_event(directory/"events.jsonl",{"sequence":1,"at":now,"actor":"parent","action":"init","plan_id":args.plan_id,"step_count":len(steps)})
    return {"ok":True,"action":"init","ledger":str(directory),"plan_id":args.plan_id,"step_count":len(steps),"legacy_schema":1,"retry_policy":"legacy_unbounded"}
def transition_v1(args):
    require_parent(args.actor); directory=ledger_dir(args); data=load_v1(directory); sid=safe_identifier(args.step_id,"step id")
    if sid not in data["steps"]: raise LedgerError("unknown step id")
    step=data["steps"][sid]; old,new=step["state"],args.to
    if new not in TRANSITIONS[old]: raise LedgerError(f"transition {old} -> {new} is not allowed")
    if new=="ready":
        if old in {"blocked","failed"}:
            if not args.retry or not args.evidence_path or not args.summary: raise LedgerError("retry from blocked or failed requires --retry, --evidence-path, and --summary")
            step["attempt"]+=1
        elif any(data["steps"][d]["state"]!="integrated" for d in step["dependencies"]): raise LedgerError("dependencies must be integrated before a step becomes ready")
    if new=="integrated" and not args.summary: raise LedgerError("integration requires --summary")
    if new=="blocked":
        if not BLOCKER_CODE.fullmatch(args.blocker_code): raise LedgerError("blocked transition requires --blocker-code like blocked:model_unavailable")
        step["blocker_code"]=args.blocker_code
    elif new=="ready": step["blocker_code"]=""
    if args.evidence_path: step["evidence_paths"]=(step["evidence_paths"]+[relative_path(args.evidence_path,"--evidence-path")])[-8:]
    if args.summary: step["summary"]=args.summary[:240]
    step["state"]=new; now=utc_now(); seq=data["event_sequence"]+1; data["event_sequence"]=seq; data["updated_at"]=now
    atomic_json(checkpoint_path(directory),data); append_event(directory/"events.jsonl",{"sequence":seq,"at":now,"actor":"parent","action":"transition","plan_id":data["plan_id"],"step_id":sid,"from":old,"to":new,"attempt":step["attempt"],"summary":step["summary"],"evidence_path":args.evidence_path or "","blocker_code":step["blocker_code"]})
    return {"ok":True,"action":"transition","step_id":sid,"from":old,"to":new,"attempt":step["attempt"],"legacy_schema":1,"retry_policy":"legacy_unbounded"}

def read_plan(path: str) -> tuple[dict[str,Any],str]:
    try: plan=json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as exc: raise LedgerError(f"cannot read plan: {exc}") from exc
    try:
        from validate_plan_contract import validate
    except ImportError:
        import importlib.util
        spec=importlib.util.spec_from_file_location("validate_plan_contract",Path(__file__).with_name("validate_plan_contract.py")); module=importlib.util.module_from_spec(spec); assert spec.loader; spec.loader.exec_module(module); validate=module.validate
    result=validate(plan)
    if not result.get("valid") or not result.get("dispatch_ready"): raise LedgerError("plan is not a valid dispatch-ready contract version 2: "+"; ".join(result.get("errors",[])))
    return plan,sha256(plan)
def parse_assignments(raw:str, plan:dict[str,Any])->dict[str,dict[str,str]]:
    try: values=json.loads(raw)
    except json.JSONDecodeError as exc: raise LedgerError(f"invalid --assignments-json: {exc.msg}") from exc
    if not isinstance(values,list): raise LedgerError("--assignments-json must be a JSON list")
    leaf_ids={leaf["id"] for leaf in plan["leaves"]}; output={}
    for value in values:
        if not isinstance(value,dict): raise LedgerError("each assignment must be an object")
        sid=safe_identifier(value.get("step_id",value.get("id","")),"step id")
        if sid in output or sid not in leaf_ids: raise LedgerError("assignments must join each approved plan leaf exactly once")
        output[sid]={"agent_id":canonical_uuid4(value.get("agent_id"),"agent_id"),"attempt_id":canonical_uuid4(value.get("attempt_id"),"attempt_id")}
    if set(output)!=leaf_ids: raise LedgerError("assignments must join each approved plan leaf exactly once")
    return output
def v2_step(leaf:dict[str,Any], assignment:dict[str,str])->dict[str,Any]:
    return {"id":leaf["id"],"state":"pending","attempt":1,"max_attempts":leaf["max_attempts"],"dependencies":leaf["dependencies"],"agent_id":assignment["agent_id"],"attempt_id":assignment["attempt_id"],"fingerprints":[],"summary":"","blocker":None,"return_path":"","return_sha256":"","accepted":False}
def init_v2(args):
    require_parent(args.actor)
    if not args.approved: raise LedgerError("--approved is required before ledger creation")
    directory=ledger_dir(args); run_id=safe_identifier(args.run_id,"run id")
    plan,plan_hash=read_plan(args.plan); assignments=parse_assignments(args.assignments_json,plan)
    run_dir=directory/"runs"/run_id
    if run_dir.exists(): raise LedgerError("run already exists; init-v2 is not an overwrite operation")
    now=utc_now(); steps={leaf["id"]:v2_step(leaf,assignments[leaf["id"]]) for leaf in plan["leaves"]}
    data={"schema_version":2,"plan_id":args.plan_id,"run_id":run_id,"approved":True,"plan_hash":plan_hash,"created_at":now,"updated_at":now,"event_sequence":1,"steps":steps}
    atomic_json(checkpoint_path(directory,run_id),data); atomic_json(run_dir/"plan.json",plan,maximum=64*1024)
    append_event(run_dir/"events.jsonl",{"sequence":1,"at":now,"actor":"parent","action":"init-v2","plan_id":args.plan_id,"run_id":run_id,"plan_hash":plan_hash,"step_count":len(steps)})
    return {"ok":True,"action":"init-v2","plan_id":args.plan_id,"run_id":run_id,"plan_hash":plan_hash,"step_count":len(steps)}
def load_v2(directory:Path,run_id:str)->dict[str,Any]:
    path=checkpoint_path(directory,run_id)
    if not path.is_file(): raise LedgerError("v2 run checkpoint does not exist")
    try:data=json.loads(path.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as exc:raise LedgerError(f"cannot read checkpoint: {exc}") from exc
    errors=validate_v2(data,directory,run_id)
    if errors: raise LedgerError("invalid v2 checkpoint: "+"; ".join(errors))
    return data
def validate_v2(data:Any,directory:Path,run_id:str)->list[str]:
    errors=[]
    if not isinstance(data,dict) or data.get("schema_version")!=2: return ["unsupported v2 schema_version"]
    if data.get("run_id")!=run_id: errors.append("run id does not match checkpoint")
    if not isinstance(data.get("plan_hash"),str) or not re.fullmatch(r"[0-9a-f]{64}",data["plan_hash"]): errors.append("invalid plan_hash")
    plan_path=directory/"runs"/run_id/"plan.json"
    try: plan=json.loads(plan_path.read_text(encoding="utf-8")); actual=sha256(plan)
    except (OSError,json.JSONDecodeError): errors.append("missing or invalid v2 plan snapshot"); plan={}; actual=""
    if actual and actual!=data.get("plan_hash"): errors.append("plan snapshot hash mismatch")
    if plan:
        try: validated,_=read_plan(str(plan_path))
        except LedgerError as exc: errors.append(str(exc)); validated={}
        if validated:
            leaves={x["id"]:x for x in validated["leaves"]}; steps=data.get("steps")
            if not isinstance(steps,dict) or set(steps)!=set(leaves): errors.append("checkpoint steps do not match approved plan")
            else:
                for sid,step in steps.items():
                    if step.get("dependencies")!=leaves[sid]["dependencies"] or step.get("max_attempts")!=leaves[sid]["max_attempts"]: errors.append(f"step contract mismatch: {sid}")
                    if step.get("state") not in STATES or not isinstance(step.get("attempt"),int) or not 1<=step["attempt"]<=step.get("max_attempts",0): errors.append(f"invalid lifecycle attempt: {sid}")
                    try: canonical_uuid4(step.get("agent_id"),"agent_id"); canonical_uuid4(step.get("attempt_id"),"attempt_id")
                    except LedgerError: errors.append(f"invalid assignment identity: {sid}")
    if len(canonical(data)+b"\n")>CHECKPOINT_MAX_BYTES: errors.append("checkpoint exceeds 16 KiB")
    return errors
def event_v2(directory:Path,data:dict[str,Any],action:str,**extra:Any)->None:
    data["event_sequence"]+=1; data["updated_at"]=utc_now(); event={"sequence":data["event_sequence"],"at":data["updated_at"],"actor":"parent","action":action,"plan_id":data["plan_id"],"run_id":data["run_id"],**extra}; atomic_json(checkpoint_path(directory,data["run_id"]),data); append_event(directory/"runs"/data["run_id"] / "events.jsonl",event)
def retry_v2(args,data,step):
    if isinstance(step.get("blocker"), dict) and step["blocker"].get("code") == "blocked:oversized_return":
        raise LedgerError("oversized returns are terminal and may not be retried")
    if step["attempt"]>=step["max_attempts"]: raise LedgerError("retry limit exhausted; no exhaustion override exists")
    if not args.retry or not args.evidence_path or not args.summary or not args.agent_id or not args.attempt_id: raise LedgerError("retry requires --retry, --evidence-path, --summary, --agent-id, and --attempt-id")
    step["attempt"]+=1; step["agent_id"]=canonical_uuid4(args.agent_id,"agent_id"); step["attempt_id"]=canonical_uuid4(args.attempt_id,"attempt_id"); step["state"]="ready"; step["summary"]=args.summary[:240]; step["blocker"]=None
def transition_v2(args):
    require_parent(args.actor); directory=ledger_dir(args); data=load_v2(directory,args.run_id); sid=safe_identifier(args.step_id,"step id")
    if sid not in data["steps"]: raise LedgerError("unknown step id")
    step=data["steps"][sid]; old,new=step["state"],args.to
    if new not in TRANSITIONS[old]: raise LedgerError(f"transition {old} -> {new} is not allowed")
    if new=="ready":
        if old in {"blocked","failed"}: retry_v2(args,data,step)
        else:
            if any(data["steps"][dep]["state"]!="integrated" for dep in step["dependencies"]): raise LedgerError("dependencies must be integrated before a step becomes ready")
            if not args.agent_id or not args.attempt_id: raise LedgerError("ready requires --agent-id and --attempt-id")
            step["agent_id"]=canonical_uuid4(args.agent_id,"agent_id"); step["attempt_id"]=canonical_uuid4(args.attempt_id,"attempt_id"); step["state"]="ready"
    else:
        if new=="integrated" and not args.summary: raise LedgerError("integration requires --summary")
        if new=="blocked":
            if not BLOCKER_CODE.fullmatch(args.blocker_code): raise LedgerError("blocked transition requires --blocker-code")
            step["blocker"]={"code":args.blocker_code,"summary":args.summary[:240],"evidence_path":relative_path(args.evidence_path,"--evidence-path") if args.evidence_path else "","sha256":args.evidence_sha256 or ""}
        step["state"]=new
        if args.summary: step["summary"]=args.summary[:240]
    event_v2(directory,data,"transition-v2",step_id=sid,from_state=old,to_state=new,attempt=step["attempt"])
    return {"ok":True,"action":"transition-v2","run_id":args.run_id,"step_id":sid,"from":old,"to":new,"attempt":step["attempt"]}
def validate_return(value:Any,data:dict[str,Any],step:dict[str,Any],write_set:list[Any])->dict[str,Any]:
    if not isinstance(value,dict): raise LedgerError("step return must be an object")
    if len(canonical(value))>RETURN_MAX_BYTES: raise LedgerError("bounded-step-return-v1 exceeds 8 KiB")
    required={"return_contract","plan_id","run_id","step_id","attempt_id","agent_id","status","changed_paths","acceptance","blockers","notes","commit_hash","unstarted_remainder"}
    if set(value)!=required: raise LedgerError("bounded-step-return-v1 fields do not match contract")
    if value["return_contract"]!="bounded-step-return-v1" or value["plan_id"]!=data["plan_id"] or value["run_id"]!=data["run_id"] or value["step_id"]!=step["id"]: raise LedgerError("step return assignment does not match ledger")
    if value["attempt_id"]!=step["attempt_id"] or value["agent_id"]!=step["agent_id"]: raise LedgerError("step return agent or attempt identity does not match current assignment")
    if value["status"] not in {"completed","blocked","failed"}: raise LedgerError("step return status must be completed, blocked, or failed")
    paths=value["changed_paths"]
    if not isinstance(paths,list) or len(paths)>64 or len(set(paths))!=len(paths): raise LedgerError("changed_paths must be a unique bounded list")
    allowed = [item for item in write_set if isinstance(item, str)]
    for path in paths:
        relative_path(path,"changed path")
        if not any(path == item or path.startswith(item.rstrip("/") + "/") for item in allowed):
            raise LedgerError("changed path is outside the assigned write_set")
    acceptance=value["acceptance"]
    if not isinstance(acceptance,dict) or set(acceptance)!={"command","exit_code"} or not isinstance(acceptance["command"],str) or not isinstance(acceptance["exit_code"],int) or isinstance(acceptance["exit_code"],bool): raise LedgerError("acceptance must contain command and integer exit_code")
    blocker=value["blockers"]
    if not isinstance(blocker,dict) or set(blocker)!={"code","summary","evidence_path","sha256"} or not isinstance(blocker["summary"],str) or len(blocker["summary"])>240 or not isinstance(blocker["evidence_path"],str) or not isinstance(blocker["sha256"],str): raise LedgerError("blockers must contain code, summary, evidence_path, sha256")
    if blocker["code"] and not BLOCKER_CODE.fullmatch(blocker["code"]): raise LedgerError("invalid blocker code")
    if blocker["evidence_path"]: relative_path(blocker["evidence_path"],"blocker evidence path")
    if blocker["sha256"] and not re.fullmatch(r"[0-9a-f]{64}",blocker["sha256"]): raise LedgerError("blocker sha256 must be lowercase SHA-256")
    notes=value["notes"]
    if not isinstance(notes,list) or len(notes)>16 or any(not isinstance(n,dict) or set(n)!={"type","message"} or not isinstance(n["type"],str) or not n["type"] or not isinstance(n["message"],str) or len(n["message"])>480 for n in notes): raise LedgerError("notes must be typed bounded note objects")
    if not isinstance(value["unstarted_remainder"],str) or len(value["unstarted_remainder"])>480 or not isinstance(value["commit_hash"],str): raise LedgerError("invalid commit_hash or unstarted_remainder")
    if value["status"]=="completed":
        if acceptance["exit_code"]!=0 or blocker["code"] or not COMMIT_HASH.fullmatch(value["commit_hash"]): raise LedgerError("completed return requires exit 0, no blocker, and a 40/64-hex commit_hash")
    elif value["commit_hash"] and not COMMIT_HASH.fullmatch(value["commit_hash"]): raise LedgerError("commit_hash must be 40/64 lowercase hex")
    return value
def ingest_return(args):
    require_parent(args.actor); directory=ledger_dir(args); data=load_v2(directory,args.run_id)
    try: raw=Path(args.return_file).read_bytes()
    except OSError as exc: raise LedgerError(f"cannot read step return: {exc}") from exc
    if len(raw) > RETURN_MAX_BYTES:
        # An oversized handoff is intentionally terminal: retaining it would
        # violate the bounded-state contract, and retrying it hides the fault.
        try: preview=json.loads(raw.decode("utf-8")); sid=preview.get("step_id", "") if isinstance(preview, dict) else ""
        except (UnicodeDecodeError, json.JSONDecodeError): sid=""
        if sid in data["steps"] and data["steps"][sid]["state"] == "in_progress":
            step=data["steps"][sid]; old=step["state"]; step["state"]="blocked"; step["blocker"]={"code":"blocked:oversized_return","summary":"bounded-step-return-v1 exceeds 8 KiB","evidence_path":"","sha256":""}; step["summary"]="bounded-step-return-v1 exceeds 8 KiB"
            event_v2(directory,data,"reject-oversized-return",step_id=sid,from_state=old,to_state="blocked",attempt=step["attempt"])
        raise LedgerError("bounded-step-return-v1 exceeds 8 KiB")
    try: value=json.loads(raw.decode("utf-8"))
    except (OSError,json.JSONDecodeError) as exc: raise LedgerError(f"cannot read step return: {exc}") from exc
    sid=value.get("step_id") if isinstance(value,dict) else ""
    if sid not in data["steps"]: raise LedgerError("step return has unknown step id")
    step=data["steps"][sid]
    if step["state"]!="in_progress": raise LedgerError("only the current in_progress attempt can ingest a return")
    plan=json.loads((directory/"runs"/args.run_id/"plan.json").read_text(encoding="utf-8"))
    leaf=next(item for item in plan["leaves"] if item["id"] == sid)
    value=validate_return(value,data,step,leaf["write_set"]); fingerprint=sha256({k:value[k] for k in ("status","changed_paths","acceptance","blockers","notes","commit_hash","unstarted_remainder")})
    copy_path=directory/"runs"/args.run_id/"returns"/sid/f"{step['attempt_id']}.json"; atomic_json(copy_path,value,maximum=RETURN_MAX_BYTES)
    step["return_path"]=str(copy_path.relative_to(directory/"runs"/args.run_id)); step["return_sha256"]=sha256(value); step["accepted"]=True; step["summary"]=(value["blockers"]["summary"] or value["unstarted_remainder"] or value["status"])[:240]; step["blocker"]=value["blockers"] if value["blockers"]["code"] else None
    step["fingerprints"]=(step["fingerprints"]+[fingerprint])[-5:]
    old=step["state"]
    if value["status"]=="completed": step["state"]="completed"
    else:
        repeated=step["fingerprints"].count(fingerprint)>1
        if repeated: step["state"]="blocked"; step["blocker"]={"code":"blocked:no_progress","summary":"repeated non-completed return fingerprint","evidence_path":step["return_path"],"sha256":step["return_sha256"]}
        elif step["attempt"]>=step["max_attempts"]: step["state"]="blocked"; step["blocker"]={"code":"blocked:retry_exhausted","summary":"max attempts reached with differing evidence","evidence_path":step["return_path"],"sha256":step["return_sha256"]}
        else: step["state"]=value["status"]
    event_v2(directory,data,"ingest-return",step_id=sid,from_state=old,to_state=step["state"],attempt=step["attempt"],return_sha256=step["return_sha256"])
    return {"ok":True,"action":"ingest-return","run_id":args.run_id,"step_id":sid,"state":step["state"],"return_sha256":step["return_sha256"]}
def compact(data:dict[str,Any],step_id:str="")->dict[str,Any]:
    steps=data["steps"]
    if step_id:
        sid=safe_identifier(step_id,"step id")
        if sid not in steps: raise LedgerError("unknown step id")
        return {"ok":True,"schema_version":2,"plan_id":data["plan_id"],"run_id":data["run_id"],"plan_hash":data["plan_hash"],"step":steps[sid],"rehydration_incomplete":False}
    return {"ok":True,"schema_version":2,"plan_id":data["plan_id"],"run_id":data["run_id"],"plan_hash":data["plan_hash"],"event_sequence":data["event_sequence"],"steps":[{"id":s["id"],"state":s["state"],"attempt":s["attempt"],"max_attempts":s["max_attempts"],"summary":s["summary"],"blocker":s["blocker"],"accepted":s["accepted"]} for s in steps.values()],"rehydration_incomplete":False}
def bounded_show(result:dict[str,Any])->dict[str,Any]:
    encoded=json.dumps(result,sort_keys=True,separators=(",",":")); tokens=len(PROXY_TOKEN_RE.findall(encoded))
    if tokens<=SHOW_MAX_PROXY_TOKENS: result["summary_proxy_tokens"]=tokens; return result
    # Stable truncation: retain ordered step headers, then report omitted count.
    if "steps" in result:
        original=result["steps"]; kept=[]
        for item in original:
            candidate={**result,"steps":kept+[item],"omitted_steps":len(original)-len(kept)-1,"rehydration_incomplete":True}
            if len(PROXY_TOKEN_RE.findall(json.dumps(candidate,sort_keys=True,separators=(",",":"))))>SHOW_MAX_PROXY_TOKENS: break
            kept.append(item)
        result={**result,"steps":kept,"omitted_steps":len(original)-len(kept),"rehydration_incomplete":True}
    result["summary_proxy_tokens"]=len(PROXY_TOKEN_RE.findall(json.dumps(result,sort_keys=True,separators=(",",":"))))
    return result
def show(args):
    directory=ledger_dir(args)
    if args.run_id: return bounded_show(compact(load_v2(directory,args.run_id),args.step_id))
    data=load_v1(directory); result={"ok":True,"plan_id":data["plan_id"],"updated_at":data["updated_at"],"event_sequence":data["event_sequence"],"steps":[{"id":s["id"],"state":s["state"],"attempt":s["attempt"],"dependencies":s["dependencies"],"harness":s["harness"],"tier":s["tier"],"model_or_alias":s["model_or_alias"],"effort":s["effort"],"worktree":s["worktree"],"blocker_code":s["blocker_code"],"summary":s["summary"],"evidence_paths":s["evidence_paths"]} for s in data["steps"].values()],"legacy_schema":1,"rehydration_incomplete":True,"retry_policy":"legacy_unbounded"}; return bounded_show(result)
def validate(args):
    directory=ledger_dir(args)
    if args.run_id:
        data=load_v2(directory,args.run_id); errors=validate_v2(data,directory,args.run_id); events=directory/"runs"/args.run_id/"events.jsonl"
    else:
        data=load_v1(directory); errors=validate_checkpoint(data); events=directory/"events.jsonl"
    if not events.is_file(): errors.append("events.jsonl does not exist")
    else:
        previous=0
        for n,line in enumerate(events.read_text(encoding="utf-8").splitlines(),1):
            try:event=json.loads(line)
            except json.JSONDecodeError: errors.append(f"invalid event JSON at line {n}"); continue
            if not isinstance(event,dict) or event.get("sequence")!=previous+1: errors.append(f"invalid event sequence at line {n}")
            elif event.get("actor")!="parent" or event.get("plan_id")!=data["plan_id"]: errors.append(f"invalid event ownership at line {n}")
            previous+=1
        if previous!=data["event_sequence"]: errors.append("event sequence does not match checkpoint")
    result={"ok":not errors,"plan_id":data["plan_id"],"run_id":args.run_id or "","errors":errors,"checkpoint_bytes":checkpoint_path(directory,args.run_id).stat().st_size}
    if not args.run_id: result.update({"legacy_schema":1,"rehydration_incomplete":True,"retry_policy":"legacy_unbounded"})
    return result
def transition(args): return transition_v2(args) if args.run_id else transition_v1(args)
def parser():
    root=argparse.ArgumentParser(description=__doc__); root.add_argument("--repo-root"); root.add_argument("--ledger-root"); root.add_argument("--plan-id",required=True); commands=root.add_subparsers(dest="command",required=True)
    initial=commands.add_parser("init"); initial.add_argument("--actor",required=True); initial.add_argument("--approved",action="store_true"); initial.add_argument("--steps-json",required=True)
    v2=commands.add_parser("init-v2"); v2.add_argument("--actor",required=True); v2.add_argument("--approved",action="store_true"); v2.add_argument("--run-id",required=True); v2.add_argument("--plan",required=True); v2.add_argument("--assignments-json",required=True)
    change=commands.add_parser("transition"); change.add_argument("--actor",required=True); change.add_argument("--run-id"); change.add_argument("--step-id",required=True); change.add_argument("--to",required=True,choices=sorted(STATES)); change.add_argument("--retry",action="store_true"); change.add_argument("--summary",default=""); change.add_argument("--evidence-path",default=""); change.add_argument("--evidence-sha256",default=""); change.add_argument("--blocker-code",default=""); change.add_argument("--agent-id",default=""); change.add_argument("--attempt-id",default="")
    ingest=commands.add_parser("ingest-return"); ingest.add_argument("--actor",required=True); ingest.add_argument("--run-id",required=True); ingest.add_argument("--return-file",required=True)
    showing=commands.add_parser("show"); showing.add_argument("--run-id"); showing.add_argument("--step-id",default="")
    checking=commands.add_parser("validate"); checking.add_argument("--run-id")
    return root
def main(argv=None):
    args=parser().parse_args(argv)
    try:
        fn={"init":init,"init-v2":init_v2,"transition":transition,"ingest-return":ingest_return,"show":show,"validate":validate}[args.command]; result=fn(args); return emit(result,0 if result.get("ok",True) else 2)
    except LedgerError as exc: return emit({"ok":False,"error":str(exc)},3)
    except OSError as exc: return emit({"ok":False,"error":f"I/O failure: {exc}"},4)
if __name__=="__main__": raise SystemExit(main())
