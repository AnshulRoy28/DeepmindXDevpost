"""
NEURO-SENTINEL Sovereign Surgeon

Phase B: Sovereign Deployment
- Uses Gemini 3 Pro with 1M token context
- Generates optimized Dockerfiles
- Creates Terraform IaC for GCP Cloud Run
- Detects required secrets

Phase C: Self-Healing Loop
- Analyzes errors with full codebase context
- Generates fix proposals with Assist Mode metadata
"""

import os
import json
import asyncio
from typing import Optional, Tuple
from datetime import datetime

import google.generativeai as genai

from core.schema import (
    RepoMap,
    DeploymentPlan,
    DockerfileSpec,
    TerraformSpec,
    SecretRequirement,
    ThoughtSignature,
    FixProposal,
    CodePatch,
    AssistModeMetadata,
    RiskLevel,
    FileMapping,
    DependencyInfo,
)


class SovereignSurgeon:
    """
    The brain of NEURO-SENTINEL.
    Uses Gemini 3 Pro's 1M token context to reason about entire codebases.
    """
    
    # Model configuration
    MODEL_NAME = "gemini-2.5-pro-preview-06-05"  # Use available Gemini model
    
    def __init__(self, api_key: str):
        """
        Initialize the Sovereign Surgeon.
        
        Args:
            api_key: Google AI API key
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            self.MODEL_NAME,
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
            }
        )
        self.thought_signatures: list[ThoughtSignature] = []
    
    def _create_signature(
        self,
        reasoning: str,
        action: str,
        verification: str,
        risk: RiskLevel = RiskLevel.LOW,
        tokens: int = 0
    ) -> ThoughtSignature:
        """Create a new thought signature for audit trail."""
        sig_id = f"SIG-{datetime.utcnow().strftime('%H%M%S')}-{len(self.thought_signatures):03d}"
        sig = ThoughtSignature(
            id=sig_id,
            reasoning_step=reasoning,
            action_taken=action,
            verification_method=verification,
            risk_level=risk,
            context_tokens_used=tokens
        )
        self.thought_signatures.append(sig)
        return sig
    
    async def analyze_and_plan(
        self,
        codebase_context: str,
        guidelines: str
    ) -> Tuple[RepoMap, DeploymentPlan]:
        """
        Analyze codebase and generate deployment plan.
        
        Args:
            codebase_context: Full codebase as concatenated string
            guidelines: User's deployment guidelines
            
        Returns:
            Tuple of (RepoMap, DeploymentPlan)
        """
        # Create signature for this analysis
        sig = self._create_signature(
            reasoning="Analyzing codebase structure and generating deployment artifacts",
            action="Full context analysis with Gemini 3 Pro",
            verification="Schema validation of output",
            tokens=len(codebase_context) // 4
        )
        
        # Build the analysis prompt
        prompt = self._build_analysis_prompt(codebase_context, guidelines)
        
        # Call Gemini
        response = await self.model.generate_content_async(prompt)
        
        # Parse the response
        result = self._parse_analysis_response(response.text, sig)
        
        return result
    
    def _build_analysis_prompt(self, context: str, guidelines: str) -> str:
        """Build the prompt for codebase analysis."""
        return f"""ROLE: You are NEURO-SENTINEL, a Sovereign DevOps Agent with expertise in cloud infrastructure, containerization, and application deployment.

MISSION: Analyze the provided codebase and deployment guidelines to create a complete, production-ready infrastructure plan.

=== CODEBASE CONTEXT (1M Token Window) ===
{context}

=== USER DEPLOYMENT GUIDELINES ===
{guidelines}

=== REQUIRED OUTPUT ===
Respond with a valid JSON object containing two main sections: "repo_map" and "deployment_plan".

SCHEMA REQUIREMENTS:

1. repo_map:
   - project_name: string (detected project name)
   - primary_language: string (main programming language)
   - framework: string or null (e.g., "FastAPI", "Express", "Django")
   - entry_point: string (main entry file)
   - dependency_file: string (e.g., "requirements.txt", "package.json")
   - dependencies: array of {{ name: string, version: string|null, source: string }}
   - detected_env_vars: array of strings (environment variables used in code)
   - detected_ports: array of numbers (ports used in code)
   - logic_flow: object mapping module names to their responsibilities
   - total_files: number
   - total_tokens: number (estimate)

