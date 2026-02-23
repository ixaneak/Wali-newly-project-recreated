#!/usr/bin/env python3
"""
Project Structure Validator

Validates that the project follows organizational standards.
Run this before commits or when reviewing AI-generated code.

Usage:
    python scripts/validate-project-structure.py
    python scripts/validate-project-structure.py --fix
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
FORBIDDEN_ROOT_FILES = [
    # Forbidden extensions in root
    '.md', '.txt', '.py', '.ps1', '.sh', '.json', '.log',
]
ALLOWED_ROOT_FILES = [
    # Allowed files in root
    'README.md', '.env.example', '.gitignore', 'LICENSE',
    'PROJECT_STRUCTURE.md', 'AGENTS.md', 'CONTRIBUTING.md',
    'Makefile', 'Dockerfile', 'docker-compose.yml',
    'k6.exe', 'query',  # Special files
]
REQUIRED_FOLDERS = [
    'docs', 'scripts', 'tests', 'data', 'logs',
    'python-services', 'infrastructure',
]
REQUIRED_DOC_INDEXES = [
    'docs/README.md',
]


def check_forbidden_root_files() -> List[Tuple[str, str]]:
    """Check for files that shouldn't be in root."""
    issues = []
    root_files = [f for f in PROJECT_ROOT.iterdir() if f.is_file()]
    
    for file_path in root_files:
        file_name = file_path.name
        
        # Skip allowed files
        if file_name in ALLOWED_ROOT_FILES:
            continue
        
        # Check extension
        if any(file_name.endswith(ext) for ext in FORBIDDEN_ROOT_FILES):
            suggested_folder = suggest_folder(file_name)
            issues.append((
                file_name,
                f"File '{file_name}' should not be in root. "
                f"Suggested location: {suggested_folder}"
            ))
    
    return issues


def suggest_folder(filename: str) -> str:
    """Suggest appropriate folder for a file."""
    if filename.endswith('.md'):
        return "docs/<category>/"
    elif filename.endswith(('.py', '.ps1', '.sh')):
        return "scripts/"
    elif filename.endswith('.json'):
        return "data/"
    elif filename.endswith('.txt'):
        return "logs/"
    elif 'test' in filename.lower():
        return "tests/"
    else:
        return " Appropriate subfolder/"


def check_duplicate_docs() -> List[Tuple[str, str]]:
    """Check for potential duplicate documentation."""
    issues = []
    docs_dir = PROJECT_ROOT / 'docs'
    
    if not docs_dir.exists():
        return issues
    
    # Find all markdown files
    md_files = list(docs_dir.rglob('*.md'))
    file_names = [f.stem.lower() for f in md_files]
    
    # Check for duplicates (simplified)
    seen = {}
    for file_path in md_files:
        stem = file_path.stem.lower()
        if stem in seen:
            issues.append((
                str(file_path),
                f"Potential duplicate: '{file_path.name}' similar to '{seen[stem]}'"
            ))
        else:
            seen[stem] = file_path.name
    
    return issues


def check_required_folders() -> List[Tuple[str, str]]:
    """Check that required folders exist."""
    issues = []
    
    for folder in REQUIRED_FOLDERS:
        folder_path = PROJECT_ROOT / folder
        if not folder_path.exists():
            issues.append((
                folder,
                f"Required folder '{folder}' is missing"
            ))
    
    return issues


def check_docs_in_readme() -> List[Tuple[str, str]]:
    """Check if docs are referenced in docs/README.md."""
    issues = []
    readme_path = PROJECT_ROOT / 'docs' / 'README.md'
    
    if not readme_path.exists():
        return issues
    
    readme_content = readme_path.read_text(encoding='utf-8')
    docs_dir = PROJECT_ROOT / 'docs'
    
    # Get all markdown files in docs (excluding README.md)
    doc_files = [
        f for f in docs_dir.rglob('*.md')
        if f.name != 'README.md'
    ]
    
    for doc_file in doc_files:
        # Check if file is referenced in README
        relative_path = doc_file.relative_to(docs_dir).as_posix()
        if relative_path not in readme_content:
            issues.append((
                str(doc_file),
                f"Doc '{doc_file.name}' not referenced in docs/README.md"
            ))
    
    return issues


def print_report(issues: List[Tuple[str, str]]) -> None:
    """Print validation report."""
    with open("validation_report.txt", "w", encoding="utf-8") as f:
        if not issues:
            msg = "Project structure validation passed!"
            print(msg)
            f.write(msg + "\n")
            return
        
        msg = "Project structure issues found:\n"
        print(msg)
        f.write(msg + "\n")
        
        categories = {
            'Root Files': [],
            'Duplicates': [],
            'Missing Folders': [],
            'Documentation': [],
            'Other': [],
        }
        
        for file, message in issues:
            if 'root' in message.lower():
                categories['Root Files'].append((file, message))
            elif 'duplicate' in message.lower():
                categories['Duplicates'].append((file, message))
            elif 'missing' in message.lower():
                categories['Missing Folders'].append((file, message))
            elif 'README' in message:
                categories['Documentation'].append((file, message))
            else:
                categories['Other'].append((file, message))
        
        for category, items in categories.items():
            if items:
                cat_msg = f"\n{category}:"
                print(cat_msg)
                f.write(cat_msg + "\n")
                for file, message in items:
                    item_msg = f"  - {message}"
                    print(item_msg)
                    f.write(item_msg + "\n")
        
        f.write(f"\n{'='*60}\n")
        f.write(f"Total issues: {len(issues)}\n")
        f.write("\nTo fix these issues:\n")
        f.write("  1. Move files to appropriate folders\n")
        f.write("  2. Remove duplicates\n")
        f.write("  3. Update docs/README.md with new documentation\n")


def main():
    """Main validation function."""
    print("Validating Wali project structure...\n")
    
    all_issues = []
    
    # Run checks
    all_issues.extend(check_forbidden_root_files())
    all_issues.extend(check_duplicate_docs())
    all_issues.extend(check_required_folders())
    all_issues.extend(check_docs_in_readme())
    
    # Print report
    print_report(all_issues)
    
    # Exit with appropriate code
    sys.exit(0 if not all_issues else 1)


if __name__ == '__main__':
    main()
