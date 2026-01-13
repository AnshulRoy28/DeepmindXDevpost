"""
NEURO-SENTINEL Pydantic Schemas

Defines the core data models for:
- Repository semantic mapping (RepoMap)
- Deployment artifacts (DeploymentPlan) 
- Self-healing fix proposals (FixProposal)
- Reasoning audit trail (ThoughtSignature)
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal
from datetime import datetime
from enum import Enum


# ============================================
# Enums
# ============================================
class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AgentState(str, Enum):
    IDLE = "IDLE"
    BREATHE = "BREATHE"           # Monitoring mode
    RAPID_PULSE = "RAPID_PULSE"   # Active reasoning
    STROBE_RED = "STROBE_RED"     # Error detected
    SUCCESS = "SUCCESS"           # Fix applied successfully


class FixStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"
    FAILED = "failed"


# ============================================
# Phase A: Deep Ingestion Schemas
# ============================================
class FileMapping(BaseModel):
    """Mapping of a single file in the repository."""
    path: str = Field(..., description="Relative path from repo root")
    language: str = Field(..., description="Detected programming language")
    size_bytes: int = Field(..., description="File size in bytes")
    purpose: Optional[str] = Field(None, description="AI-inferred purpose of the file")


class DependencyInfo(BaseModel):
    """Detected dependency information."""
    name: str
    version: Optional[str] = None
    source: str = Field(..., description="e.g., requirements.txt, package.json")


class RepoMap(BaseModel):
    """
    Semantic Repository Mapping - the 'Mental Map' of the codebase.
    Generated during Phase A: Deep Ingestion.
    """
    project_name: str = Field(..., description="Detected project name")
    primary_language: str = Field(..., description="Main programming language")
    framework: Optional[str] = Field(None, description="Detected framework (e.g., FastAPI, Express, Django)")
    entry_point: str = Field(..., description="Main entry file (e.g., main.py, index.js)")
    dependency_file: str = Field(..., description="Primary dependency file path")
    
    # Dependency analysis
    dependencies: List[DependencyInfo] = Field(default_factory=list)
    
    # File structure
    file_mappings: List[FileMapping] = Field(default_factory=list)
    total_files: int = Field(0, description="Total number of files analyzed")
    total_tokens: int = Field(0, description="Estimated token count for context")
    
    # Logic flow analysis
    logic_flow: Dict[str, str] = Field(
        default_factory=dict,
        description="Key modules and their responsibilities"
    )
    
    # Environment requirements
    detected_env_vars: List[str] = Field(
        default_factory=list,
        description="Environment variables referenced in code"
    )
    detected_ports: List[int] = Field(
        default_factory=list,
        description="Ports explicitly used in the application"
    )


class UserGuidelines(BaseModel):
    """Parsed deployment guidelines from deployment_guidelines.md"""
    port: Optional[int] = Field(None, description="Required port")
    cloud_provider: str = Field("gcp", description="Target cloud provider")
    region: Optional[str] = Field(None, description="Deployment region")
    database_type: Optional[str] = Field(None, description="Required database type")
    min_instances: int = Field(0, description="Minimum instances for autoscaling")
    max_instances: int = Field(10, description="Maximum instances for autoscaling")
    memory_limit: str = Field("512Mi", description="Container memory limit")
    cpu_limit: str = Field("1", description="Container CPU limit")
    custom_constraints: List[str] = Field(default_factory=list, description="Additional user constraints")


# ============================================
# Phase B: Sovereign Deployment Schemas
# ============================================
class ThoughtSignature(BaseModel):
    """
    Reasoning audit trail - prevents 'Logic Drift' in multi-step operations.
    Each significant action is signed for traceability.
    """
    id: str = Field(..., description="Unique signature ID (e.g., SIG-A1B2)")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    reasoning_step: str = Field(..., description="What the agent reasoned about")
    action_taken: str = Field(..., description="What action was performed")
    verification_method: str = Field(..., description="How the action was verified")
    risk_level: RiskLevel = Field(RiskLevel.LOW)
    context_tokens_used: int = Field(0, description="Tokens used in this reasoning step")


class DockerfileSpec(BaseModel):
    """Generated Dockerfile specification."""
    base_image: str = Field(..., description="Base Docker image")
    build_stage: str = Field(..., description="Multi-stage build content")
    runtime_stage: str = Field(..., description="Runtime stage content")
    full_content: str = Field(..., description="Complete Dockerfile content")
    optimizations_applied: List[str] = Field(default_factory=list)


class TerraformSpec(BaseModel):
    """Generated Terraform configuration."""
    provider_config: str = Field(..., description="GCP provider configuration")
    cloud_run_config: str = Field(..., description="Cloud Run service definition")
    iam_config: str = Field(..., description="IAM roles and service account")
    secrets_config: str = Field(..., description="Secret Manager configuration")
    full_content: str = Field(..., description="Complete Terraform HCL")


class SecretRequirement(BaseModel):
    """A secret detected as required by the application."""
    name: str = Field(..., description="Secret/env var name (e.g., DATABASE_URL)")
    source_file: str = Field(..., description="File where it was detected")
    source_line: int = Field(..., description="Line number where detected")
    is_critical: bool = Field(True, description="Whether app will fail without it")
    suggested_source: Optional[str] = Field(None, description="Where to obtain this secret")


class DeploymentPlan(BaseModel):
    """
    Complete deployment plan output from Phase B: Sovereign Deployment.
    """
    # Generated artifacts
    dockerfile: DockerfileSpec
    terraform: TerraformSpec
    
    # Requirements
    secrets_required: List[SecretRequirement] = Field(default_factory=list)
    secrets_missing: List[str] = Field(default_factory=list)
    
    # Deployment metadata
    estimated_monthly_cost_usd: float = Field(0.0)
    deployment_region: str = Field("us-central1")
    service_url_pattern: str = Field(..., description="Expected Cloud Run URL pattern")
    
    # Reasoning trail
    thought_signatures: List[ThoughtSignature] = Field(default_factory=list)


# ============================================
# Phase C: Self-Healing / Fix Proposal Schemas
# ============================================
class AssistModeMetadata(BaseModel):
    """
    Educational metadata for Assist Mode - makes fixes understandable for interns.
    """
    what_this_does: str = Field(..., description="Plain-English explanation of the fix")
    why_its_needed: str = Field(..., description="Context from the codebase analysis")
    potential_implications: List[str] = Field(
        default_factory=list,
        description="Side effects, risks, and what could go wrong"
    )
    learn_more_links: List[str] = Field(
        default_factory=list,
        description="URLs to relevant documentation"
    )


class CodePatch(BaseModel):
    """A single code change in diff format."""
    file_path: str = Field(..., description="Relative path to the file")
    start_line: int = Field(..., description="Starting line number")
    end_line: int = Field(..., description="Ending line number")
    original_content: str = Field(..., description="Original code")
    patched_content: str = Field(..., description="Fixed code")
    diff: str = Field(..., description="Unified diff format")


class FixProposal(BaseModel):
    """
    Human-in-the-Loop fix proposal from Phase C: Self-Healing Loop.
    Presented to user for approval before application.
    """
    id: str = Field(..., description="Unique fix proposal ID")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Error context
    error_type: str = Field(..., description="Type of error (e.g., TypeError, ConnectionError)")
    error_message: str = Field(..., description="Original error message")
    stack_trace: str = Field(..., description="Full stack trace")
    affected_file: str = Field(..., description="Primary file with the issue")
    affected_line: int = Field(..., description="Line number of the error")
    
    # Diagnosis
    diagnosis: str = Field(..., description="AI-generated root cause analysis")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in the fix (0-1)")
    risk_level: RiskLevel = Field(RiskLevel.LOW)
    
    # Suggested fixes
    patches: List[CodePatch] = Field(default_factory=list)
    alternative_fixes: List[str] = Field(
        default_factory=list,
        description="Other possible approaches"
    )
    
    # Assist Mode content
    assist_mode: AssistModeMetadata
    
    # Status tracking
    status: FixStatus = Field(FixStatus.PENDING)
    reviewed_by: Optional[str] = Field(None, description="User who reviewed")
    reviewed_at: Optional[datetime] = Field(None)
    rejection_reason: Optional[str] = Field(None)
    
    # Reasoning trail
    thought_signature: ThoughtSignature


# ============================================
# Real-time Communication Schemas
# ============================================
class Thought(BaseModel):
    """A single thought in the Thought Stream."""
    id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    type: Literal["reasoning", "action", "error", "system"]
    content: str
    signature: Optional[str] = Field(None, description="ThoughtSignature ID if applicable")


class SystemState(BaseModel):
    """Complete system state for dashboard synchronization."""
    agent_state: AgentState = Field(AgentState.IDLE)
    current_task: Optional[str] = Field(None)
    token_usage: Dict[str, int] = Field(default_factory=lambda: {"current": 0, "max": 1000000})
    active_node_id: Optional[str] = Field(None)
    recent_thoughts: List[Thought] = Field(default_factory=list)
    pending_fixes: List[str] = Field(default_factory=list, description="IDs of pending FixProposals")


class InfrastructureNode(BaseModel):
    """A node in the Logic Lattice visualization."""
    id: str
    name: str
    type: Literal["service", "database", "api", "file", "secret"]
    status: Literal["healthy", "warning", "error", "processing"]
    position: tuple[float, float, float] = Field(..., description="3D position [x, y, z]")
    connections: List[str] = Field(default_factory=list, description="IDs of connected nodes")


# ============================================
# API Request/Response Schemas
# ============================================
class AnalyzeRequest(BaseModel):
    """Request to analyze a repository."""
    repo_url: str = Field(..., description="GitHub repository URL")
    branch: str = Field("main", description="Branch to analyze")
    guidelines_content: Optional[str] = Field(None, description="Optional inline guidelines")


class AnalyzeResponse(BaseModel):
    """Response from repository analysis."""
    status: Literal["success", "error"]
    repo_map: Optional[RepoMap] = None
    deployment_plan: Optional[DeploymentPlan] = None
    error_message: Optional[str] = None


class FixApprovalRequest(BaseModel):
    """Request to approve or reject a fix proposal."""
    fix_id: str
    action: Literal["approve", "reject", "modify"]
    modification: Optional[str] = Field(None, description="Modified patch if action is 'modify'")
    rejection_reason: Optional[str] = Field(None, description="Reason if action is 'reject'")


class FixApprovalResponse(BaseModel):
    """Response after processing fix approval."""
    status: Literal["applied", "rejected", "modified", "error"]
    deployment_url: Optional[str] = Field(None, description="New deployment URL if applied")
    message: str