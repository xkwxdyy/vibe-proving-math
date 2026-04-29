import json

from fastapi.testclient import TestClient

from api.server import app


def _collect_sse_events(client: TestClient, payload: dict) -> list[dict]:
    events = []
    with client.stream("POST", "/formalize", json=payload) as resp:
        assert resp.status_code == 200, resp.text
        for line in resp.iter_lines():
            if not line:
                continue
            if isinstance(line, bytes):
                line = line.decode("utf-8", errors="replace")
            if not line.startswith("data:"):
                continue
            raw = line[5:].strip()
            if raw == "[DONE]":
                events.append({"kind": "done"})
                break
            obj = json.loads(raw)
            if "status" in obj:
                events.append({"kind": "status", "step": obj.get("step"), "status": obj["status"]})
            elif "final" in obj:
                events.append({"kind": "final", "data": obj["final"]})
            elif "error" in obj:
                events.append({"kind": "error", "data": obj["error"]})
            elif "chunk" in obj:
                events.append({"kind": "chunk", "data": obj["chunk"]})
    return events


def test_formalize_rejects_blank_statement():
    client = TestClient(app)
    resp = client.post("/formalize", json={"statement": "   "})
    assert resp.status_code == 422


def test_formalize_auto_repairs_until_verified(monkeypatch):
    import modes.formalization.pipeline as pipeline

    async def fake_extract_keywords(statement: str) -> list[str]:
        return ["prime", "number"]

    async def fake_search(keywords: list[str], top_k: int = 6) -> list[dict]:
        return []

    async def fake_autoformalize(statement: str, model=None, lang: str = "zh") -> dict:
        return {
            "lean_code": "theorem demo : True := by\n  exact missingProof",
            "theorem_statement": "theorem demo : True",
            "uses_mathlib": False,
            "proof_status": "complete",
            "explanation": "初版自动形式化",
            "confidence": 0.41,
        }

    repair_calls: list[dict] = []

    async def fake_repair(statement: str, lean_code: str, compile_error: str, *, model=None, lang: str = "zh") -> dict:
        repair_calls.append({
            "statement": statement,
            "lean_code": lean_code,
            "compile_error": compile_error,
            "lang": lang,
        })
        return {
            "lean_code": "theorem demo : True := by\n  trivial",
            "theorem_statement": "theorem demo : True",
            "uses_mathlib": False,
            "proof_status": "complete",
            "explanation": "根据编译错误移除了不存在的标识符",
            "confidence": 0.78,
        }

    compile_results = iter([
        {"status": "error", "error": "lean:2:8: error: unknown identifier 'missingProof'"},
        {"status": "verified", "error": ""},
    ])

    async def fake_compile(lean_code: str) -> dict:
        return next(compile_results)

    monkeypatch.setattr(pipeline, "_extract_keywords", fake_extract_keywords)
    monkeypatch.setattr(pipeline, "_search_github_mathlib", fake_search)
    monkeypatch.setattr(pipeline, "_autoformalize", fake_autoformalize)
    monkeypatch.setattr(pipeline, "_repair_formalization", fake_repair)
    monkeypatch.setattr(pipeline, "_try_compile_lean", fake_compile)

    client = TestClient(app)
    events = _collect_sse_events(
        client,
        {"statement": "True 命题", "lang": "zh", "max_iters": 4, "mode": "pipeline"},
    )

    status_steps = [e["step"] for e in events if e["kind"] == "status"]
    assert "generate" in status_steps
    assert "compile" in status_steps
    assert "repair" in status_steps

    final = next(e["data"] for e in events if e["kind"] == "final")
    assert final["compilation"]["status"] == "verified"
    assert final["iterations"] == 2
    assert final["auto_optimized"] is True
    assert len(final["attempt_history"]) == 2
    assert repair_calls, "应至少调用一次编译错误驱动修复"
    assert "missingProof" in repair_calls[0]["compile_error"]


