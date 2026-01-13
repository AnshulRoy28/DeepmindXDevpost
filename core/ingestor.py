"""
NEURO-SENTINEL Repository Ingestor

Phase A: Deep Ingestion
- Clones GitHub repositories
- Builds semantic context for the 1M token window
- Parses deployment guidelines
"""

import os
import shutil
import asyncio
from pathlib import Path
from typing import Optional, List, Set
from datetime import datetime

import git
from git import Repo

from core.schema import RepoMap, FileMapping, DependencyInfo, UserGuidelines


class RepositoryIngestor:
    """
    Ingests a GitHub repository and builds a comprehensive context
    for Gemini's 1M token reasoning window.
    """
    
    # Default directories/files to ignore
    DEFAULT_IGNORE: Set[str] = {
        '.git',
        '__pycache__',
        'node_modules',
        'venv',
        '.venv',
        'env',
        '.env',
        '.idea',
        '.vscode',
        'dist',
        'build',
        '.next',
        'coverage',
        '.pytest_cache',
        '.mypy_cache',
        '*.pyc',
        '*.pyo',
        '*.egg-info',
        '.DS_Store',
        'Thumbs.db',
    }
    
    # File extensions to include
    CODE_EXTENSIONS: Set[str] = {
        '.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.go', '.rs',
        '.rb', '.php', '.c', '.cpp', '.h', '.hpp', '.cs', '.swift',
        '.kt', '.scala', '.vue', '.svelte', '.html', '.css', '.scss',
        '.sass', '.less', '.sql', '.sh', '.bash', '.zsh', '.ps1',
        '.yaml', '.yml', '.json', '.toml', '.ini', '.cfg', '.conf',
        '.md', '.rst', '.txt', '.dockerfile', '.tf', '.hcl',
    }
    
    # Dependency files for different languages
    DEPENDENCY_FILES: dict[str, str] = {
        'requirements.txt': 'python',
        'Pipfile': 'python',
        'pyproject.toml': 'python',
        'setup.py': 'python',
        'package.json': 'javascript',
        'yarn.lock': 'javascript',
        'pnpm-lock.yaml': 'javascript',
        'go.mod': 'go',
        'Cargo.toml': 'rust',
        'Gemfile': 'ruby',
        'pom.xml': 'java',
        'build.gradle': 'java',
        'composer.json': 'php',
    }
    
    # Entry point patterns for different languages
    ENTRY_POINTS: dict[str, List[str]] = {
        'python': ['main.py', 'app.py', 'run.py', 'server.py', '__main__.py', 'manage.py', 'wsgi.py'],
        'javascript': ['index.js', 'main.js', 'app.js', 'server.js', 'index.ts', 'main.ts'],
        'go': ['main.go', 'cmd/main.go'],
        'rust': ['main.rs', 'lib.rs'],
        'java': ['Main.java', 'Application.java'],
    }
    
    def __init__(self, repo_url: str, workspace_dir: str = "./workspace"):
        """
        Initialize the repository ingestor.
        
        Args:
            repo_url: GitHub repository URL
            workspace_dir: Local directory for cloning
        """
        self.repo_url = repo_url
        self.workspace_dir = Path(workspace_dir)
        self.repo_name = self._extract_repo_name(repo_url)
        self.repo_path = self.workspace_dir / self.repo_name
        self._repo: Optional[Repo] = None
        self._context_cache: Optional[str] = None
        
    def _extract_repo_name(self, url: str) -> str:
        """Extract repository name from URL."""
        # Handle both HTTPS and SSH URLs
        if url.endswith('.git'):
            url = url[:-4]
        return url.split('/')[-1]
    
    def clone(self) -> Path:
        """
        Clone the repository synchronously.
        
        Returns:
            Path to the cloned repository
        """
        # Clean existing directory if present
        if self.repo_path.exists():
            shutil.rmtree(self.repo_path)
        
        # Ensure workspace exists
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"[Ingestor] Cloning {self.repo_url} to {self.repo_path}")
        self._repo = Repo.clone_from(self.repo_url, self.repo_path)
        print(f"[Ingestor] Clone complete")
        
        return self.repo_path
    
    async def clone_async(self) -> Path:
        """Clone the repository asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.clone)
    
    def _should_ignore(self, path: Path) -> bool:
        """Check if a path should be ignored."""
        name = path.name
        
        # Check direct matches
        if name in self.DEFAULT_IGNORE:
            return True
        
        # Check patterns (e.g., *.pyc)
        for pattern in self.DEFAULT_IGNORE:
            if pattern.startswith('*') and name.endswith(pattern[1:]):
                return True
        
        return False
    
    def _is_code_file(self, path: Path) -> bool:
        """Check if a file is a code file."""
        suffix = path.suffix.lower()
        name = path.name.lower()
        
        # Check extension
        if suffix in self.CODE_EXTENSIONS:
            return True
        
        # Check special files without extensions
        if name in {'dockerfile', 'makefile', 'rakefile', 'gemfile', 'procfile'}:
            return True
        
        return False
    
    def _detect_language(self, path: Path) -> str:
        """Detect programming language from file extension."""
        suffix = path.suffix.lower()
        
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.jsx': 'javascript',
            '.java': 'java',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php',
            '.c': 'c',
            '.cpp': 'cpp',
            '.cs': 'csharp',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.vue': 'vue',
            '.svelte': 'svelte',
            '.html': 'html',
            '.css': 'css',
            '.sql': 'sql',
            '.sh': 'shell',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.json': 'json',
            '.tf': 'terraform',
            '.hcl': 'hcl',
            '.md': 'markdown',
        }
        
        return language_map.get(suffix, 'unknown')
    
    def get_full_context(self) -> str:
        """
        Concatenate the entire codebase into a single string for Gemini.
        Uses caching to avoid re-reading files.
        
        Returns:
            Concatenated codebase as a string
        """
        if self._context_cache is not None:
            return self._context_cache
        
        if not self.repo_path.exists():
            raise ValueError("Repository not cloned. Call clone() first.")
        
        context_parts: List[str] = []
        
        for root, dirs, files in os.walk(self.repo_path):
            root_path = Path(root)
            
            # Filter out ignored directories (in-place modification)
            dirs[:] = [d for d in dirs if not self._should_ignore(root_path / d)]
            
            for file_name in files:
                file_path = root_path / file_name
                
                # Skip ignored files
                if self._should_ignore(file_path):
                    continue
                
                # Only include code files
                if not self._is_code_file(file_path):
                    continue
                
                # Read and append file content
                try:
                    relative_path = file_path.relative_to(self.repo_path)
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        context_parts.append(
                            f"--- FILE: {relative_path} ---\n"
                            f"{content}\n"
                            f"--- END FILE: {relative_path} ---\n"
                        )
                except Exception as e:
                    print(f"[Ingestor] Warning: Could not read {file_path}: {e}")
                    continue
        
        self._context_cache = "\n".join(context_parts)
        return self._context_cache
    
    def read_guidelines(self) -> str:
        """
        Read the deployment_guidelines.md file if it exists.
        
        Returns:
            Guidelines content or default message
        """
        guidelines_path = self.repo_path / 'deployment_guidelines.md'
        
        if guidelines_path.exists():
            with open(guidelines_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        # Check alternative names
        alternatives = ['DEPLOYMENT.md', 'deployment.md', 'DEPLOY.md', 'deploy.md']
        for alt in alternatives:
            alt_path = self.repo_path / alt
            if alt_path.exists():
                with open(alt_path, 'r', encoding='utf-8') as f:
                    return f.read()
        
        return "No specific deployment guidelines provided. Use sensible defaults."
    
    def build_repo_map(self) -> RepoMap:
        """
        Build a semantic map of the repository.
        
        Returns:
            RepoMap with project metadata
        """
        if not self.repo_path.exists():
            raise ValueError("Repository not cloned. Call clone() first.")
        
        file_mappings: List[FileMapping] = []
        language_counts: dict[str, int] = {}
        detected_deps: List[DependencyInfo] = []
        detected_env_vars: Set[str] = set()
        detected_ports: Set[int] = set()
        dependency_file: Optional[str] = None
        primary_language: str = "unknown"
        entry_point: str = "unknown"
        framework: Optional[str] = None
        
        for root, dirs, files in os.walk(self.repo_path):
            root_path = Path(root)
            dirs[:] = [d for d in dirs if not self._should_ignore(root_path / d)]
            
            for file_name in files:
                file_path = root_path / file_name
                
                if self._should_ignore(file_path) or not self._is_code_file(file_path):
                    continue
                
                try:
                    relative_path = str(file_path.relative_to(self.repo_path))
                    language = self._detect_language(file_path)
                    size = file_path.stat().st_size
                    
                    # Count languages
                    language_counts[language] = language_counts.get(language, 0) + 1
                    
                    file_mappings.append(FileMapping(
                        path=relative_path,
                        language=language,
                        size_bytes=size
                    ))
                    
                    # Check for dependency files
                    if file_name in self.DEPENDENCY_FILES:
                        dependency_file = relative_path
                        detected_deps.extend(self._parse_dependencies(file_path, file_name))
                    
                    # Scan for env vars and ports
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        detected_env_vars.update(self._find_env_vars(content))
                        detected_ports.update(self._find_ports(content))
                        
                        # Detect framework
                        if framework is None:
                            framework = self._detect_framework(content, language)
                    
                except Exception as e:
                    print(f"[Ingestor] Warning: Could not process {file_path}: {e}")
        
        # Determine primary language
        if language_counts:
            primary_language = max(language_counts, key=language_counts.get)
        
        # Find entry point
        entry_point = self._find_entry_point(primary_language)
        
        # Estimate token count
        context = self.get_full_context()
        token_estimate = len(context) // 4  # Rough estimate: 4 chars per token
        
        return RepoMap(
            project_name=self.repo_name,
            primary_language=primary_language,
            framework=framework,
            entry_point=entry_point,
            dependency_file=dependency_file or "unknown",
            dependencies=detected_deps,
            file_mappings=file_mappings,
            total_files=len(file_mappings),
            total_tokens=token_estimate,
            detected_env_vars=list(detected_env_vars),
            detected_ports=list(detected_ports)
        )
    
    def _parse_dependencies(self, path: Path, filename: str) -> List[DependencyInfo]:
        """Parse dependencies from a dependency file."""
        deps: List[DependencyInfo] = []
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if filename == 'requirements.txt':
                for line in content.splitlines():
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.split('==')
                        name = parts[0].split('>=')[0].split('<=')[0].split('[')[0]
                        version = parts[1] if len(parts) > 1 else None
                        deps.append(DependencyInfo(name=name, version=version, source=filename))
            
            elif filename == 'package.json':
                import json
                data = json.loads(content)
                for dep_type in ['dependencies', 'devDependencies']:
                    if dep_type in data:
                        for name, version in data[dep_type].items():
                            deps.append(DependencyInfo(name=name, version=version, source=filename))
        
        except Exception as e:
            print(f"[Ingestor] Warning: Could not parse {filename}: {e}")
        
        return deps
    
    def _find_env_vars(self, content: str) -> Set[str]:
        """Find environment variable references in code."""
        import re
        
        env_vars: Set[str] = set()
        
        # Python: os.environ['VAR'], os.getenv('VAR')
        patterns = [
            r"os\.environ\[[\'\"](\w+)[\'\"]\]",
            r"os\.getenv\([\'\"](\w+)[\'\"]",
            r"process\.env\.(\w+)",  # JavaScript
            r"ENV\[[\'\"](\w+)[\'\"]\]",  # Ruby
            r"getenv\([\'\"](\w+)[\'\"]",  # PHP
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            env_vars.update(matches)
        
        return env_vars
    
    def _find_ports(self, content: str) -> Set[int]:
        """Find port numbers in code."""
        import re
        
        ports: Set[int] = set()
        
        # Common port patterns
        patterns = [
            r"port\s*[=:]\s*(\d{4,5})",
            r"PORT\s*[=:]\s*(\d{4,5})",
            r"listen\((\d{4,5})",
            r":(\d{4,5})[/\"\']",
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                port = int(match)
                if 1024 <= port <= 65535:  # Valid port range
                    ports.add(port)
        
        return ports
    
    def _detect_framework(self, content: str, language: str) -> Optional[str]:
        """Detect the framework used in the code."""
        framework_patterns = {
            'FastAPI': [r'from fastapi import', r'FastAPI\('],
            'Flask': [r'from flask import', r'Flask\(__name__\)'],
            'Django': [r'from django', r'DJANGO_SETTINGS_MODULE'],
            'Express': [r'require\([\'"]express[\'"]\)', r'from [\'"]express[\'"]'],
            'Next.js': [r'from [\'"]next', r'next/'],
            'React': [r'from [\'"]react[\'"]', r'import React'],
            'Vue': [r'from [\'"]vue[\'"]', r'createApp'],
            'Spring': [r'@SpringBootApplication', r'springframework'],
            'Gin': [r'github.com/gin-gonic/gin'],
            'Actix': [r'actix_web', r'actix-web'],
        }
        
        import re
        for framework, patterns in framework_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content):
                    return framework
        
        return None
    
    def _find_entry_point(self, language: str) -> str:
        """Find the entry point file for the detected language."""
        entry_points = self.ENTRY_POINTS.get(language, [])
        
        for entry in entry_points:
            entry_path = self.repo_path / entry
            if entry_path.exists():
                return entry
        
        # Fallback: look for any main file
        for file in self.repo_path.iterdir():
            if file.is_file() and 'main' in file.name.lower():
                return file.name
        
        return "unknown"
    
    def cleanup(self):
        """Remove the cloned repository."""
        if self.repo_path.exists():
            shutil.rmtree(self.repo_path)
            print(f"[Ingestor] Cleaned up {self.repo_path}")