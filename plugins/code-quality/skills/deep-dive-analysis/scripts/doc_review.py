#!/usr/bin/env python3
"""
Documentation Review Tool for Deep Dive Analysis (Phase 8)

SECURITY HARDENED VERSION - Addresses all critical review findings.

Provides commands for:
- Scanning documentation health
- Validating and fixing broken links (with backup)
- Verifying documentation against source code (AST-based)
- Validating verification markers point to real code
- Updating navigation indexes
- Running full maintenance workflow

Usage:
    python doc_review.py scan --path docs/ --output doc_health_report.json
    python doc_review.py validate-links --path docs/ [--fix] [--dry-run]
    python doc_review.py verify --doc <doc_path> --source <source_path>
    python doc_review.py validate-markers --path docs/
    python doc_review.py update-indexes --search-index <path> --by-domain <path>
    python doc_review.py full-maintenance --path docs/ [--auto-fix] [--dry-run]
"""

import argparse
import json
import logging
import re
import shutil
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

# Import AST parser for real code verification (C4 fix)
try:
    from ast_parser import parse_file, ParseResult
    AST_AVAILABLE = True
except ImportError:
    AST_AVAILABLE = False
    ParseResult = None

# Configure logging (replaces print statements)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class DocFile:
    """Represents a documentation file with metadata."""
    path: str
    relative_path: str
    line_count: int
    has_frontmatter: bool = False
    last_updated: Optional[str] = None
    has_todos: bool = False
    todo_count: int = 0
    broken_links: list = field(default_factory=list)
    outbound_links: list = field(default_factory=list)
    inbound_links: int = 0
    status: str = "unknown"  # verified, needs_update, obsolete
    # Verification tracking (markers are CLAIMS until validated)
    verified_claims: int = 0      # [VERIFIED:...] markers
    unverified_claims: int = 0    # [UNVERIFIED] markers
    validated_claims: int = 0     # Markers that passed tool validation
    stale_claims: int = 0         # Markers pointing to non-existent code
    deprecated_count: int = 0
    verification_ratio: float = 0.0


@dataclass
class MarkerValidation:
    """Result of validating a verification marker."""
    marker: str
    file_path: str
    line_number: int
    source_file: Optional[str] = None
    source_line: Optional[int] = None
    status: str = "unknown"  # valid, stale_file, stale_line, invalid_format
    error: Optional[str] = None
    code_at_line: Optional[str] = None


@dataclass
class HealthReport:
    """Documentation health report."""
    generated_at: str
    total_files: int
    files_by_directory: dict
    files_with_todos: list
    files_missing_metadata: list
    large_files: list
    broken_links: list
    obsolete_candidates: list
    # Verification integrity
    unverified_files: list
    low_verification_files: list
    stale_markers: list  # Markers pointing to non-existent code (C5)
    verification_summary: dict
    statistics: dict