def test_formalize_continue_optimization_skips_search(monkeypatch):
    import modes.formalization.pipeline as pipeline

    called = {
        "extract": 0,
        "search": 0,
        "auto": 0,
        "repair": 0,
    }

    async def fail_extract(statement: str) -> list[str]:
        called["extract"] += 1
        raise AssertionError("continue 优化路径不应重新提取关键词")

    async def fail_search(keywords: list[str], top_k: int = 6) -> list[dict]:
        called["search"] += 1
        raise AssertionError("continue 优化路径不应重新搜索 mathlib")

    async def fail_auto(statement: str, model=None, lang: str = "zh") -> dict:
        called["auto"] += 1
        raise AssertionError("continue 优化路径不应重新走首次 autoformalize")

    async def fake_repair(statement: str, lean_code: str, compile_error: str, *, model=None, lang: str = "zh") -> dict:
        called["repair"] += 1
        assert "unknown constant" in compile_error
        return {
            "lean_code": "theorem demo : True := by\n  trivial",
            "theorem_statement": "theorem demo : True",
            "uses_mathlib": False,
            "proof_status": "complete",
            "explanation": "继续优化成功",
            "confidence": 0.8,
        }

    compile_results = iter([
        {"status": "error", "error": "lean:2:2: error: unknown constant Foo.bar"},
        {"status": "verified", "error": ""},
    ])

    async def fake_compile(lean_code: str) -> dict:
        return next(compile_results)

    monkeypatch.setattr(pipeline, "_extract_keywords", fail_extract)
    monkeypatch.setattr(pipeline, "_search_github_mathlib", fail_search)
    monkeypatch.setattr(pipeline, "_autoformalize", fail_auto)
    monkeypatch.setattr(pipeline, "_repair_formalization", fake_repair)
    monkeypatch.setattr(pipeline, "_try_compile_lean", fake_compile)

    client = TestClient(app)
    events = _collect_sse_events(
        client,
        {
            "statement": "True 命题",
            "lang": "zh",
            "max_iters": 3,
            "skip_search": True,
            "current_code": "theorem demo : True := by\n  exact Foo.bar",
            "compile_error": "lean:2:2: error: unknown constant Foo.bar",
        },
    )

    final = next(e["data"] for e in events if e["kind"] == "final")
    assert final["compilation"]["status"] == "verified"
    assert final["iterations"] == 2
    assert called["extract"] == 0
    assert called["search"] == 0
    assert called["auto"] == 0
    assert called["repair"] == 1


def test_formalize_returns_mathlib_match_before_generation(monkeypatch):
    import modes.formalization.pipeline as pipeline

    called = {
        "extract": 0,
        "validate": 0,
    }

    async def fake_extract(statement: str) -> list[str]:
        called["extract"] += 1
        return ["square", "inequality"]

    async def fake_retrieve(statement: str, *, keywords: list[str]):
        return [], [{"path": "Mathlib/Algebra/Order/Field/Basic.lean", "name": "demo", "html_url": "https://example.com/mathlib"}]

    async def fake_validate(statement: str, candidates: list[dict]):
        called["validate"] += 1
        return ({
            "path": "Mathlib/Algebra/Order/Field/Basic.lean",
            "name": "sqineq",
            "html_url": "https://example.com/mathlib",
            "snippet": "theorem sqineq (a b : ℝ) : a ^ 2 + b ^ 2 ≥ 2 * a * b := by\n  nlinarith [sq_nonneg (a - b)]",
            "lean_name": "sqineq",
            "match_explanation": "已匹配到 mathlib 定理",
        }, 0.93)

    monkeypatch.setattr(pipeline, "_extract_keywords", fake_extract)
    monkeypatch.setattr(pipeline, "_retrieve_context", fake_retrieve)
    monkeypatch.setattr(pipeline, "_validate_match", fake_validate)

    client = TestClient(app)
    events = _collect_sse_events(
        client,
        {
            "statement": "对任意实数 a, b，证明 a^2 + b^2 ≥ 2ab。",
            "lang": "zh",
            "max_iters": 2,
            "mode": "pipeline",
        },
    )

    status_steps = [e["step"] for e in events if e["kind"] == "status"]
    assert "search" in status_steps
    assert "validate" in status_steps
    assert "found" in status_steps
    assert "generate" not in status_steps

    final = next(e["data"] for e in events if e["kind"] == "final")
    assert final["source"] == "mathlib4"
    assert final["compilation"]["status"] == "mathlib_verified"
    assert final["selected_candidate"]["origin"] == "mathlib4"
    assert called == {"extract": 1, "validate": 1}


