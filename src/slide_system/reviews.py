from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from .runs import STATUS_LABELS, find_run, now_iso
from .state import mutate_run, transition_run
from .storage import atomic_write_json, read_json
from .validation import validate_document, validate_file


def record_review(
    project_root: Path,
    config: dict[str, Any],
    run_id: str,
    *,
    review_source: Path,
    owner: str,
) -> dict[str, Any]:
    selected = find_run(project_root, config, run_id)
    if selected["status"] != "ready_for_review":
        raise ValueError(f"レビューを記録できる状態ではありません: {selected['status']}")
    run_dir = Path(selected["_run_dir"])
    attempt_number = int(selected["progress"].get("current_attempt", 0))
    review = validate_file(project_root, "review", review_source.resolve())
    if review["run_id"] != run_id or int(review["attempt"]) != attempt_number:
        raise ValueError("レビューのRun IDまたはAttempt番号が一致しません")
    attempt_dir = run_dir / "attempts" / f"{attempt_number:03d}"
    qa_path = attempt_dir / "qa-report.json"
    if not qa_path.is_file() or read_json(qa_path).get("result") != "PASS":
        raise ValueError("統合QAがPASSしていないAttemptは採用・レビューできません")
    review_path = attempt_dir / "review.json"
    atomic_write_json(review_path, review)

    def apply(run: dict[str, Any]) -> dict[str, Any]:
        attempt_path = attempt_dir / "attempt.json"
        attempt = read_json(attempt_path)
        attempt["status"] = "accepted" if review["result"] == "accepted" else "needs_revision"
        attempt["updated_at"] = now_iso()
        attempt.setdefault("artifacts", {})["review"] = "review.json"
        validate_document(project_root, "attempt", attempt)
        atomic_write_json(attempt_path, attempt)
        run["quality"]["latest_review"] = f"attempts/{attempt_number:03d}/review.json"
        run["quality"]["human_result"] = review["result"]
        if review["result"] == "needs_revision":
            run["status"] = "needs_revision"
            run["progress"]["current_phase"] = "needs_revision"
            run["guidance"] = {"status_label": STATUS_LABELS["needs_revision"], "last_action": "利用者レビューで修正点が見つかりました", "next_action": "新しい修正Attemptを作成してください"}
        else:
            delivery_dir = run_dir / "delivery"
            delivery_dir.mkdir(exist_ok=True)
            html_source = attempt_dir / "deck.html"
            pdf_source = attempt_dir / "deck.pdf"
            if not html_source.is_file():
                raise FileNotFoundError("採用するHTMLがありません")
            shutil.copy2(html_source, delivery_dir / "final.html")
            if run["output"]["profile"] == "html_pdf":
                if not pdf_source.is_file():
                    raise FileNotFoundError("採用するPDFがありません")
                shutil.copy2(pdf_source, delivery_dir / "final.pdf")
            run["delivery"] = {"accepted_attempt": attempt_number, "html": "delivery/final.html", "pdf": "delivery/final.pdf" if pdf_source.is_file() else None}
            run["guidance"] = {"status_label": STATUS_LABELS["ready_for_review"], "last_action": "利用者が成果物を採用しました", "next_action": "Runを完了します"}
        return run

    updated = mutate_run(project_root, config, run_id, owner=owner, event="human_review_recorded", mutator=apply, event_details={"attempt": attempt_number, "result": review["result"]})
    if review["result"] == "accepted":
        updated = transition_run(project_root, config, run_id, new_status="complete", owner=owner, last_action="利用者承認済み成果物をdeliveryへ保存しました", next_action="必要な場合は子Runを作成してください", phase="complete", last_step="delivery_completed")
    return updated
