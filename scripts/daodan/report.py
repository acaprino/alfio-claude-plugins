"""The build report.

One report type carries everything a build can fail on, so the CLI's exit code
is a property of the report rather than a scattered set of early returns.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence, TextIO

from .adapter import SupportReport
from .validate import ValidationIssue


@dataclass(frozen=True)
class BuildReport:
    issues: tuple[ValidationIssue, ...] = ()
    drift: tuple[Path, ...] = ()
    support: tuple[SupportReport, ...] = field(default=())

    @property
    def has_failures(self) -> bool:
        return bool(self.issues or self.drift)

    def write(self, stream: TextIO) -> None:
        for issue in self.issues:
            stream.write(f"{issue.code}: {issue.path}: {issue.message}\n")
        for path in self.drift:
            stream.write(f"generated-drift: {path}\n")

    def write_support(self, stream: TextIO) -> None:
        for report in sorted(self.support, key=lambda item: (item.host, item.plugin)):
            strategies = ", ".join(f"{name}={strategy}" for name, strategy in report.workflow_strategies)
            stream.write(f"{report.host}: {report.plugin}: {report.state} [{strategies}]\n")


def merge(reports: Sequence[BuildReport]) -> BuildReport:
    return BuildReport(
        issues=tuple(issue for report in reports for issue in report.issues),
        drift=tuple(path for report in reports for path in report.drift),
        support=tuple(item for report in reports for item in report.support),
    )
