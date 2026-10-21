"""Run the frozen quality proxies through MCP, locally or after an authorized rollout."""

import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from evaluation.quality import evaluate  # noqa: E402
from search import INPUT_SCHEMA, OUTPUT_SCHEMA  # noqa: E402


async def run(url, output):
    path = Path(__file__).with_name("quality_cases.json")
    cases = json.loads(path.read_text(encoding="utf-8"))
    raw = (ROOT / "data/products.json").read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    assert digest == "05b6aa5e8e8c1c8c997d584f8288e432862454f8820531e13473443e83c8f073"
    catalog = SimpleNamespace(by_id={p["id"]: p for p in json.loads(raw)})
    rows = []
    async with httpx.AsyncClient(timeout=30) as client:
        async with streamable_http_client(url, http_client=client) as (read, write, _):
            async with ClientSession(read, write) as session:
                init = await session.initialize()
                assert init.protocolVersion == "2025-11-25"
                tools = (await session.list_tools()).tools
                assert len(tools) == 1 and tools[0].name == "search_products"
                assert (
                    tools[0].inputSchema == INPUT_SCHEMA
                    and tools[0].outputSchema == OUTPUT_SCHEMA
                )
                for case in cases:
                    row = {
                        "name": case["name"],
                        "area": case["area"],
                        "split": case["split"],
                    }
                    start = time.perf_counter()
                    result = await asyncio.wait_for(
                        session.call_tool("search_products", case["args"]), 10
                    )
                    row["milliseconds"] = (time.perf_counter() - start) * 1000
                    row["response"] = result.structuredContent
                    try:
                        assert not result.isError
                        assert (
                            json.loads(result.content[0].text)
                            == result.structuredContent
                        )
                        evaluate(case, result.structuredContent, catalog)
                        row["pass"] = True
                    except AssertionError as exc:
                        row.update({"pass": False, "error": str(exc)})
                    rows.append(row)
    report = {
        "note": "Native MCP attribute/coverage proxies, not Bedrock grades or official score.",
        "url": url,
        "catalog_sha256": digest,
        "cases_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "passed": sum(r["pass"] for r in rows),
        "total": len(rows),
        "cases": rows,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "cases"}, indent=2))
    print("Failed cases:", [r["name"] for r in rows if not r["pass"]])
    return report["passed"] == report["total"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    passed = asyncio.run(
        asyncio.wait_for(run(options.url, options.output), timeout=180)
    )
    raise SystemExit(0 if passed else 1)
