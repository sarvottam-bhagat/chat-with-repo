import re
from typing import Dict, List

def make_all_files_content_str(repo_dict: Dict) -> str:
    """Create formatted string of all files' content"""
    return "\n".join(
        f"=== File: {path} ===\n{content}\n"
        for path, content in repo_dict.items()
    )

def make_files_prompt(repo_dict: Dict, user_query: str) -> str:
    """Generate prompt for file selection"""
    # Pre-compute the file list with newlines to avoid backslash in f-string
    file_list = '\n'.join(repo_dict.keys())
    return (
        f"Repository Structure:\n{file_list}\n\n"
        f"Question: {user_query}\n"
        "Which files are relevant to answer this? Return as Python array of file paths."
    )

def parse_arr_from_gemini_resp(text: str) -> List[str]:
    """Parse array from LLM response"""
    try:
        # Handle both quoted and unquoted filenames
        return re.findall(r"'([^']+)'|\"([^\"]+)\"|[\w\./-]+", text)
    except:
        return []

def content_str_from_dict(repo_dict: Dict, paths: List[str]) -> str:
    """Create context string from selected paths"""
    return "\n".join(
        f"🔎 {path}:\n{repo_dict.get(path, 'NOT FOUND')}\n"
        for path in paths if path in repo_dict
    )

def format_agent_response(response: str, agent_type: str) -> str:
    """Format different agent responses appropriately"""
    response = response.replace("•", "  *")  # Normalize bullet points
    
    formatters = {
        "Low-Level Design": _format_design_response,
        "Code Generation": _format_code_response,
        "Code Changes": _format_changes_response
    }
    
    return formatters.get(agent_type, lambda x: x)(response)

def _format_design_response(text: str) -> str:
    """Format LLD agent response"""
    # Extract sections using markdown headers
    sections = re.split(r'(?m)^#+\s+', text)
    formatted = []
    for sec in sections:
        if sec.strip():
            header_match = re.match(r'(\w+)(.*?)\n', sec)
            if header_match:
                header = header_match.group(1).title()
                content = sec[len(header_match.group(0)):]
                formatted.append(f"### {header}\n{content.strip()}")
    return "\n\n".join(formatted) if formatted else text

def _format_code_response(text: str) -> str:
    """Format code generation response"""
    # Extract code blocks with language specifiers
    code_blocks = re.findall(r'```(\w+)?\n(.*?)\n```', text, re.DOTALL)
    formatted = []
    
    for lang, code in code_blocks:
        formatted.append(f"```{lang}\n{code.strip()}\n```")
    
    # Add non-code explanations
    explanations = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    if explanations.strip():
        formatted.append(f"\n**Explanation**\n{explanations.strip()}")
    
    return "\n".join(formatted)

def _format_changes_response(text: str) -> str:
    """Format code changes analysis"""
    # Extract impact sections
    impacts = re.findall(
        r'(?i)(\d+\.\s*[^:]+):?\s*\n([^•]+?(?=\n\d+\.|$))', 
        text, 
        re.DOTALL
    )
    
    formatted = []
    for num, (title, content) in enumerate(impacts, 1):
        clean_title = re.sub(r'^\d+\.\s*', '', title).strip()
        formatted.append(
            f"#### {num}. {clean_title.title()}\n"
            f"{content.strip()}\n"
        )
    
    # Add diff summary if present
    diff_summary = re.search(r'```diff(.*?)```', text, re.DOTALL)
    if diff_summary:
        formatted.insert(0, f"```diff\n{diff_summary.group(1).strip()}\n```\n")
    
    return "\n".join(formatted) if formatted else text

def parse_agent_response(raw_response: str, agent_type: str) -> Dict:
    """Parse structured agent response into components"""
    if agent_type == "Code Generation":
        return {
            "files": re.findall(r'File:\s+(.+\.\w+)', raw_response),
            "code": re.findall(r'```.*?\n(.*?)\n```', raw_response, re.DOTALL),
            "explanation": re.sub(r'```.*?```', '', raw_response, flags=re.DOTALL)
        }
    elif agent_type == "Low-Level Design":
        return {
            "components": re.findall(r'Component:\s+(.+?)\n', raw_response),
            "interactions": re.findall(r'Interaction:\s+(.+?)\n', raw_response)
        }
    return {"raw": raw_response}