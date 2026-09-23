"""
🤖 MCP 适配层 — Model Context Protocol Server
让任何支持 MCP 的 AI Agent（Claude / Cursor / 各类Agent）直接把合规检测当作工具调用。

两种用法:
  1) 本地 stdio（Agent 拉起进程，最常见）:
       python mcp_server.py
  2) 远程 HTTP/SSE（多Agent共享，部署后）:
       python mcp_server.py --transport streamable-http --port 8200

暴露的工具:
  - check_compliance(text, content_type, is_ai_generated, subject)
  - get_compliance_score(text, ...)
"""
import sys
import argparse
from mcp.server.fastmcp import FastMCP

from compliance_engine import analyze_content, auto_fix

mcp = FastMCP("contentguard")


@mcp.tool()
def check_compliance(
    text: str,
    content_type: str = "email",
    is_ai_generated: bool = True,
    subject: str = "",
    return_fix: bool = True,
) -> dict:
    """Validate English marketing content against FTC, EU AI Act, CAN-SPAM and GDPR.

    Args:
        text: The marketing copy / email body to validate.
        content_type: One of "email", "ad", "social", "webpage".
        is_ai_generated: Whether the content was generated/assisted by AI.
        subject: Email subject line (used to detect misleading Re:/Fwd:).
        return_fix: If true, include an auto-fixed compliant version.

    Returns:
        compliance_score (0-100), is_compliant, counts of issues,
        a list of violations with fixes, and optionally auto_fix output.
    """
    if content_type not in ("email", "ad", "social", "webpage"):
        content_type = "email"

    analysis = analyze_content(
        text,
        content_type=content_type,
        is_ai_generated=is_ai_generated,
        subject=subject or "",
    )

    result = {
        "compliance_score": analysis["compliance_score"],
        "is_compliant": analysis["is_compliant"],
        "summary": analysis["summary"],
        "counts": analysis["counts"],
        "violations": [
            {
                "rule": v["rule"],
                "severity": v["severity"],
                "category": v["category"],
                "message": v["message"],
                "fix": v["fix"],
            }
            for v in analysis["violations"]
        ],
    }

    if return_fix:
        result["auto_fix"] = auto_fix(
            text, analysis,
            is_ai_generated=is_ai_generated,
            content_type=content_type,
        )

    return result


@mcp.tool()
def get_compliance_score(
    text: str,
    content_type: str = "email",
    is_ai_generated: bool = True,
    subject: str = "",
) -> int:
    """Return just the 0-100 compliance score for quick gating decisions
    (e.g. an agent checks score before sending an email).

    Args:
        text: The marketing copy to score.
        content_type: One of "email", "ad", "social", "webpage".
        is_ai_generated: Whether AI produced/assisted the content.
        subject: Email subject line.
    """
    if content_type not in ("email", "ad", "social", "webpage"):
        content_type = "email"
    return analyze_content(
        text, content_type=content_type,
        is_ai_generated=is_ai_generated, subject=subject or "",
    )["compliance_score"]


def main():
    parser = argparse.ArgumentParser(description="ContentGuard MCP server")
    parser.add_argument("--transport", default="stdio",
                        choices=["stdio", "streamable-http", "sse"])
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8200)
    args = parser.parse_args()

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        # 远程传输，部署后供多个 Agent 通过网络调用
        mcp.settings.host = args.host
        mcp.settings.port = args.port
        mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
