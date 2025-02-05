import difflib
import re
from typing import Dict, List

class CodebaseQA:
    @staticmethod
    def generate_prompt(code: str, question: str) -> str:
        return f"""**Codebase Analysis Request**
Analyze the following codebase and answer the question:
{code[:15000]}  # Truncate to avoid token limits
---
Question: {question}
Provide a detailed answer with file references where applicable."""

class LowLevelDesignAgent:
    @staticmethod
    def generate_prompt(code: str, feature: str) -> str:
        return f"""**Low-Level Design Request**
Feature: {feature}
Analyze this code architecture:
{code[:15000]}
---
Generate design plan with:
1. Component breakdown
2. Interface definitions
3. Data flow diagram
4. Sequence diagrams
5. Error handling strategy
6. Testing approach"""

class CodeGenerationAgent:
    @staticmethod
    def generate_prompt(code: str, task: str) -> str:
        return f"""**Code Generation Request**
Task: {task}
Reference this codebase:
{code[:15000]}
---
Provide:
1. Files to modify/create (Markdown format)
2. Complete code implementation
3. Code comments
4. Test cases
5. Migration plan (if needed)"""

class CodeChangesAgent:
    @staticmethod
    def analyze_changes(current: Dict, default: Dict) -> str:
        diff = []
        for file in set(current.keys()).union(default.keys()):
            a = default.get(file, "").splitlines()
            b = current.get(file, "").splitlines()
            diff.extend(difflib.unified_diff(a, b, f'original/{file}', f'modified/{file}'))
        return f"""**Change Analysis Request**
Changed Files:
{list(current.keys())}

Code Diffs:
{"".join(diff)[:10000]}
---
Analyze impact on:
1. Existing functionality
2. API contracts
3. Data persistence
4. Security aspects
5. Performance
6. Test coverage"""