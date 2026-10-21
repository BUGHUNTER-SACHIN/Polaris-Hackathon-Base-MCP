"""Frozen student-authored attribute/coverage proxies, not official judge grades."""

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from search import Catalog, OUTPUT_SCHEMA  # noqa: E402
from jsonschema import Draft202012Validator  # noqa: E402


def satisfies(product, rule):
    for key, field in (
        ("types", "product_type"),
        ("colors", "color"),
        ("patterns", "pattern"),
        ("categories", "category"),
    ):
        if key in rule and product[field] not in rule[key]:
            return False
    if product["product_type"] in rule.get("excluded_types", []):
        return False
    if product["color"] in rule.get("excluded_colors", []):
        return False
    if product["price"]["amount"] > rule.get("max_price", float("inf")):
        return False
    if "min_rating" in rule:
        rating = product["rating"]["average"]
        if rating is None or rating < rule["min_rating"]:
            return False
    if product["rating"]["count"] < rule.get("min_review_count", 0):
        return False
    text = " ".join(
        str(product.get(k) or "") for k in ("name", "description")
    ).casefold()
    if not all(term in text for term in rule.get("text", [])):
        return False
    if rule.get("audience") == "men":
        return product["audience"] == "Menswear" or product["section"].startswith(
            ("Men ", "Mens ", "Denim Men")
        )
    return True


def evaluate(case, payload, catalog):
    Draft202012Validator(OUTPUT_SCHEMA).validate(payload)
    ids = [p["id"] for p in payload["results"]]
    recs = payload["recommendations"]
    rids = [p["id"] for p in recs]
    assert len(ids) == len(set(ids)) and len(rids) == len(set(rids))
    assert all(isinstance(i, str) and i in catalog.by_id for i in ids + rids)
    assert not set(ids) & set(rids)
    assert all(r["for_product_id"] in ids for r in recs)
    assert len(ids) <= case.get("max_results", case["args"].get("limit", 10))
    if case.get("empty"):
        assert not ids and not rids, "expected empty arrays"
        return
    ps = [catalog.by_id[i] for i in ids]
    if "reference_count" in case:
        available = sum(
            any(satisfies(p, rule) for rule in case["choices"])
            for p in catalog.by_id.values()
        )
        assert available == case["reference_count"], "catalog reference count changed"
        assert case.get("min_results", 10) <= available, "impossible reference target"
    assert len(ps) >= case.get("min_results", 10), "missing primary slots"
    choices = case["choices"]
    assert all(any(satisfies(p, r) for r in choices) for p in ps), "primary constraints"
    assert all(any(satisfies(p, r) for p in ps) for r in choices), "missing choice"
    if "complements" in case:
        assert len(recs) == 5, "missing recommendation slots"
        assert all(
            any(satisfies(catalog.by_id[r["id"]], rule) for rule in case["complements"])
            for r in recs
        ), "accessory constraints"
    else:
        assert not recs
    if case.get("price_ascending"):
        assert ps == sorted(ps, key=lambda p: (p["price"]["amount"], p["id"]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", choices=("dev", "heldout", "all"), default="dev")
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    path = Path(__file__).with_name("quality_cases.json")
    cases = json.loads(path.read_text(encoding="utf-8"))
    start = time.perf_counter()
    catalog = Catalog.load(ROOT / "data/products.json")
    startup = time.perf_counter() - start
    rows = []
    for case in cases:
        if options.split != "all" and options.split != case["split"]:
            continue
        row = {"name": case["name"], "area": case["area"], "split": case["split"]}
        start = time.perf_counter()
        payload = catalog.search(case["args"])
        row.update(response=payload, milliseconds=(time.perf_counter() - start) * 1000)
        try:
            evaluate(case, payload, catalog)
            row["pass"] = True
        except AssertionError as exc:
            row.update({"pass": False, "error": str(exc)})
        rows.append(row)
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["area"]].append(row)
    report = {
        "note": "Attribute, full-slot and coverage proxies only; no Bedrock grades or official score.",
        "cases_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "split": options.split,
        "startup_seconds": startup,
        "passed": sum(r["pass"] for r in rows),
        "total": len(rows),
        "areas": {
            k: {"passed": sum(r["pass"] for r in v), "total": len(v)}
            for k, v in grouped.items()
        },
        "cases": rows,
    }
    options.output.parent.mkdir(parents=True, exist_ok=True)
    options.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "cases"}, indent=2))
    print("Failed cases:", [r["name"] for r in rows if not r["pass"]])
    return report["passed"] == report["total"]


if __name__ == "__main__":
    raise SystemExit(0 if main() else 1)