2. deployment_plan:
   - dockerfile:
     - base_image: string (e.g., "python:3.12-slim")
     - build_stage: string (multi-stage build content)
     - runtime_stage: string (final stage content)
     - full_content: string (complete Dockerfile)
     - optimizations_applied: array of strings
   
   - terraform:
     - provider_config: string (GCP provider HCL)
     - cloud_run_config: string (Cloud Run service HCL)
     - iam_config: string (Service account and IAM HCL)
     - secrets_config: string (Secret Manager HCL)
     - full_content: string (complete Terraform configuration)
   
   - secrets_required: array of:
     - name: string (e.g., "DATABASE_URL")
     - source_file: string (where detected)
     - source_line: number
     - is_critical: boolean
     - suggested_source: string or null
   
   - secrets_missing: array of strings (secrets not yet configured)
   - estimated_monthly_cost_usd: number
   - deployment_region: string (default: "us-central1")
   - service_url_pattern: string (expected Cloud Run URL)

CONSTRAINTS:
1. Dockerfile MUST use multi-stage builds for optimization
2. Terraform MUST use least-privilege IAM (only roles/run.admin, roles/secretmanager.secretAccessor, roles/artifactregistry.writer, roles/logging.viewer)
3. All secrets MUST be sourced from GCP Secret Manager, never hardcoded
4. Cloud Run MUST have autoscaling configured (min: 0, max: 10)
5. Health checks MUST be enabled