def test_formalize_aristotle_mocked_streams_final(monkeypatch):
    import base64
    import json

    import modes.formalization.pipeline as pipeline

    async def fake_aristotle(statement, *, lang="zh", skip_search=False, tools=None):
        yield "<!--vp-status:submit|submitted-->"
        payload = {
            "status": "generated",
            "lean_code": "theorem demo : True := trivial",
            "source": "aristotle",
            "compilation": {
                "status": "verified",
                "verifier": "aristotle",
                "passed": True,
                "aristotle_formalize_project_id": "job_formal_1",
                "aristotle_prove_project_id": "job_prove_1",
            },
            "failure_mode": "none",
            "next_action_hint": "",
        }
        enc = base64.b64encode(json.dumps(payload, ensure_ascii=False).encode()).decode()
        yield f"<!--vp-final:{enc}-->"

    monkeypatch.setattr("core.aristotle_client.is_aristotle_enabled", lambda: True)
    monkeypatch.setattr(pipeline, "run_formalization_aristotle", fake_aristotle)

    client = TestClient(app)
    events = _collect_sse_events(client, {"statement": "True", "lang": "zh", "mode": "aristotle"})
    final = next(e["data"] for e in events if e["kind"] == "final")
    assert final["source"] == "aristotle"
    assert final["compilation"]["aristotle_formalize_project_id"] == "job_formal_1"


def test_formalize_aristotle_disabled_uses_pipeline(monkeypatch):
    from modes.formalization.models import FormalizationBlueprint, FormalizationCandidate

    import modes.formalization.pipeline as pipeline

    async def fake_extract_keywords(statement: str) -> list[str]:
        return []

    async def fake_search(keywords: list[str], top_k: int = 6) -> list[dict]:
        return []

    async def fake_retrieve(statement: str, *, keywords: list[str]):
        return [], []

    async def fake_plan(statement, retrieval_hits, **kwargs):
        return FormalizationBlueprint(
            goal_summary="demo",
            target_shape="theorem demo : True",
            strategy="",
            notes=[],
            revision=0,
        )

    async def fake_gen(statement, blueprint, retrieval_hits, **kwargs):
        return FormalizationCandidate(
            lean_code="theorem demo : True := by trivial",
            theorem_statement="theorem demo : True",
            uses_mathlib=False,
            proof_status="complete",
            explanation="mock",
            confidence=0.9,
            origin="generated",
            blueprint_revision=0,
        )

    async def fake_compile(lean_code: str) -> dict:
        return {"status": "verified", "error": "", "passed": True}

    monkeypatch.setattr("core.aristotle_client.is_aristotle_enabled", lambda: False)
    monkeypatch.setattr(pipeline, "_extract_keywords", fake_extract_keywords)
    monkeypatch.setattr(pipeline, "_search_github_mathlib", fake_search)
    monkeypatch.setattr(pipeline, "_retrieve_context", fake_retrieve)
    monkeypatch.setattr(pipeline, "_plan_blueprint", fake_plan)
    monkeypatch.setattr(pipeline, "_generate_candidate", fake_gen)
    monkeypatch.setattr(pipeline, "_try_compile_lean", fake_compile)

    client = TestClient(app)
    events = _collect_sse_events(
        client,
        {"statement": "True", "lang": "zh", "mode": "aristotle"},
    )
    final = next(e["data"] for e in events if e["kind"] == "final")
    assert final["compilation"]["status"] == "verified"
    assert final.get("source") == "generated"


def test_formalize_aristotle_poll_steps_visible(monkeypatch):
    import modes.formalization.pipeline as pipeline

    async def fake_aristotle(statement, *, lang="zh", skip_search=False, tools=None):
        yield "<!--vp-status:poll|waiting-->"
        yield "<!--vp-status:compile|done-->"

    monkeypatch.setattr("core.aristotle_client.is_aristotle_enabled", lambda: True)
    monkeypatch.setattr(pipeline, "run_formalization_aristotle", fake_aristotle)

    client = TestClient(app)
    events = _collect_sse_events(client, {"statement": "x", "mode": "aristotle"})
    steps = [e["step"] for e in events if e["kind"] == "status"]
    assert "poll" in steps or "compile" in steps


def test_formalize_status_endpoint_mocked(monkeypatch):
    from datetime import datetime, timezone

    from aristotlelib.project import Project, ProjectStatus

    class FakeProject:
        project_id = "tid"
        status = ProjectStatus.COMPLETE
        created_at = datetime.now(timezone.utc)
        last_updated_at = datetime.now(timezone.utc)
        percent_complete = 100
        output_summary = None

        async def refresh(self):
            pass

    async def fake_from_id(cls, project_id: str):
        return FakeProject()

    monkeypatch.setattr("core.aristotle_client.ensure_aristotle_api_key_set", lambda: None)
    monkeypatch.setattr(Project, "from_id", classmethod(fake_from_id))

    client = TestClient(app)
    r = client.get("/formalize/status/tid")
    assert r.status_code == 200
    body = r.json()
    assert body["project_id"] == "tid"
    assert body["status"] == "COMPLETE"
