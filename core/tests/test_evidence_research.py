import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from evidence_research import attach_report_page_readback, assemble_dossier, parse_search_response
from harness_context import route_lanes, select_tools
from jarvis_mark2 import MARK2_TOOLS, Mark2Runtime


def response(url="https://example.org/report?utm_source=demo", answer="Cited finding"):
    return {
        "output": [
            {"type": "web_search_call", "action": {"sources": [
                {"url": url, "title": "Report"},
                {"url": "https://other.example/uncited", "title": "Uncited search result"},
            ]}},
            {"type": "message", "content": [{
                "type": "output_text", "text": answer,
                "annotations": [{"type": "url_citation", "url": url, "title": "Report", "start_index": 0, "end_index": len(answer)}],
            }]},
        ],
    }


class EvidenceParserTests(unittest.TestCase):
    def test_dossier_records_provider_usage_without_cost_guess(self):
        raw = response()
        raw["usage"] = {"input_tokens": 120, "output_tokens": 30, "total_tokens": 150}
        finding = parse_search_response("Question", raw)
        data = assemble_dossier("Topic", [finding])
        self.assertEqual(data["research_usage"]["web_search_events_observed"], 1)
        self.assertEqual(data["research_usage"]["total_tokens_reported"], 150)
        self.assertEqual(data["research_usage"]["responses_with_usage"], 1)
        self.assertIn("not a billing invoice", data["research_usage"]["note"])

    def test_missing_usage_is_not_misreported_as_free(self):
        data = assemble_dossier("Topic", [parse_search_response("Question", response())])
        self.assertEqual(data["research_usage"]["responses_with_usage"], 0)
        self.assertEqual(data["research_usage"]["responses_total"], 1)

    def test_report_readback_is_bounded_and_does_not_claim_truth(self):
        data = assemble_dossier("Topic", [parse_search_response("Question", response(
            answer="The measured result was 42 units.",
        ))])
        for number in range(2, 6):
            data["sources"].append({"id": f"S{number}", "url": f"https://example.org/{number}"})
        calls = []

        def fake_probe(url, quote):
            calls.append((url, quote))
            return {"status": "page_read", "quote_match": "exact_text_found",
                    "excerpt": "The measured result was 42 units.", "text_chars_scanned": 100}

        result = attach_report_page_readback(data, fake_probe)
        self.assertEqual(len(calls), 3)
        self.assertEqual(result["page_readback_summary"]["exact_answer_text_found"], 3)
        self.assertEqual(result["sources"][3]["page_inspection"]["status"], "not_inspected_budget")
        self.assertEqual(result["sources"][4]["page_inspection"]["status"], "not_inspected_budget")
        self.assertIn("42 units", next(quote for url, quote in calls if "report" in url))
        self.assertIn("does not verify", result["page_readback_summary"]["caveat"])

    def test_report_readback_failure_is_labeled_not_fabricated(self):
        data = assemble_dossier("Topic", [parse_search_response("Question", response())])
        result = attach_report_page_readback(data, lambda _url, _quote: (_ for _ in ()).throw(OSError()))
        self.assertEqual(result["sources"][0]["page_inspection"], {
            "status": "unavailable", "quote_requested": True,
        })
        self.assertEqual(result["page_readback_summary"]["pages_read"], 0)

    def test_cited_and_consulted_urls_remain_distinct(self):
        finding = parse_search_response("Question", response())
        self.assertEqual(finding["status"], "cited")
        self.assertEqual(finding["cited_sources"][0]["answer_spans"], ["Cited finding"])
        self.assertEqual(len(finding["consulted_only_sources"]), 1)
        self.assertIn("uncited", finding["consulted_only_sources"][0]["url"])

    def test_no_annotation_is_unverified_even_if_search_returned_urls(self):
        raw = response()
        raw["output"][1]["content"][0]["annotations"] = []
        finding = parse_search_response("Question", raw)
        self.assertEqual(finding["status"], "unverified")
        self.assertEqual(finding["cited_sources"], [])

    def test_no_web_search_is_unverified(self):
        raw = response()
        raw["output"] = raw["output"][1:]
        finding = parse_search_response("Question", raw)
        self.assertEqual(finding["status"], "unverified")
        self.assertFalse(finding["web_search_observed"])

    def test_tracking_variants_deduplicate_across_questions(self):
        findings = [
            parse_search_response("First", response()),
            parse_search_response("Second", response(url="https://example.org/report?utm_medium=chat")),
        ]
        dossier = assemble_dossier("Topic", findings)
        self.assertEqual(len(dossier["sources"]), 1)
        self.assertEqual(dossier["sources"][0]["supports_questions"], ["First", "Second"])
        self.assertEqual(dossier["findings"][1]["source_ids"], ["S1"])

    def test_invalid_or_credential_urls_never_become_sources(self):
        finding = parse_search_response("Question", response(url="https://user:pass@example.org/secret"))
        self.assertEqual(finding["status"], "unverified")
        self.assertEqual(finding["cited_sources"], [])