OUTPUT FORMAT: Pure JSON only, no markdown or explanation. The response must be valid JSON that can be parsed directly.
"""

    def _parse_analysis_response(
        self,
        response_text: str,
        signature: ThoughtSignature
    ) -> Tuple[RepoMap, DeploymentPlan]:
        """Parse the Gemini response into structured objects."""
        try:
            # Clean up response if needed
            text = response_text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            
            data = json.loads(text)
            
            # Parse RepoMap
            rm_data = data.get("repo_map", {})
            repo_map = RepoMap(
                project_name=rm_data.get("project_name", "unknown"),
                primary_language=rm_data.get("primary_language", "unknown"),
                framework=rm_data.get("framework"),
                entry_point=rm_data.get("entry_point", "unknown"),
                dependency_file=rm_data.get("dependency_file", "unknown"),
                dependencies=[
                    DependencyInfo(**dep) for dep in rm_data.get("dependencies", [])
                ],
                file_mappings=[
                    FileMapping(**fm) for fm in rm_data.get("file_mappings", [])
                ],
                total_files=rm_data.get("total_files", 0),
                total_tokens=rm_data.get("total_tokens", 0),
                logic_flow=rm_data.get("logic_flow", {}),
                detected_env_vars=rm_data.get("detected_env_vars", []),
                detected_ports=rm_data.get("detected_ports", [])
            )
            
            # Parse DeploymentPlan
            dp_data = data.get("deployment_plan", {})
            
            dockerfile_data = dp_data.get("dockerfile", {})
            dockerfile = DockerfileSpec(
                base_image=dockerfile_data.get("base_image", "python:3.12-slim"),
                build_stage=dockerfile_data.get("build_stage", ""),
                runtime_stage=dockerfile_data.get("runtime_stage", ""),
                full_content=dockerfile_data.get("full_content", ""),
                optimizations_applied=dockerfile_data.get("optimizations_applied", [])
            )
            
            terraform_data = dp_data.get("terraform", {})
            terraform = TerraformSpec(
                provider_config=terraform_data.get("provider_config", ""),
                cloud_run_config=terraform_data.get("cloud_run_config", ""),
                iam_config=terraform_data.get("iam_config", ""),
                secrets_config=terraform_data.get("secrets_config", ""),
                full_content=terraform_data.get("full_content", "")
            )
            
            secrets_required = [
                SecretRequirement(**sr) for sr in dp_data.get("secrets_required", [])
            ]
            
            deployment_plan = DeploymentPlan(
                dockerfile=dockerfile,
                terraform=terraform,
                secrets_required=secrets_required,
                secrets_missing=dp_data.get("secrets_missing", []),
                estimated_monthly_cost_usd=dp_data.get("estimated_monthly_cost_usd", 0.0),
                deployment_region=dp_data.get("deployment_region", "us-central1"),
                service_url_pattern=dp_data.get("service_url_pattern", "https://PROJECT.run.app"),
                thought_signatures=[signature]
            )
            
            return repo_map, deployment_plan
            
        except json.JSONDecodeError as e:
            print(f"[SovereignSurgeon] JSON parse error: {e}")
            print(f"[SovereignSurgeon] Raw response: {response_text[:500]}...")
            # Return default/empty structures
            return self._create_default_response(signature)
    
    def _create_default_response(
        self,
        signature: ThoughtSignature
    ) -> Tuple[RepoMap, DeploymentPlan]:
        """Create default response when parsing fails."""
        repo_map = RepoMap(
            project_name="unknown",
            primary_language="python",
            entry_point="main.py",
            dependency_file="requirements.txt"
        )
        
        dockerfile = DockerfileSpec(
            base_image="python:3.12-slim",
            build_stage="FROM python:3.12-slim AS builder\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install --no-cache-dir -r requirements.txt",
            runtime_stage="FROM python:3.12-slim\nWORKDIR /app\nCOPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages\nCOPY . .\nCMD [\"python\", \"main.py\"]",
            full_content="# Default Dockerfile\nFROM python:3.12-slim\nWORKDIR /app\nCOPY . .\nRUN pip install -r requirements.txt\nCMD [\"python\", \"main.py\"]"
        )
        
        terraform = TerraformSpec(
            provider_config='provider "google" {\n  project = var.project_id\n  region  = var.region\n}',
            cloud_run_config="# Cloud Run configuration pending",
            iam_config="# IAM configuration pending",
            secrets_config="# Secrets configuration pending",
            full_content="# Full Terraform pending"
        )
        
        deployment_plan = DeploymentPlan(
            dockerfile=dockerfile,
            terraform=terraform,
            service_url_pattern="https://PROJECT.run.app",
            thought_signatures=[signature]
        )
        
        return repo_map, deployment_plan
    
    async def diagnose_error(
        self,
        codebase_context: str,
        stack_trace: str,
        error_message: str,
        affected_file: str,
        affected_line: int
    ) -> FixProposal:
        """
        Diagnose an error and generate a fix proposal.
        
        Args:
            codebase_context: Full codebase as concatenated string
            stack_trace: The error stack trace
            error_message: The error message
            affected_file: File where the error occurred
            affected_line: Line number of the error
            
        Returns:
            FixProposal with HITL approval required
        """
        sig = self._create_signature(
            reasoning=f"Diagnosing error in {affected_file}:{affected_line}",
            action="Cross-referencing stack trace with codebase context",
            verification="Patch validation and type checking",
            risk=RiskLevel.MEDIUM,
            tokens=len(codebase_context) // 4
        )
        
        prompt = self._build_diagnosis_prompt(
            codebase_context, stack_trace, error_message, affected_file, affected_line
        )
        
        response = await self.model.generate_content_async(prompt)
        
        return self._parse_diagnosis_response(
            response.text, stack_trace, error_message, affected_file, affected_line, sig
        )
    
    def _build_diagnosis_prompt(
        self,
        context: str,
        stack_trace: str,
        error_message: str,
        affected_file: str,
        affected_line: int
    ) -> str:
        """Build the prompt for error diagnosis."""
        return f"""ROLE: You are NEURO-SENTINEL's Surgical Module, specializing in production error diagnosis and code remediation.

MISSION: Analyze the error in context of the full codebase and propose a minimal, safe fix.

=== CODEBASE CONTEXT ===
{context}

=== ERROR INFORMATION ===
File: {affected_file}
Line: {affected_line}
Error Message: {error_message}

Stack Trace:
{stack_trace}

=== REQUIRED OUTPUT ===
Respond with a valid JSON object containing a fix proposal.

