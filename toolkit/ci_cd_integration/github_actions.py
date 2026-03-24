from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class GitHubActionsRunner:

    _PASS_ICON = "v"
    _FAIL_ICON = "x"
    _WARN_ICON = "!"

    def __init__(
        self,
        system_id: str,
        config_path: str = "configs/ci_cd_config.yaml",
        eval_sets: Optional[Dict[str, str]] = None,
        compare_to: Optional[str] = None,
        output_file: Optional[str] = None,
        summary_file: Optional[str] = None,
    ):
        self.system_id  = system_id
        self.config_path = config_path
        self.eval_sets  = eval_sets
        self.compare_to = compare_to
        self.output_file = output_file
        self.summary_file = (
            summary_file
            or os.environ.get("GITHUB_STEP_SUMMARY")
        )

    # Summary rendering

    def _render_summary(
        self, result: Any, duration_s: float
    ) -> str:
        """Render Markdown step summary."""
        passed   = result.passed
        icon     = self._PASS_ICON if passed else self._FAIL_ICON
        status   = "PASSED" if passed else "FAILED"

        lines = [
            f"QALIS Quality Gate — {self.system_id}",
            f"",
            f"Status: {icon} {status}  ",
            f"Run time: {duration_s:.1f}s  ",
            f"Timestamp: {datetime.now(timezone.utc).isoformat()}",
            f"",
        ]

        # Mandatory failures
        if result.failures:
            lines += [
                "Gate Failures",
                "",
                "| Metric | Value | Threshold | Description |",
                "|--------|-------|-----------|-------------|",
            ]
            for f in result.failures:
                lines.append(
                    f"| `{f['metric_id']}` | `{f['value']:.4f}` "
                    f"| `{f['operator']} {f['threshold']}` "
                    f"| {f.get('description', '')} |"
                )
            lines.append("")

        # Regressions
        if result.regressions:
            lines += [
                "Regressions Detected",
                "",
                "| Metric | Current | Baseline | Delta |",
                "|--------|---------|----------|-------|",
            ]
            for r in result.regressions:
                lines.append(
                    f"| {r['metric_id']} "
                    f"| {r['current_value']:.4f} "
                    f"| {r['baseline_value']:.4f} "
                    f"| {r['delta']:+.4f} |"
                )
            lines.append("")

        # Advisory warnings
        if result.advisory_warnings:
            lines += ["Advisory Warnings", ""]
            for w in result.advisory_warnings:
                lines.append(f"- {w}")
            lines.append("")

        if passed and not result.advisory_warnings:
            lines += [
                "All Checks Passed",
                "",
                "Deployment is cleared by the QALIS quality gate.",
                "",
            ]

        lines += [
            "---",
            f"QALIS CI gate - system {self.system_id} "
            f"config {self.config_path}",
        ]
        return "\n".join(lines)

    def _write_summary(self, content: str) -> None:
     
        if self.summary_file:
            try:
                Path(self.summary_file).parent.mkdir(parents=True, exist_ok=True)
                with open(self.summary_file, "a", encoding="utf-8") as fh:
                    fh.write(content + "\n")
            except Exception as exc:
                logger.warning("Could not write step summary: %s", exc)
        else:
            print(content)

    def _set_github_output(self, result: Any) -> None:
       
        output_path = os.environ.get("GITHUB_OUTPUT")
        pairs = {
            "qalis_gate_passed": str(result.passed).lower(),
            "qalis_violations":  ",".join(
                f["metric_id"] for f in result.failures
            ),
            "qalis_regressions": ",".join(
                r["metric_id"] for r in result.regressions
            ),
        }
        if output_path:
            try:
                with open(output_path, "a", encoding="utf-8") as fh:
                    for k, v in pairs.items():
                        fh.write(f"{k}={v}\n")
            except Exception as exc:
                logger.warning("Could not write GITHUB_OUTPUT: %s", exc)
        else:
            # Print in GitHub Actions set-output format for older runners
            for k, v in pairs.items():
                print(f"::set-output name={k}::{v}")

    def _emit_annotations(self, result: Any) -> None:
      
        for f in result.failures:
            msg = (
                f"QALIS gate FAILED: {f['metric_id']}={f['value']:.4f} "
                f"(threshold {f['operator']} {f['threshold']}) — "
                f"{f.get('description', '')}"
            )
            print(f"::error title=QALIS Gate Failure::{msg}")

        for r in result.regressions:
            msg = (
                f"QALIS regression: {r['metric_id']} dropped {r['delta']:+.4f} "
                f"(current={r['current_value']:.4f}, "
                f"baseline={r['baseline_value']:.4f})"
            )
            print(f"::error title=QALIS Regression::{msg}")

        for w in result.advisory_warnings:
            print(f"::warning title=QALIS Advisory::{w}")

    # Main entrypoint

    def run(self) -> int:
       
        import time
        from toolkit.ci_gate.quality_gate import QALISQualityGate

        logger.info(
            "QALIS GitHub Actions Runner - system=%s config=%s compare_to=%s",
            self.system_id, self.config_path, self.compare_to,
        )

        t0 = time.perf_counter()
        gate = QALISQualityGate(
            system_id=self.system_id,
            config_path=self.config_path,
        )
        result = gate.run(
            eval_sets=self.eval_sets,
            compare_to=self.compare_to,
        )
        duration = time.perf_counter() - t0

        # Console output
        print(str(result))

        # GitHub Actions outputs
        self._emit_annotations(result)
        self._set_github_output(result)

        # Step summary Markdown
        summary_md = self._render_summary(result, duration)
        self._write_summary(summary_md)

        # JSON output file
        if self.output_file:
            data = {
                "system_id":   result.system_id,
                "passed":      result.passed,
                "timestamp":   result.timestamp,
                "failures":    result.failures,
                "regressions": result.regressions,
                "advisory_warnings": result.advisory_warnings,
                "duration_s":  round(duration, 2),
            }
            try:
                Path(self.output_file).parent.mkdir(parents=True, exist_ok=True)
                with open(self.output_file, "w", encoding="utf-8") as fh:
                    json.dump(data, fh, indent=2)
                logger.info("Gate result written: %s", self.output_file)
            except Exception as exc:
                logger.warning("Could not write output file: %s", exc)

        return 0 if result.passed else 1


# CLI entrypoint

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="qalis-gate",
        description="QALIS quality gate for GitHub Actions / CI pipelines",
    )
    p.add_argument("--system-id",    required=True, help="System identifier")
    p.add_argument("--config-path",  default="configs/ci_cd_config.yaml")
    p.add_argument("--compare-to",   default=None,
                   help="Version tag for regression detection")
    p.add_argument("--output-file",  default=None,
                   help="Write JSON result to this path")
    p.add_argument("--eval-set",     action="append", default=[],
                   metavar="METRIC=PATH",
                   help="Override eval set path, e.g. FC-1=path/to/suite.csv")
    p.add_argument("--verbose",      action="store_true")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s  %(name)s  %(message)s",
    )
    eval_sets: Dict[str, str] = {}
    for kv in args.eval_set:
        if "=" in kv:
            k, v = kv.split("=", 1)
            eval_sets[k] = v

    runner = GitHubActionsRunner(
        system_id=args.system_id,
        config_path=args.config_path,
        compare_to=args.compare_to,
        output_file=args.output_file,
        eval_sets=eval_sets or None,
    )
    return runner.run()


if __name__ == "__main__":
    sys.exit(main())