class DossierIntegrationTests(unittest.TestCase):
    def test_bounded_dossier_handles_partial_failure_and_redacts_audit(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(
            os.environ, {"OPENAI_API_KEY": "never-print-key"}, clear=False,
        ):
            runtime = Mark2Runtime(Path(folder))

            def fake_search(question):
                return "error: temporary outage" if question == "Risks?" else response()

            with patch.object(runtime, "_research_data", side_effect=fake_search) as mocked, patch.object(
                runtime, "_probe_research_source", return_value={"status": "reachable", "http_status": 200},
            ):
                result = runtime.execute("research_dossier", {
                    "topic": "private product", "questions": ["Benefits?", "Risks?"],
                })
            data = json.loads(result)
            self.assertEqual(mocked.call_count, 2)
            self.assertEqual([item["status"] for item in data["findings"]], ["cited", "error"])
            self.assertEqual(data["status"], "partial_or_unverified")
            self.assertEqual(data["sources"][0]["link_check"]["status"], "reachable")
            runtime.audit("research_dossier", {
                "topic": "private product", "questions": ["Benefits?", "Risks?"],
            }, result)
            audit = runtime.audit_path.read_text(encoding="utf-8")
            self.assertNotIn("private product", audit)
            self.assertNotIn("never-print-key", audit)
            self.assertNotIn("Benefits?", audit)
            self.assertIn("[REDACTED: research questions]", audit)

    def test_limits_and_routing(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(
            os.environ, {"OPENAI_API_KEY": "test"}, clear=False,
        ):
            runtime = Mark2Runtime(Path(folder))
            with self.assertRaisesRegex(ValueError, "1 to 3"):
                runtime.research_dossier("Topic", ["a?", "b?", "c?", "d?"])
            with self.assertRaisesRegex(ValueError, "distinct"):
                runtime.research_dossier("Topic", ["Same?", "same?"])
            names = {item["function"]["name"] for item in select_tools(MARK2_TOOLS, route_lanes("deep research dossier"))}
            self.assertIn("research_dossier", names)

    def test_provider_exception_is_isolated_per_question(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(
            os.environ, {"OPENAI_API_KEY": "test"}, clear=False,
        ):
            runtime = Mark2Runtime(Path(folder))

            def fake_search(question):
                if question == "Broken?":
                    raise RuntimeError("provider failed")
                return response()

            with patch.object(runtime, "_research_data", side_effect=fake_search), patch.object(
                runtime, "_probe_research_source", return_value={"status": "timeout"},
            ):
                result = json.loads(runtime.research_dossier("Topic", ["Working?", "Broken?"]))
            self.assertEqual(result["status"], "partial_or_unverified")
            self.assertEqual(result["findings"][1]["status"], "error")
            self.assertIn("provider failed", result["findings"][1]["error"])

    def test_source_page_tool_is_scoped_and_audit_redacted(self):
        names = {item["function"]["name"] for item in select_tools(MARK2_TOOLS, route_lanes("inspect a research source"))}
        self.assertIn("research_source_page", names)
        with tempfile.TemporaryDirectory() as folder:
            runtime = Mark2Runtime(Path(folder))
            with patch.object(runtime, "_run_source_probe", return_value={
                "status": "page_read", "quote_match": "exact_text_found", "excerpt": "Private fixture text",
            }) as probe:
                result = runtime.execute("research_source_page", {
                    "url": "https://example.org/private", "quote": "Private fixture text",
                })
            self.assertEqual(json.loads(result)["status"], "page_read")
            probe.assert_called_once_with({
                "mode": "page", "url": "https://example.org/private", "quote": "Private fixture text",
            }, 6)
            runtime.audit("research_source_page", {
                "url": "https://example.org/private", "quote": "Private fixture text",
            }, result)
            audit = runtime.audit_path.read_text(encoding="utf-8")
            self.assertNotIn("https://example.org/private", audit)
            self.assertNotIn("Private fixture text", audit)


if __name__ == "__main__":
    unittest.main()
