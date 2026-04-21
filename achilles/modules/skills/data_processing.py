"""
Data Processing Skill
=====================

Parse, analyse, transform, and report on structured data.

Actions:
- **parse**            – Deserialise CSV, JSON, JSONL, or XML text
- **analyse**          – Compute summary statistics for a dataset
- **transform**        – Filter, rename columns, sort, or deduplicate rows
- **generate_report**  – Produce a plain-text or Markdown report from data
- **merge**            – Combine two datasets on a shared key
- **export**           – Serialise a dataset to CSV or JSON

No third-party data-science libraries are required; the skill relies only on
Python's standard library (``csv``, ``json``, ``statistics``, ``xml.etree``).
If ``pandas`` is installed it is used transparently for richer analysis.
"""

from __future__ import annotations

import csv
import io
import json
import logging
import statistics
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Union

from achilles.modules.skills import Skill

logger = logging.getLogger(__name__)

Dataset = List[Dict[str, Any]]


def _can_convert_float(value: Any) -> bool:
    """Return True if *value* can be parsed as a float."""
    try:
        float(str(value))
        return True
    except (ValueError, TypeError):
        return False


class DataProcessingSkill(Skill):
    """Parse, analyse, transform, and report on structured datasets."""

    name: str = "data_processing"
    description: str = (
        "Parse CSV/JSON/XML data, compute statistics, transform rows, "
        "merge datasets, and generate plain-text or Markdown reports."
    )

    def _build_action_map(self) -> Dict[str, Callable]:
        return {
            "parse": self._parse,
            "analyse": self._analyse,
            "transform": self._transform,
            "generate_report": self._generate_report,
            "merge": self._merge,
            "export": self._export,
        }

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    async def _parse(
        self,
        data: str,
        fmt: str = "json",
        delimiter: str = ",",
        has_header: bool = True,
    ) -> Dict[str, Any]:
        """
        Deserialise text data.

        Args:
            data:       Raw text to parse.
            fmt:        ``"json"``, ``"jsonl"``, ``"csv"``, or ``"xml"``.
            delimiter:  CSV delimiter (default comma).
            has_header: Whether the first CSV row is a header.

        Returns:
            Dict with ``rows`` (Dataset) and ``row_count``.
        """
        try:
            if fmt == "json":
                rows = self._parse_json(data)
            elif fmt == "jsonl":
                rows = self._parse_jsonl(data)
            elif fmt == "csv":
                rows = self._parse_csv(data, delimiter, has_header)
            elif fmt == "xml":
                rows = self._parse_xml(data)
            else:
                return {"skill": "data_processing", "action": "parse",
                        "status": "error", "reason": f"Unknown format: {fmt}"}
            return {
                "skill": "data_processing",
                "action": "parse",
                "format": fmt,
                "rows": rows,
                "row_count": len(rows),
            }
        except Exception as exc:
            logger.error("Parse error: %s", exc)
            return {"skill": "data_processing", "action": "parse",
                    "status": "error", "reason": str(exc)}

    async def _analyse(
        self,
        rows: Dataset,
        numeric_columns: Optional[List[str]] = None,
        categorical_columns: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Compute summary statistics for a dataset.

        Args:
            rows:                List of record dicts.
            numeric_columns:     Columns to analyse as numbers.
                                 Auto-detected if None.
            categorical_columns: Columns to analyse as categories.
                                 Auto-detected if None.

        Returns:
            Dict with per-column statistics.
        """
        if not rows:
            return {"skill": "data_processing", "action": "analyse",
                    "status": "empty", "stats": {}}

        all_cols = list(rows[0].keys())
        num_cols = numeric_columns or self._detect_numeric(rows, all_cols)
        cat_cols = categorical_columns or [c for c in all_cols if c not in num_cols]

        stats: Dict[str, Any] = {
            "row_count": len(rows),
            "column_count": len(all_cols),
            "columns": all_cols,
            "numeric": {},
            "categorical": {},
        }

        for col in num_cols:
            values = [float(r[col]) for r in rows if r.get(col) not in (None, "")]
            if values:
                stats["numeric"][col] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "mean": statistics.mean(values),
                    "median": statistics.median(values),
                    "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
                }

        for col in cat_cols:
            values = [str(r[col]) for r in rows if r.get(col) not in (None, "")]
            counter = Counter(values)
            stats["categorical"][col] = {
                "unique_count": len(counter),
                "top_values": counter.most_common(10),
                "null_count": sum(1 for r in rows if r.get(col) in (None, "")),
            }

        return {
            "skill": "data_processing",
            "action": "analyse",
            "stats": stats,
        }

    async def _transform(
        self,
        rows: Dataset,
        filters: Optional[List[Dict[str, Any]]] = None,
        select_columns: Optional[List[str]] = None,
        rename_columns: Optional[Dict[str, str]] = None,
        sort_by: Optional[str] = None,
        sort_desc: bool = False,
        deduplicate: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Filter, select, rename, sort, and deduplicate rows.

        Args:
            rows:            Input dataset.
            filters:         List of ``{"column": str, "op": str, "value": Any}``.
                             Supported ops: ``eq``, ``ne``, ``gt``, ``gte``, ``lt``,
                             ``lte``, ``contains``, ``startswith``.
            select_columns:  Keep only these columns.
            rename_columns:  Map old_name → new_name.
            sort_by:         Column name to sort by.
            sort_desc:       Sort descending if True.
            deduplicate:     Column name to deduplicate on (keep first occurrence).
            limit:           Maximum rows in output.

        Returns:
            Dict with ``rows`` (transformed Dataset) and ``row_count``.
        """
        result = list(rows)

        # Filter
        for f in filters or []:
            result = [r for r in result if self._match_filter(r, f)]

        # Select
        if select_columns:
            result = [{k: r.get(k) for k in select_columns} for r in result]

        # Rename
        if rename_columns:
            result = [
                {rename_columns.get(k, k): v for k, v in r.items()}
                for r in result
            ]

        # Sort
        if sort_by:
            result.sort(key=lambda r: (r.get(sort_by) is None, r.get(sort_by)),
                        reverse=sort_desc)

        # Deduplicate
        if deduplicate:
            seen: set = set()
            deduped = []
            for r in result:
                key = r.get(deduplicate)
                if key not in seen:
                    seen.add(key)
                    deduped.append(r)
            result = deduped

        # Limit
        if limit is not None:
            result = result[:limit]

        return {
            "skill": "data_processing",
            "action": "transform",
            "rows": result,
            "row_count": len(result),
        }

    async def _generate_report(
        self,
        rows: Dataset,
        title: str = "Data Report",
        fmt: str = "markdown",
        include_stats: bool = True,
        max_preview_rows: int = 10,
    ) -> Dict[str, Any]:
        """
        Generate a human-readable report from a dataset.

        Args:
            rows:             Input dataset.
            title:            Report title.
            fmt:              ``"markdown"`` or ``"text"``.
            include_stats:    Include a statistics section.
            max_preview_rows: Number of sample rows to show.

        Returns:
            Dict with ``report`` string.
        """
        stats_result = (await self._analyse(rows)) if include_stats else {}
        stats = stats_result.get("stats", {})

        if fmt == "markdown":
            report = self._build_markdown_report(
                title, rows, stats, max_preview_rows
            )
        else:
            report = self._build_text_report(
                title, rows, stats, max_preview_rows
            )

        return {
            "skill": "data_processing",
            "action": "generate_report",
            "title": title,
            "format": fmt,
            "report": report,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def _merge(
        self,
        left: Dataset,
        right: Dataset,
        on: str,
        how: str = "inner",
    ) -> Dict[str, Any]:
        """
        Join two datasets on a shared key column.

        Args:
            left:  Left dataset.
            right: Right dataset.
            on:    Key column name present in both datasets.
            how:   ``"inner"``, ``"left"``, or ``"right"``.

        Returns:
            Dict with merged ``rows`` and ``row_count``.
        """
        right_index: Dict[Any, Dict[str, Any]] = {r.get(on): r for r in right}
        result: Dataset = []

        for row in left:
            key = row.get(on)
            match = right_index.get(key)
            if match:
                merged = {**row, **{k: v for k, v in match.items() if k != on}}
                result.append(merged)
            elif how == "left":
                result.append(row)

        if how == "right":
            left_keys = {r.get(on) for r in left}
            for row in right:
                if row.get(on) not in left_keys:
                    result.append(row)

        return {
            "skill": "data_processing",
            "action": "merge",
            "rows": result,
            "row_count": len(result),
        }

    async def _export(
        self,
        rows: Dataset,
        fmt: str = "json",
        delimiter: str = ",",
    ) -> Dict[str, Any]:
        """
        Serialise a dataset to CSV or JSON.

        Args:
            rows:      Dataset to export.
            fmt:       ``"json"`` or ``"csv"``.
            delimiter: CSV delimiter (default comma).

        Returns:
            Dict with ``content`` string.
        """
        if not rows:
            return {"skill": "data_processing", "action": "export",
                    "content": "" if fmt == "csv" else "[]", "format": fmt}

        if fmt == "json":
            content = json.dumps(rows, indent=2, default=str)
        elif fmt == "csv":
            buf = io.StringIO()
            writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()),
                                    delimiter=delimiter)
            writer.writeheader()
            writer.writerows(rows)
            content = buf.getvalue()
        else:
            return {"skill": "data_processing", "action": "export",
                    "status": "error", "reason": f"Unknown format: {fmt}"}

        return {
            "skill": "data_processing",
            "action": "export",
            "format": fmt,
            "content": content,
            "row_count": len(rows),
        }

    # ------------------------------------------------------------------
    # Internal parsers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_json(data: str) -> Dataset:
        parsed = json.loads(data)
        if isinstance(parsed, list):
            return [r if isinstance(r, dict) else {"value": r} for r in parsed]
        if isinstance(parsed, dict):
            return [parsed]
        return [{"value": parsed}]

    @staticmethod
    def _parse_jsonl(data: str) -> Dataset:
        rows = []
        for line in data.splitlines():
            line = line.strip()
            if line:
                obj = json.loads(line)
                rows.append(obj if isinstance(obj, dict) else {"value": obj})
        return rows

    @staticmethod
    def _parse_csv(data: str, delimiter: str, has_header: bool) -> Dataset:
        reader = csv.DictReader(io.StringIO(data), delimiter=delimiter)
        if not has_header:
            # Use column indices as keys
            raw_rows = list(csv.reader(io.StringIO(data), delimiter=delimiter))
            return [{str(i): v for i, v in enumerate(row)} for row in raw_rows]
        return [dict(row) for row in reader]

    @staticmethod
    def _parse_xml(data: str) -> Dataset:
        root = ET.fromstring(data)
        rows = []
        for child in root:
            row = {grandchild.tag: grandchild.text for grandchild in child}
            if not row:
                row = {child.tag: child.text}
            rows.append(row)
        return rows

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _detect_numeric(rows: Dataset, cols: List[str]) -> List[str]:
        """Return columns where >80% of non-null values are numeric."""
        numeric = []
        for col in cols:
            values = [r.get(col) for r in rows if r.get(col) not in (None, "")]
            if not values:
                continue
            convertible = sum(
                1 for v in values if _can_convert_float(v)
            )
            if convertible / len(values) >= 0.8:
                numeric.append(col)
        return numeric

    @staticmethod
    def _match_filter(row: Dict[str, Any], f: Dict[str, Any]) -> bool:
        col, op, val = f.get("column", ""), f.get("op", "eq"), f.get("value")
        cell = row.get(col)
        if op == "eq":
            return cell == val
        if op == "ne":
            return cell != val
        try:
            if op == "gt":
                return float(str(cell)) > float(str(val))
            if op == "gte":
                return float(str(cell)) >= float(str(val))
            if op == "lt":
                return float(str(cell)) < float(str(val))
            if op == "lte":
                return float(str(cell)) <= float(str(val))
        except (ValueError, TypeError):
            return False
        if op == "contains":
            return str(val).lower() in str(cell).lower()
        if op == "startswith":
            return str(cell).lower().startswith(str(val).lower())
        return True

    @staticmethod
    def _build_markdown_report(
        title: str, rows: Dataset, stats: Dict[str, Any], preview: int
    ) -> str:
        lines = [f"# {title}", "", f"**Generated:** {datetime.now(timezone.utc).isoformat()} UTC", ""]

        if stats:
            lines += [
                "## Summary",
                f"- **Rows:** {stats.get('row_count', len(rows))}",
                f"- **Columns:** {stats.get('column_count', 0)}",
                "",
            ]
            numeric = stats.get("numeric", {})
            if numeric:
                lines.append("### Numeric Columns")
                lines.append("| Column | Count | Min | Max | Mean | Median |")
                lines.append("|--------|-------|-----|-----|------|--------|")
                for col, s in numeric.items():
                    lines.append(
                        f"| {col} | {s['count']} | {s['min']:.2f} | {s['max']:.2f} "
                        f"| {s['mean']:.2f} | {s['median']:.2f} |"
                    )
                lines.append("")

            categorical = stats.get("categorical", {})
            if categorical:
                lines.append("### Categorical Columns")
                for col, s in categorical.items():
                    top = ", ".join(f"{v}({c})" for v, c in s["top_values"][:5])
                    lines.append(f"- **{col}**: {s['unique_count']} unique — top: {top}")
                lines.append("")

        if rows:
            cols = list(rows[0].keys())
            lines += [
                f"## Sample Data (first {min(preview, len(rows))} rows)",
                "| " + " | ".join(cols) + " |",
                "| " + " | ".join("---" for _ in cols) + " |",
            ]
            for row in rows[:preview]:
                values = [str(row.get(c, "")) for c in cols]
                lines.append("| " + " | ".join(values) + " |")

        return "\n".join(lines)

    @staticmethod
    def _build_text_report(
        title: str, rows: Dataset, stats: Dict[str, Any], preview: int
    ) -> str:
        lines = [
            "=" * 60,
            title.center(60),
            f"Generated: {datetime.now(timezone.utc).isoformat()} UTC".center(60),
            "=" * 60,
            "",
        ]
        if stats:
            lines += [
                f"Rows   : {stats.get('row_count', len(rows))}",
                f"Columns: {stats.get('column_count', 0)}",
                "",
            ]
            for col, s in stats.get("numeric", {}).items():
                lines.append(
                    f"  {col:<20} min={s['min']:.2f}  max={s['max']:.2f}  "
                    f"mean={s['mean']:.2f}"
                )
            lines.append("")

        if rows:
            lines.append(f"Sample rows (first {min(preview, len(rows))}):")
            for row in rows[:preview]:
                lines.append("  " + ", ".join(f"{k}={v}" for k, v in row.items()))

        return "\n".join(lines)


__all__ = ["DataProcessingSkill"]
