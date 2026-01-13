"""
NEURO-SENTINEL Core Module

Contains the main components for the Sovereign DevOps Agent:
- schema: Pydantic models for all data structures
- ingestor: Repository ingestion and context building
- deployment_logic: Gemini integration and deployment generation
"""

from core.schema import (
    # Enums
    RiskLevel,
    AgentState,
    FixStatus,
    # Phase A schemas
    RepoMap,
    FileMapping,
    DependencyInfo,
    UserGuidelines,
    # Phase B schemas
    ThoughtSignature,
    DockerfileSpec,
    TerraformSpec,
    SecretRequirement,
    DeploymentPlan,
    # Phase C schemas
    AssistModeMetadata,
    CodePatch,
    FixProposal,
    # Real-time schemas
    Thought,
    SystemState,
    InfrastructureNode,
    # API schemas
    AnalyzeRequest,
    AnalyzeResponse,
    FixApprovalRequest,
    FixApprovalResponse,
)

from core.ingestor import RepositoryIngestor
from core.deployment_logic import SovereignSurgeon

__all__ = [
    # Classes
    "RepositoryIngestor",
    "SovereignSurgeon",
    # Enums
    "RiskLevel",
    "AgentState",
    "FixStatus",
    # Schemas
    "RepoMap",
    "FileMapping",
    "DependencyInfo",
    "UserGuidelines",
    "ThoughtSignature",
    "DockerfileSpec",
    "TerraformSpec",
    "SecretRequirement",
    "DeploymentPlan",
    "AssistModeMetadata",
    "CodePatch",
    "FixProposal",
    "Thought",
    "SystemState",
    "InfrastructureNode",
    "AnalyzeRequest",
    "AnalyzeResponse",
    "FixApprovalRequest",
    "FixApprovalResponse",
]
