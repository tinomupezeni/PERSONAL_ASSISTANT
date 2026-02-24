"""
Self-Analysis Module for Ada.

Ada identifies gaps in her own functionality and suggests improvements.
She analyzes:
- Failed operations and errors
- Missing features users ask about
- Incomplete implementations
- Performance issues
- Code quality
"""

import os
import json
import ast
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    from groq import Groq
except ImportError:
    Groq = None

BASE_DIR = Path(__file__).parent
GAPS_DIR = BASE_DIR / "data" / "gaps"
GAPS_DIR.mkdir(parents=True, exist_ok=True)

GAPS_FILE = GAPS_DIR / "identified_gaps.json"
IMPROVEMENTS_FILE = GAPS_DIR / "improvement_log.json"


# ============================================================
# GAP STORAGE
# ============================================================

def get_gaps() -> dict:
    """Get identified gaps."""
    if GAPS_FILE.exists():
        return json.loads(GAPS_FILE.read_text())
    return {
        "gaps": [],
        "last_analysis": None
    }


def add_gap(
    category: str,
    description: str,
    severity: str = "medium",
    suggested_fix: str = "",
    source: str = "manual"
) -> dict:
    """Add a gap to the list."""
    data = get_gaps()

    gap = {
        "id": len(data["gaps"]) + 1,
        "category": category,
        "description": description,
        "severity": severity,  # low, medium, high, critical
        "suggested_fix": suggested_fix,
        "source": source,  # manual, error_log, user_request, code_analysis
        "status": "open",  # open, in_progress, fixed, wont_fix
        "identified_at": datetime.now().isoformat()
    }

    data["gaps"].append(gap)
    GAPS_FILE.write_text(json.dumps(data, indent=2))
    return gap


def update_gap_status(gap_id: int, status: str, notes: str = "") -> bool:
    """Update gap status."""
    data = get_gaps()

    for gap in data["gaps"]:
        if gap["id"] == gap_id:
            gap["status"] = status
            if notes:
                gap["resolution_notes"] = notes
            gap["updated_at"] = datetime.now().isoformat()
            GAPS_FILE.write_text(json.dumps(data, indent=2))
            return True

    return False


def get_open_gaps() -> list:
    """Get all open gaps."""
    data = get_gaps()
    return [g for g in data["gaps"] if g["status"] == "open"]


# ============================================================
# CODE ANALYSIS
# ============================================================

def analyze_code_structure() -> dict:
    """Analyze Ada's code structure."""
    results = {
        "files": [],
        "total_lines": 0,
        "functions": 0,
        "classes": 0,
        "todos_in_code": [],
        "incomplete_functions": []
    }

    py_files = list(BASE_DIR.glob("*.py"))

    for file in py_files:
        try:
            content = file.read_text(encoding="utf-8")
            lines = content.split("\n")

            file_info = {
                "name": file.name,
                "lines": len(lines),
                "functions": 0,
                "classes": 0
            }

            # Parse AST
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        file_info["functions"] += 1
                        results["functions"] += 1

                        # Check for pass/NotImplemented
                        body = ast.unparse(node) if hasattr(ast, 'unparse') else ""
                        if "pass" in body or "NotImplemented" in body:
                            results["incomplete_functions"].append(
                                f"{file.name}:{node.name}"
                            )

                    elif isinstance(node, ast.ClassDef):
                        file_info["classes"] += 1
                        results["classes"] += 1

            except SyntaxError:
                file_info["syntax_error"] = True

            # Find TODOs and FIXMEs
            for i, line in enumerate(lines, 1):
                if "TODO" in line or "FIXME" in line or "XXX" in line:
                    results["todos_in_code"].append({
                        "file": file.name,
                        "line": i,
                        "text": line.strip()
                    })

            results["files"].append(file_info)
            results["total_lines"] += len(lines)

        except Exception as e:
            results["files"].append({
                "name": file.name,
                "error": str(e)
            })

    return results


def analyze_readme_vs_code() -> dict:
    """Compare README claims vs actual code."""
    readme_path = BASE_DIR / "README.md"
    if not readme_path.exists():
        return {"error": "No README.md found"}

    readme = readme_path.read_text(encoding="utf-8")
    results = {
        "claimed_features": [],
        "missing_implementations": []
    }

    # Extract checked features from README
    for line in readme.split("\n"):
        if "- [x]" in line:
            feature = line.split("- [x]")[1].strip()
            results["claimed_features"].append(feature)
        elif "- [ ]" in line:
            feature = line.split("- [ ]")[1].strip()
            results["missing_implementations"].append(feature)

    return results