SCHEMA:
{{
  "diagnosis": "string - root cause analysis",
  "confidence_score": number 0-1,
  "risk_level": "low" | "medium" | "high" | "critical",
  "patches": [
    {{
      "file_path": "string",
      "start_line": number,
      "end_line": number,
      "original_content": "string - exact original code",
      "patched_content": "string - fixed code",
      "diff": "string - unified diff format"
    }}
  ],
  "alternative_fixes": ["string array of other approaches"],
  "assist_mode": {{
    "what_this_does": "string - plain English explanation for interns",
    "why_its_needed": "string - context and reasoning",
    "potential_implications": ["array of side effects and risks"],
    "learn_more_links": ["array of documentation URLs"]
  }}
}}

CONSTRAINTS:
1. Propose the MINIMAL fix required
2. NEVER suggest removing entire functions/classes unless absolutely necessary
3. Include comprehensive Assist Mode metadata for learning
4. Confidence score should reflect actual certainty
5. Risk level must account for downstream effects

OUTPUT FORMAT: Pure JSON only.
"""

    def _parse_diagnosis_response(
        self,
        response_text: str,
        stack_trace: str,
        error_message: str,
        affected_file: str,
        affected_line: int,
        signature: ThoughtSignature
    ) -> FixProposal:
        """Parse the diagnosis response into a FixProposal."""
        try:
            text = response_text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            
            data = json.loads(text)
            
            patches = [
                CodePatch(
                    file_path=p.get("file_path", affected_file),
                    start_line=p.get("start_line", affected_line),
                    end_line=p.get("end_line", affected_line),
                    original_content=p.get("original_content", ""),
                    patched_content=p.get("patched_content", ""),
                    diff=p.get("diff", "")
                )
                for p in data.get("patches", [])
            ]
            
            assist_data = data.get("assist_mode", {})
            assist_mode = AssistModeMetadata(
                what_this_does=assist_data.get("what_this_does", "Applies a code fix"),
                why_its_needed=assist_data.get("why_its_needed", "To resolve the detected error"),
                potential_implications=assist_data.get("potential_implications", []),
                learn_more_links=assist_data.get("learn_more_links", [])
            )
            
            risk_str = data.get("risk_level", "low").lower()
            risk_level = RiskLevel(risk_str) if risk_str in ["low", "medium", "high", "critical"] else RiskLevel.LOW
            
            return FixProposal(
                id=f"fix-{datetime.utcnow().timestamp()}",
                error_type=error_message.split(":")[0] if ":" in error_message else "Error",
                error_message=error_message,
                stack_trace=stack_trace,
                affected_file=affected_file,
                affected_line=affected_line,
                diagnosis=data.get("diagnosis", "Analysis complete"),
                confidence_score=data.get("confidence_score", 0.8),
                risk_level=risk_level,
                patches=patches,
                alternative_fixes=data.get("alternative_fixes", []),
                assist_mode=assist_mode,
                thought_signature=signature
            )
            
        except json.JSONDecodeError as e:
            print(f"[SovereignSurgeon] Diagnosis parse error: {e}")
            # Return a default fix proposal
            return FixProposal(
                id=f"fix-{datetime.utcnow().timestamp()}",
                error_type="ParseError",
                error_message=error_message,
                stack_trace=stack_trace,
                affected_file=affected_file,
                affected_line=affected_line,
                diagnosis="Unable to parse AI response. Manual investigation required.",
                confidence_score=0.0,
                risk_level=RiskLevel.HIGH,
                patches=[],
                assist_mode=AssistModeMetadata(
                    what_this_does="Manual fix required",
                    why_its_needed="AI parsing failed",
                    potential_implications=["Requires manual debugging"],
                    learn_more_links=[]
                ),
                thought_signature=signature
            )
    
    async def generate_deployment_specs(
        self,
        repo_context: str,
        guidelines: str
    ) -> str:
        """
        Legacy method for backward compatibility.
        Generates deployment specifications as JSON string.
        """
        repo_map, deployment_plan = await self.analyze_and_plan(repo_context, guidelines)
        return json.dumps({
            "repo_map": repo_map.model_dump(),
            "deployment_plan": deployment_plan.model_dump()
        }, indent=2, default=str)