class DocReviewer:
    """Documentation review and maintenance tool."""

    # Compiled regex patterns (M4 performance fix)
    TODO_PATTERN = re.compile(r'\b(TODO|FIXME|TBD|XXX)\b', re.IGNORECASE)
    VERIFIED_PATTERN = re.compile(r'\[VERIFIED:\s*([^\]]+)\]')
    VALIDATED_PATTERN = re.compile(r'\[VALIDATED:\s*([^\]]+)\]')
    UNVERIFIED_PATTERN = re.compile(r'\[UNVERIFIED[^\]]*\]')
    DEPRECATED_PATTERN = re.compile(r'\[DEPRECATED[^\]]*\]')
    LINK_PATTERN = re.compile(r'\[([^\]]*)\]\(([^)]+)\)')
    # Pattern to parse marker content: file.py:123 or file.py:123 @ date
    MARKER_CONTENT_PATTERN = re.compile(r'([^:@]+):(\d+)(?:\s*@\s*(.+))?')

    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path).resolve()
        self.docs_path = self.base_path / "docs"
        self.doc_files: dict[str, DocFile] = {}
        self.backup_dir: Optional[Path] = None
        self.dry_run = False
        self.changes_log: list[dict] = []

    def _validate_path(self, path: str, allowed_base: Path) -> Path:
        """
        Validate path is within allowed directory (C3 fix - path traversal protection).

        Raises ValueError if path escapes the allowed directory.
        """
        # Resolve the path
        if Path(path).is_absolute():
            resolved = Path(path).resolve()
        else:
            resolved = (allowed_base / path).resolve()

        # Check it's within bounds
        try:
            resolved.relative_to(allowed_base)
        except ValueError:
            raise ValueError(
                f"Security Error: Path '{path}' resolves outside allowed directory '{allowed_base}'"
            )

        return resolved

    def _create_backup(self, files_to_modify: list[Path]) -> Path:
        """
        Create backup of files before modification (C2 fix).

        Returns backup directory path.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.base_path / ".doc_backup" / timestamp
        backup_dir.mkdir(parents=True, exist_ok=True)

        for file_path in files_to_modify:
            if file_path.exists():
                relative = file_path.relative_to(self.base_path)
                backup_path = backup_dir / relative
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, backup_path)
                logger.debug(f"Backed up: {relative}")

        logger.info(f"Created backup at: {backup_dir}")
        self.backup_dir = backup_dir
        return backup_dir

    def _log_change(self, file_path: str, change_type: str, before: str, after: str, line: int = 0):
        """Log a change for dry-run mode or audit trail."""
        self.changes_log.append({
            "file": file_path,
            "type": change_type,
            "line": line,
            "before": before[:100] if before else None,
            "after": after[:100] if after else None,
            "timestamp": datetime.now().isoformat()
        })

    def scan(self, path: str = "docs/", output: Optional[str] = None) -> HealthReport:
        """Scan documentation and generate health report."""
        try:
            scan_path = self._validate_path(path, self.base_path)
        except ValueError as e:
            logger.error(str(e))
            sys.exit(1)

        if not scan_path.exists():
            logger.error(f"Path {scan_path} does not exist")
            sys.exit(1)

        logger.info(f"Scanning documentation in {scan_path}...")

        md_files = list(scan_path.rglob("*.md"))

        files_by_dir: dict[str, int] = {}
        files_with_todos: list[dict] = []
        files_missing_metadata: list[str] = []
        large_files: list[dict] = []
        failed_files: list[dict] = []  # Track failures (H2 fix)

        for md_file in md_files:
            try:
                relative = md_file.relative_to(self.base_path)
                dir_name = str(relative.parent).replace('\\', '/')

                files_by_dir[dir_name] = files_by_dir.get(dir_name, 0) + 1

                # Read with error handling for encoding issues (R1 fix)
                content = md_file.read_text(encoding='utf-8', errors='replace')
                lines = content.splitlines()
                line_count = len(lines)

                # Check frontmatter
                has_frontmatter = content.startswith('---')
                last_updated = None
                if has_frontmatter:
                    match = re.search(r'[Ll]ast[_\s][Uu]pdated[:\s]+(\d{4}-\d{2}-\d{2})', content[:500])
                    if match:
                        last_updated = match.group(1)

                # Check for TODOs
                todo_matches = self.TODO_PATTERN.findall(content)
                has_todos = len(todo_matches) > 0

                # Check for VERIFICATION MARKERS (claims, not validated yet)
                verified_claims = len(self.VERIFIED_PATTERN.findall(content))
                validated_claims = len(self.VALIDATED_PATTERN.findall(content))
                unverified_claims = len(self.UNVERIFIED_PATTERN.findall(content))
                deprecated_count = len(self.DEPRECATED_PATTERN.findall(content))

                # Calculate ratio
                total_verifiable = verified_claims + validated_claims + unverified_claims
                verification_ratio = (verified_claims + validated_claims) / total_verifiable if total_verifiable > 0 else 0.0

                doc_file = DocFile(
                    path=str(md_file),
                    relative_path=str(relative).replace('\\', '/'),
                    line_count=line_count,
                    has_frontmatter=has_frontmatter,
                    last_updated=last_updated,
                    has_todos=has_todos,
                    todo_count=len(todo_matches),
                    verified_claims=verified_claims,
                    validated_claims=validated_claims,
                    unverified_claims=unverified_claims,
                    deprecated_count=deprecated_count,
                    verification_ratio=verification_ratio
                )
                self.doc_files[str(relative).replace('\\', '/')] = doc_file

                if has_todos:
                    files_with_todos.append({
                        "file": str(relative).replace('\\', '/'),
                        "todo_count": len(todo_matches)
                    })

                if not last_updated:
                    files_missing_metadata.append(str(relative).replace('\\', '/'))

                if line_count > 1500:
                    large_files.append({
                        "file": str(relative).replace('\\', '/'),
                        "lines": line_count
                    })

            except Exception as e:
                logger.warning(f"Failed to process {md_file}: {e}")
                failed_files.append({"file": str(md_file), "error": str(e)})

        # Sort directories
        files_by_dir = dict(sorted(files_by_dir.items(), key=lambda x: -x[1]))

        # Collect verification statistics
        unverified_files = []
        low_verification_files = []
        total_verified = 0
        total_validated = 0
        total_unverified = 0
        total_deprecated = 0

        for doc in self.doc_files.values():
            total_verified += doc.verified_claims
            total_validated += doc.validated_claims
            total_unverified += doc.unverified_claims
            total_deprecated += doc.deprecated_count

            if doc.unverified_claims > 0:
                unverified_files.append({
                    "file": doc.relative_path,
                    "unverified_count": doc.unverified_claims,
                    "verified_count": doc.verified_claims + doc.validated_claims,
                    "ratio": doc.verification_ratio
                })

            if doc.verification_ratio < 0.5 and (doc.verified_claims + doc.validated_claims + doc.unverified_claims) > 0:
                low_verification_files.append({
                    "file": doc.relative_path,
                    "ratio": doc.verification_ratio,
                    "verified": doc.verified_claims + doc.validated_claims,
                    "unverified": doc.unverified_claims
                })

        total_claims = total_verified + total_validated + total_unverified
        verification_summary = {
            "total_verified_markers": total_verified,
            "total_validated_markers": total_validated,
            "total_unverified_markers": total_unverified,
            "total_deprecated_markers": total_deprecated,
            "files_with_unverified": len(unverified_files),
            "files_below_50_percent": len(low_verification_files),
            "overall_ratio": (total_verified + total_validated) / total_claims if total_claims > 0 else 0.0,
            "failed_files": len(failed_files)
        }

        report = HealthReport(
            generated_at=datetime.now().isoformat(),
            total_files=len(md_files),
            files_by_directory=files_by_dir,
            files_with_todos=sorted(files_with_todos, key=lambda x: -x["todo_count"]),
            files_missing_metadata=sorted(files_missing_metadata),
            large_files=sorted(large_files, key=lambda x: -x["lines"]),
            broken_links=[],
            obsolete_candidates=[],
            unverified_files=sorted(unverified_files, key=lambda x: -x["unverified_count"]),
            low_verification_files=sorted(low_verification_files, key=lambda x: x["ratio"]),
            stale_markers=[],
            verification_summary=verification_summary,
            statistics={
                "total_files": len(md_files),
                "files_with_todos": len(files_with_todos),
                "files_missing_metadata": len(files_missing_metadata),
                "large_files_count": len(large_files),
                "directories": len(files_by_dir),
                "verification_integrity": verification_summary,
                "failed_files": failed_files
            }
        )

        if output:
            try:
                output_path = self._validate_path(output, self.base_path)
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(asdict(report), f, indent=2)
                logger.info(f"Health report saved to {output_path}")
            except ValueError as e:
                logger.error(str(e))

        # Print summary
        self._print_health_summary(report, files_by_dir, total_verified, total_validated,
                                   total_unverified, total_deprecated, unverified_files,
                                   low_verification_files)

        return report

    def _print_health_summary(self, report, files_by_dir, total_verified, total_validated,
                              total_unverified, total_deprecated, unverified_files, low_verification_files):
        """Print formatted health summary."""
        print(f"\n{'='*60}")
        print("DOCUMENTATION HEALTH REPORT")
        print(f"{'='*60}")
        print(f"Total files: {report.total_files}")
        print(f"Directories: {len(files_by_dir)}")
        print(f"Files with TODOs: {len(report.files_with_todos)}")
        print(f"Files missing metadata: {len(report.files_missing_metadata)}")
        print(f"Large files (>1500 lines): {len(report.large_files)}")

        print(f"\n{'='*60}")
        print("VERIFICATION INTEGRITY (SOURCE OF TRUTH COMPLIANCE)")
        print(f"{'='*60}")
        print(f"[VERIFIED] markers (human claims):    {total_verified}")
        print(f"[VALIDATED] markers (tool-checked):   {total_validated}")
        print(f"[UNVERIFIED] markers:                 {total_unverified}")
        print(f"[DEPRECATED] markers:                 {total_deprecated}")
        print(f"Files with unverified claims: {len(unverified_files)}")
        print(f"Files below 50% verification: {len(low_verification_files)}")

        total_claims = total_verified + total_validated + total_unverified
        if total_claims > 0:
            ratio = (total_verified + total_validated) / total_claims * 100
            print(f"\nOVERALL VERIFICATION RATIO: {ratio:.1f}%")
            if ratio < 80:
                print("  WARNING: Documentation integrity below acceptable threshold!")
                print("  Run 'validate-markers' to check if claims are still valid.")
        else:
            print(f"\nNO VERIFICATION MARKERS FOUND")
            print("  ALL DOCUMENTATION SHOULD BE CONSIDERED UNVERIFIED")
            print("  Add [VERIFIED: file.py:line] markers after code verification")

    def validate_links(self, path: str = "docs/", fix: bool = False, dry_run: bool = False) -> list[dict]:
        """Validate all relative links in documentation."""
        self.dry_run = dry_run

        try:
            scan_path = self._validate_path(path, self.base_path)
        except ValueError as e:
            logger.error(str(e))
            sys.exit(1)

        broken_links: list[dict] = []
        files_with_broken: set[Path] = set()

        logger.info(f"Validating links in {scan_path}...")

        md_files = list(scan_path.rglob("*.md"))

        for md_file in md_files:
            try:
                relative = md_file.relative_to(self.base_path)
                content = md_file.read_text(encoding='utf-8', errors='replace')
                lines = content.splitlines()

                for line_num, line in enumerate(lines, 1):
                    for match in self.LINK_PATTERN.finditer(line):
                        link_text = match.group(1)
                        link_target = match.group(2)

                        if link_target.startswith(('http://', 'https://', 'mailto:', '#')):
                            continue

                        target_path = link_target.split('#')[0]
                        if not target_path:
                            continue

                        resolved = (md_file.parent / target_path).resolve()

                        if not resolved.exists():
                            broken_links.append({
                                "source_file": str(relative).replace('\\', '/'),
                                "line": line_num,
                                "link_text": link_text,
                                "target": link_target,
                                "resolved": str(resolved)
                            })
                            files_with_broken.add(md_file)

            except Exception as e:
                logger.warning(f"Could not process {md_file}: {e}")

        print(f"\n{'='*60}")
        print("LINK VALIDATION RESULTS")
        print(f"{'='*60}")
        print(f"Total broken links: {len(broken_links)}")

        if broken_links:
            print("\nBroken links found:")
            for bl in broken_links[:20]:
                print(f"  {bl['source_file']}:{bl['line']}")
                print(f"    -> {bl['target']}")
            if len(broken_links) > 20:
                print(f"  ... and {len(broken_links) - 20} more")

        if fix and broken_links:
            if dry_run:
                print("\n[DRY-RUN] Would fix the following files:")
                for f in files_with_broken:
                    print(f"  - {f.relative_to(self.base_path)}")
            else:
                # Create backup first (C2 fix)
                self._create_backup(list(files_with_broken))
                self._fix_broken_links(broken_links)

        return broken_links

    def _fix_broken_links(self, broken_links: list[dict]) -> None:
        """Remove or comment out broken links (with backup already created)."""
        by_file: dict[str, list] = {}
        for bl in broken_links:
            src = bl['source_file']
            if src not in by_file:
                by_file[src] = []
            by_file[src].append(bl)

        for src_file, links in by_file.items():
            file_path = self.base_path / src_file
            try:
                content = file_path.read_text(encoding='utf-8', errors='replace')
                links_sorted = sorted(links, key=lambda x: -x['line'])

                lines = content.splitlines()
                for link in links_sorted:
                    line_idx = link['line'] - 1
                    if line_idx < len(lines):
                        old_line = lines[line_idx]
                        # Escape special regex chars in link text
                        escaped_text = re.escape(link['link_text'])
                        escaped_target = re.escape(link['target'])
                        pattern = re.compile(
                            r'\[' + escaped_text + r'\]\(' + escaped_target + r'[^)]*\)'
                        )
                        new_line = pattern.sub(f"~~{link['link_text']}~~ (link removed)", old_line)

                        self._log_change(src_file, "fix_link", old_line, new_line, link['line'])
                        lines[line_idx] = new_line

                file_path.write_text('\n'.join(lines), encoding='utf-8')
                logger.info(f"Fixed {len(links)} broken links in {src_file}")

            except Exception as e:
                logger.error(f"Error fixing {src_file}: {e}")

    def validate_markers(self, path: str = "docs/") -> list[MarkerValidation]:
        """
        Validate that verification markers point to existing files/lines (C5 fix).

        Checks [VERIFIED: file.py:123] and [VALIDATED: file.py:123] markers.
        """
        try:
            scan_path = self._validate_path(path, self.base_path)
        except ValueError as e:
            logger.error(str(e))
            sys.exit(1)

        logger.info(f"Validating verification markers in {scan_path}...")

        validations: list[MarkerValidation] = []
        md_files = list(scan_path.rglob("*.md"))

        for md_file in md_files:
            try:
                relative = md_file.relative_to(self.base_path)
                content = md_file.read_text(encoding='utf-8', errors='replace')
                lines = content.splitlines()

                for line_num, line in enumerate(lines, 1):
                    # Check VERIFIED markers
                    for match in self.VERIFIED_PATTERN.finditer(line):
                        marker_content = match.group(1)
                        validation = self._validate_single_marker(
                            marker=match.group(0),
                            marker_content=marker_content,
                            doc_file=str(relative).replace('\\', '/'),
                            doc_line=line_num
                        )
                        validations.append(validation)

                    # Check VALIDATED markers
                    for match in self.VALIDATED_PATTERN.finditer(line):
                        marker_content = match.group(1)
                        validation = self._validate_single_marker(
                            marker=match.group(0),
                            marker_content=marker_content,
                            doc_file=str(relative).replace('\\', '/'),
                            doc_line=line_num
                        )
                        validations.append(validation)

            except Exception as e:
                logger.warning(f"Could not process {md_file}: {e}")

        # Print results
        valid_count = sum(1 for v in validations if v.status == "valid")
        stale_count = sum(1 for v in validations if v.status.startswith("stale"))
        invalid_count = sum(1 for v in validations if v.status == "invalid_format")

        print(f"\n{'='*60}")
        print("MARKER VALIDATION RESULTS")
        print(f"{'='*60}")
        print(f"Total markers checked: {len(validations)}")
        print(f"  Valid (file + line exist): {valid_count}")
        print(f"  Stale (file or line missing): {stale_count}")
        print(f"  Invalid format: {invalid_count}")

        if stale_count > 0:
            print("\nSTALE MARKERS (need update):")
            for v in validations:
                if v.status.startswith("stale"):
                    print(f"  {v.file_path}:{v.line_number}")
                    print(f"    Marker: {v.marker}")
                    print(f"    Error: {v.error}")

        return validations

    def _validate_single_marker(self, marker: str, marker_content: str,
                                doc_file: str, doc_line: int) -> MarkerValidation:
        """Validate a single verification marker."""
        validation = MarkerValidation(
            marker=marker,
            file_path=doc_file,
            line_number=doc_line
        )

        # Parse marker content: file.py:123 or file.py:123 @ date
        content_match = self.MARKER_CONTENT_PATTERN.match(marker_content.strip())
        if not content_match:
            validation.status = "invalid_format"
            validation.error = f"Could not parse marker content: {marker_content}"
            return validation

        source_file = content_match.group(1).strip()
        source_line = int(content_match.group(2))

        validation.source_file = source_file
        validation.source_line = source_line

        # Try to find the source file in common project layouts
        possible_paths = [
            self.base_path / source_file,
            self.base_path / "src" / source_file,
            self.base_path / "lib" / source_file,
            self.base_path / "app" / source_file,
        ]

        source_path = None
        for p in possible_paths:
            if p.exists():
                source_path = p
                break

        if not source_path:
            validation.status = "stale_file"
            validation.error = f"Source file not found: {source_file}"
            return validation

        # Check line exists
        try:
            content = source_path.read_text(encoding='utf-8', errors='replace')
            lines = content.splitlines()

            if source_line > len(lines):
                validation.status = "stale_line"
                validation.error = f"Line {source_line} exceeds file length ({len(lines)} lines)"
                return validation

            validation.code_at_line = lines[source_line - 1].strip()[:100]
            validation.status = "valid"

        except Exception as e:
            validation.status = "stale_file"
            validation.error = f"Could not read file: {e}"

        return validation

    def verify_against_source(self, doc_path: str, source_path: str) -> dict:
        """
        Verify documentation accuracy against source code using AST (C4 fix).
        """
        try:
            doc_file = self._validate_path(doc_path, self.base_path)
            source_file = self._validate_path(source_path, self.base_path)
        except ValueError as e:
            logger.error(str(e))
            sys.exit(1)

        if not doc_file.exists():
            logger.error(f"Documentation file not found: {doc_file}")
            sys.exit(1)

        if not source_file.exists():
            logger.error(f"Source file not found: {source_file}")
            sys.exit(1)

        logger.info(f"Verifying {doc_path} against {source_path}...")

        doc_content = doc_file.read_text(encoding='utf-8', errors='replace')

        result = {
            "doc_file": doc_path,
            "source_file": source_path,
            "verified_at": datetime.now().isoformat(),
            "drift_detected": [],
            "verified_items": [],
            "status": "verified",
            "ast_used": AST_AVAILABLE
        }

        if AST_AVAILABLE and source_file.suffix == '.py':
            # Use AST for accurate parsing (C4 fix)
            try:
                parse_result = parse_file(source_file)

                # Get actual symbols from AST
                actual_classes = {c.name for c in parse_result.classes}
                actual_functions = {f.name for f in parse_result.functions}
                actual_methods = set()
                for cls in parse_result.classes:
                    for method in cls.methods:
                        actual_methods.add(f"{cls.name}.{method.name}")
                        actual_methods.add(method.name)

                # Find documented symbols
                doc_classes = set(re.findall(r'`(\w+)`\s*(?:class|Class)', doc_content))
                doc_classes.update(re.findall(r'###?\s*`?(\w+)`?\s*(?:\(class\)|Class)', doc_content))

                doc_functions = set(re.findall(r'`(\w+)\(`', doc_content))

                # Verify classes
                for cls in doc_classes:
                    if cls in actual_classes:
                        result["verified_items"].append(f"Class '{cls}' exists [line: {self._get_class_line(parse_result, cls)}]")
                    else:
                        result["drift_detected"].append(f"Class '{cls}' documented but NOT found in source")
                        result["status"] = "needs_update"

                # Verify functions/methods
                for func in doc_functions:
                    if func in actual_functions or func in actual_methods:
                        result["verified_items"].append(f"Function/method '{func}' exists")
                    elif not func.startswith('__') and func not in ('self', 'cls'):
                        result["drift_detected"].append(f"Function '{func}' documented but NOT found")
                        result["status"] = "needs_update"

            except Exception as e:
                logger.warning(f"AST parsing failed, falling back to regex: {e}")
                result["ast_used"] = False
                self._verify_with_regex(doc_content, source_file, result)
        else:
            self._verify_with_regex(doc_content, source_file, result)

        # Print results
        print(f"\n{'='*60}")
        print("VERIFICATION RESULTS")
        print(f"{'='*60}")
        print(f"Status: {result['status']}")
        print(f"AST parsing used: {result['ast_used']}")
        print(f"Verified items: {len(result['verified_items'])}")
        print(f"Drift detected: {len(result['drift_detected'])}")

        if result["drift_detected"]:
            print("\nDRIFT ITEMS (documentation does not match code):")
            for item in result["drift_detected"]:
                print(f"  - {item}")

        if result["verified_items"]:
            print(f"\nVERIFIED ITEMS ({len(result['verified_items'])}):")
            for item in result["verified_items"][:10]:
                print(f"  + {item}")
            if len(result["verified_items"]) > 10:
                print(f"  ... and {len(result['verified_items']) - 10} more")

        return result

    def _get_class_line(self, parse_result, class_name: str) -> int:
        """Get line number for a class from parse result."""
        for cls in parse_result.classes:
            if cls.name == class_name:
                return cls.line_number
        return 0

    def _verify_with_regex(self, doc_content: str, source_file: Path, result: dict):
        """Fallback regex-based verification (for non-Python files)."""
        source_content = source_file.read_text(encoding='utf-8', errors='replace')

        # Simple regex patterns
        source_classes = set(re.findall(r'class\s+(\w+)', source_content))
        source_functions = set(re.findall(r'def\s+(\w+)', source_content))

        doc_classes = set(re.findall(r'`(\w+)`\s*(?:class|Class)', doc_content))
        doc_functions = set(re.findall(r'`(\w+)\(`', doc_content))

        for cls in doc_classes:
            if cls in source_classes:
                result["verified_items"].append(f"Class '{cls}' found (regex)")
            else:
                result["drift_detected"].append(f"Class '{cls}' not found (regex)")
                result["status"] = "needs_update"

        for func in doc_functions:
            if func in source_functions or func in source_classes:
                result["verified_items"].append(f"Function '{func}' found (regex)")

    def update_indexes(
        self,
        search_index: Optional[str] = None,
        by_domain: Optional[str] = None,
        dry_run: bool = False
    ) -> None:
        """Update navigation index files with current statistics."""
        self.dry_run = dry_run

        if not self.doc_files:
            self.scan()

        total_files = len(self.doc_files)
        today = datetime.now().strftime("%Y-%m-%d")

        if search_index:
            try:
                index_path = self._validate_path(search_index, self.base_path)
            except ValueError as e:
                logger.error(str(e))
                return

            if index_path.exists():
                logger.info(f"Updating {search_index}...")
                content = index_path.read_text(encoding='utf-8', errors='replace')

                new_content = re.sub(
                    r'\*\*Last Updated\*\*:\s*\d{4}-\d{2}-\d{2}',
                    f'**Last Updated**: {today}',
                    content
                )

                version_match = re.search(r'\*\*Version\*\*:\s*(\d+)\.(\d+)\.(\d+)', content)
                if version_match:
                    major, minor, patch = version_match.groups()
                    new_version = f"{major}.{minor}.{int(patch) + 1}"
                    new_content = re.sub(
                        r'\*\*Version\*\*:\s*\d+\.\d+\.\d+',
                        f'**Version**: {new_version}',
                        new_content
                    )

                if dry_run:
                    print(f"[DRY-RUN] Would update {search_index}")
                else:
                    # Backup first
                    self._create_backup([index_path])
                    index_path.write_text(new_content, encoding='utf-8')
                    logger.info(f"  Updated version and last_updated date")

        if by_domain:
            try:
                domain_path = self._validate_path(by_domain, self.base_path)
            except ValueError as e:
                logger.error(str(e))
                return

            if domain_path.exists():
                logger.info(f"Updating {by_domain}...")
                content = domain_path.read_text(encoding='utf-8', errors='replace')

                new_content = re.sub(
                    r'\*\*Last Updated\*\*:\s*\d{4}-\d{2}-\d{2}',
                    f'**Last Updated**: {today}',
                    content
                )

                if dry_run:
                    print(f"[DRY-RUN] Would update {by_domain}")
                else:
                    self._create_backup([domain_path])
                    domain_path.write_text(new_content, encoding='utf-8')
                    logger.info(f"  Updated last_updated date")

        print(f"\nIndex updates complete. Total docs: {total_files}")

    def full_maintenance(
        self,
        path: str = "docs/",
        auto_fix: bool = False,
        output: Optional[str] = None,
        dry_run: bool = False
    ) -> HealthReport:
        """Run complete Phase 8 documentation maintenance workflow."""
        self.dry_run = dry_run

        print("=" * 60)
        print("PHASE 8: FULL DOCUMENTATION MAINTENANCE")
        if dry_run:
            print("*** DRY-RUN MODE - No files will be modified ***")
        print("=" * 60)

        # Step 1: Scan
        print("\n[1/5] Scanning documentation health...")
        report = self.scan(path)

        # Step 2: Validate links
        print("\n[2/5] Validating links...")
        broken_links = self.validate_links(path, fix=auto_fix, dry_run=dry_run)
        report.broken_links = broken_links

        # Step 3: Validate markers (C5 fix)
        print("\n[3/5] Validating verification markers...")
        marker_validations = self.validate_markers(path)
        stale_markers = [asdict(v) for v in marker_validations if v.status.startswith("stale")]
        report.stale_markers = stale_markers

        # Step 4: Update indexes (if navigation files exist)
        print("\n[4/5] Updating navigation indexes...")
        search_index = self.base_path / "docs" / "SEARCH_INDEX.md"
        by_domain = self.base_path / "docs" / "BY_DOMAIN.md"
        if search_index.exists() or by_domain.exists():
            self.update_indexes(
                search_index=str(search_index) if search_index.exists() else None,
                by_domain=str(by_domain) if by_domain.exists() else None,
                dry_run=dry_run
            )
        else:
            logger.info("No navigation index files found, skipping...")

        # Step 5: Generate final report
        print("\n[5/5] Generating final health report...")
        report.statistics["broken_links_count"] = len(broken_links)
        report.statistics["stale_markers_count"] = len(stale_markers)

        if output:
            try:
                output_path = self._validate_path(output, self.base_path)
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(asdict(report), f, indent=2)
                logger.info(f"Final report saved to {output_path}")
            except ValueError as e:
                logger.error(str(e))

        print("\n" + "=" * 60)
        print("MAINTENANCE COMPLETE")
        print("=" * 60)
        print(f"Total files: {report.total_files}")
        print(f"Broken links: {len(broken_links)}")
        print(f"Stale markers: {len(stale_markers)}")
        print(f"Files with TODOs: {len(report.files_with_todos)}")

        if self.backup_dir:
            print(f"\nBackup location: {self.backup_dir}")

        if self.changes_log:
            print(f"\nChanges made: {len(self.changes_log)}")

        return report


def main():
    parser = argparse.ArgumentParser(
        description="Documentation Review Tool for Deep Dive Analysis (Phase 8)"
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # scan command
    scan_parser = subparsers.add_parser("scan", help="Scan documentation health")
    scan_parser.add_argument("--path", "-p", default="docs/", help="Path to scan")
    scan_parser.add_argument("--output", "-o", help="Output JSON report file")

    # validate-links command
    links_parser = subparsers.add_parser("validate-links", help="Validate documentation links")
    links_parser.add_argument("--path", "-p", default="docs/", help="Path to scan")
    links_parser.add_argument("--fix", action="store_true", help="Fix broken links")
    links_parser.add_argument("--dry-run", action="store_true", help="Show changes without applying")

    # validate-markers command (C5 fix)
    markers_parser = subparsers.add_parser("validate-markers", help="Validate verification markers")
    markers_parser.add_argument("--path", "-p", default="docs/", help="Path to scan")

    # verify command
    verify_parser = subparsers.add_parser("verify", help="Verify doc against source")
    verify_parser.add_argument("--doc", "-d", required=True, help="Documentation file")
    verify_parser.add_argument("--source", "-s", required=True, help="Source code file")

    # update-indexes command
    index_parser = subparsers.add_parser("update-indexes", help="Update navigation indexes")
    index_parser.add_argument("--search-index", help="Path to SEARCH_INDEX.md")
    index_parser.add_argument("--by-domain", help="Path to BY_DOMAIN.md")
    index_parser.add_argument("--dry-run", action="store_true", help="Show changes without applying")

    # full-maintenance command
    full_parser = subparsers.add_parser("full-maintenance", help="Run full maintenance")
    full_parser.add_argument("--path", "-p", default="docs/", help="Path to scan")
    full_parser.add_argument("--auto-fix", action="store_true", help="Auto-fix issues")
    full_parser.add_argument("--output", "-o", help="Output JSON report file")
    full_parser.add_argument("--dry-run", action="store_true", help="Show changes without applying")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    reviewer = DocReviewer()

    if args.command == "scan":
        reviewer.scan(args.path, args.output)
    elif args.command == "validate-links":
        reviewer.validate_links(args.path, args.fix, getattr(args, 'dry_run', False))
    elif args.command == "validate-markers":
        reviewer.validate_markers(args.path)
    elif args.command == "verify":
        reviewer.verify_against_source(args.doc, args.source)
    elif args.command == "update-indexes":
        reviewer.update_indexes(args.search_index, args.by_domain, getattr(args, 'dry_run', False))
    elif args.command == "full-maintenance":
        reviewer.full_maintenance(args.path, args.auto_fix, args.output, getattr(args, 'dry_run', False))


if __name__ == "__main__":
    main()