def analyze_error_patterns() -> dict:
    """Analyze common error patterns from logs."""
    # Check for error log or history
    results = {
        "common_errors": [],
        "suggestions": []
    }

    # Look for any error logs
    log_files = list((BASE_DIR / "data").rglob("*.log")) if (BASE_DIR / "data").exists() else []

    # Also check briefs for mentioned issues
    briefs_dir = BASE_DIR / "data" / "briefs"
    if briefs_dir.exists():
        for brief_file in list(briefs_dir.glob("*.json"))[-7:]:  # Last 7 days
            try:
                brief = json.loads(brief_file.read_text())
                if "RISK" in str(brief):
                    results["common_errors"].append({
                        "source": brief_file.name,
                        "type": "brief_risk"
                    })
            except:
                pass

    return results


# ============================================================
# GAP DETECTION
# ============================================================

def detect_gaps() -> list:
    """Run full gap detection analysis."""
    detected = []

    # 1. Code structure analysis
    code = analyze_code_structure()

    if code.get("incomplete_functions"):
        for func in code["incomplete_functions"]:
            detected.append({
                "category": "incomplete_code",
                "description": f"Function has placeholder: {func}",
                "severity": "medium",
                "suggested_fix": f"Implement the function in {func}",
                "source": "code_analysis"
            })

    if code.get("todos_in_code"):
        for todo in code["todos_in_code"][:5]:  # Top 5
            detected.append({
                "category": "todo_item",
                "description": f"{todo['file']}:{todo['line']} - {todo['text'][:80]}",
                "severity": "low",
                "suggested_fix": "Address the TODO comment",
                "source": "code_analysis"
            })

    # 2. README vs Code
    readme_check = analyze_readme_vs_code()

    if readme_check.get("missing_implementations"):
        for feature in readme_check["missing_implementations"][:5]:
            detected.append({
                "category": "missing_feature",
                "description": feature,
                "severity": "medium",
                "suggested_fix": f"Implement: {feature}",
                "source": "readme_analysis"
            })

    # 3. Known architectural gaps
    known_gaps = [
        {
            "category": "persistence",
            "description": "Daemon stops when terminal closes",
            "severity": "high",
            "suggested_fix": "Convert to Windows Service or use Task Scheduler",
            "source": "known_issue"
        },
        {
            "category": "input",
            "description": "Voice input unreliable",
            "severity": "medium",
            "suggested_fix": "Improve Whisper integration or accept typed input",
            "source": "known_issue"
        },
        {
            "category": "integration",
            "description": "Google Docs requires OAuth setup",
            "severity": "low",
            "suggested_fix": "Complete OAuth flow with credentials.json",
            "source": "known_issue"
        }
    ]

    # Only add known gaps if not already in list
    existing = get_gaps()
    existing_descs = [g["description"] for g in existing.get("gaps", [])]

    for gap in known_gaps:
        if gap["description"] not in existing_descs:
            detected.append(gap)

    return detected


def run_full_analysis() -> dict:
    """Run comprehensive self-analysis."""
    print("Running self-analysis...")

    results = {
        "timestamp": datetime.now().isoformat(),
        "code_stats": analyze_code_structure(),
        "readme_check": analyze_readme_vs_code(),
        "new_gaps": []
    }

    # Detect gaps
    detected = detect_gaps()

    # Add new gaps
    for gap_data in detected:
        gap = add_gap(**gap_data)
        results["new_gaps"].append(gap)

    # Update last analysis time
    data = get_gaps()
    data["last_analysis"] = results["timestamp"]
    GAPS_FILE.write_text(json.dumps(data, indent=2))

    return results


# ============================================================
# LLM-POWERED ANALYSIS
# ============================================================

def get_improvement_suggestions() -> str:
    """Use LLM to analyze gaps and suggest improvements."""
    if not Groq or not os.environ.get("GROQ_API_KEY"):
        return "LLM not available for analysis."

    gaps = get_open_gaps()
    code_stats = analyze_code_structure()

    prompt = f"""Analyze Ada AI assistant's current state and suggest improvements.

CURRENT STATS:
- Total files: {len(code_stats['files'])}
- Total lines: {code_stats['total_lines']}
- Functions: {code_stats['functions']}
- Classes: {code_stats['classes']}
- TODOs in code: {len(code_stats.get('todos_in_code', []))}
- Incomplete functions: {len(code_stats.get('incomplete_functions', []))}

OPEN GAPS ({len(gaps)}):
"""

    for gap in gaps[:10]:  # Top 10
        prompt += f"""
- [{gap['severity'].upper()}] {gap['category']}: {gap['description']}
  Suggested: {gap.get('suggested_fix', 'None')}
"""

    prompt += """

Based on this analysis, provide:
1. TOP 3 PRIORITIES - What should be fixed first and why
2. QUICK WINS - Easy improvements that add value
3. ARCHITECTURAL SUGGESTIONS - Bigger changes to consider
4. CODE QUALITY - Any patterns to improve

Be specific. Reference actual gaps. No generic advice."""

    try:
        client = Groq()
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=800,
            messages=[
                {"role": "system", "content": "You are a senior software architect reviewing an AI assistant's codebase."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Analysis error: {e}"


# ============================================================
# FORMATTED OUTPUT
# ============================================================

def get_gaps_summary() -> str:
    """Get formatted summary of all gaps."""
    gaps = get_gaps()
    open_gaps = [g for g in gaps["gaps"] if g["status"] == "open"]

    if not open_gaps:
        return "No open gaps identified."

    # Group by severity
    critical = [g for g in open_gaps if g["severity"] == "critical"]
    high = [g for g in open_gaps if g["severity"] == "high"]
    medium = [g for g in open_gaps if g["severity"] == "medium"]
    low = [g for g in open_gaps if g["severity"] == "low"]

    lines = [
        "=" * 50,
        "  ADA SELF-ANALYSIS: IDENTIFIED GAPS",
        "=" * 50,
        f"\nTotal open gaps: {len(open_gaps)}",
        f"  Critical: {len(critical)} | High: {len(high)} | Medium: {len(medium)} | Low: {len(low)}",
        ""
    ]

    if critical:
        lines.append("CRITICAL:")
        for g in critical:
            lines.append(f"  [{g['id']}] {g['description']}")
            if g.get("suggested_fix"):
                lines.append(f"      Fix: {g['suggested_fix']}")

    if high:
        lines.append("\nHIGH PRIORITY:")
        for g in high:
            lines.append(f"  [{g['id']}] {g['description']}")
            if g.get("suggested_fix"):
                lines.append(f"      Fix: {g['suggested_fix']}")

    if medium:
        lines.append("\nMEDIUM:")
        for g in medium[:5]:  # Top 5
            lines.append(f"  [{g['id']}] {g['category']}: {g['description'][:60]}")

    if low:
        lines.append(f"\nLOW: {len(low)} items (use /gaps to see all)")

    lines.append("\n" + "=" * 50)

    return "\n".join(lines)


def get_improvement_report() -> str:
    """Generate full improvement report."""
    lines = [
        "=" * 50,
        "  ADA IMPROVEMENT REPORT",
        "=" * 50,
        ""
    ]

    # Code stats
    stats = analyze_code_structure()
    lines.append("CODE STATISTICS:")
    lines.append(f"  Files: {len(stats['files'])}")
    lines.append(f"  Lines: {stats['total_lines']}")
    lines.append(f"  Functions: {stats['functions']}")
    lines.append(f"  Classes: {stats['classes']}")

    if stats.get("incomplete_functions"):
        lines.append(f"\n  Incomplete functions: {len(stats['incomplete_functions'])}")
        for f in stats["incomplete_functions"][:3]:
            lines.append(f"    - {f}")

    if stats.get("todos_in_code"):
        lines.append(f"\n  TODOs in code: {len(stats['todos_in_code'])}")

    # Gaps summary
    lines.append("\n" + "-" * 50)
    lines.append(get_gaps_summary())

    # LLM suggestions
    lines.append("\n" + "-" * 50)
    lines.append("AI SUGGESTIONS:")
    lines.append("-" * 50)
    lines.append(get_improvement_suggestions())

    return "\n".join(lines)


if __name__ == "__main__":
    print("Running Ada Self-Analysis...\n")

    # Run analysis
    results = run_full_analysis()

    print(f"Analysis complete. Found {len(results['new_gaps'])} new gaps.\n")

    # Show summary
    print(get_gaps_summary())

    # Show LLM suggestions
    print("\n" + "=" * 50)
    print("  IMPROVEMENT SUGGESTIONS")
    print("=" * 50 + "\n")
    print(get_improvement_suggestions())
