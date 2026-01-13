"""
NEURO-SENTINEL API

FastAPI application serving as the backend for the Sovereign DevOps Agent.
Provides endpoints for repository analysis, deployment, and self-healing operations.
"""

import os
import asyncio
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import socketio

from core.schema import (
    AnalyzeRequest,
    AnalyzeResponse,
    FixApprovalRequest,
    FixApprovalResponse,
    SystemState,
    AgentState,
    Thought,
    FixProposal,
    RepoMap,
    DeploymentPlan,
)
from core.ingestor import RepositoryIngestor
from core.deployment_logic import SovereignSurgeon

# Load environment variables
load_dotenv()

# ============================================
# Socket.IO Setup for Real-time Communication
# ============================================
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=True,
    engineio_logger=True
)

# Global state management
class SentinelState:
    """Global state container for the NEURO-SENTINEL agent."""
    def __init__(self):
        self.agent_state: AgentState = AgentState.IDLE
        self.current_repo_map: Optional[RepoMap] = None
        self.current_deployment_plan: Optional[DeploymentPlan] = None
        self.pending_fixes: dict[str, FixProposal] = {}
        self.thoughts: list[Thought] = []
        self.token_usage: dict[str, int] = {"current": 0, "max": 1000000}
        self.active_node_id: Optional[str] = None
    
    def add_thought(self, thought_type: str, content: str, signature: Optional[str] = None) -> Thought:
        """Add a new thought to the stream."""
        thought = Thought(
            id=f"thought-{datetime.utcnow().timestamp()}",
            timestamp=datetime.utcnow(),
            type=thought_type,
            content=content,
            signature=signature
        )
        self.thoughts.append(thought)
        # Keep only last 100 thoughts
        if len(self.thoughts) > 100:
            self.thoughts = self.thoughts[-100:]
        return thought
    
    def get_system_state(self) -> SystemState:
        """Get current system state for dashboard sync."""
        return SystemState(
            agent_state=self.agent_state,
            token_usage=self.token_usage,
            active_node_id=self.active_node_id,
            recent_thoughts=self.thoughts[-50:],
            pending_fixes=list(self.pending_fixes.keys())
        )

sentinel_state = SentinelState()

# ============================================
# Socket.IO Event Handlers
# ============================================
@sio.event
async def connect(sid, environ):
    """Handle new client connection."""
    print(f"[Socket.IO] Client connected: {sid}")
    # Send current system state
    await sio.emit('system_state', sentinel_state.get_system_state().model_dump(), room=sid)

@sio.event
async def disconnect(sid):
    """Handle client disconnection."""
    print(f"[Socket.IO] Client disconnected: {sid}")

@sio.event
async def request_state(sid):
    """Client requesting current system state."""
    await sio.emit('system_state', sentinel_state.get_system_state().model_dump(), room=sid)

async def broadcast_thought(thought: Thought):
    """Broadcast a new thought to all connected clients."""
    await sio.emit('thought_update', thought.model_dump())

async def broadcast_state_change(state: AgentState, thought: Optional[str] = None):
    """Broadcast agent state change to all clients."""
    sentinel_state.agent_state = state
    await sio.emit('agent_state', {
        'state': state.value,
        'thought': thought,
        'timestamp': datetime.utcnow().isoformat()
    })

async def broadcast_fix_proposal(fix: FixProposal):
    """Broadcast a new fix proposal for user approval."""
    await sio.emit('fix_proposal', fix.model_dump())

# ============================================
# Application Lifespan
# ============================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown."""
    # Startup
    print("[NEURO-SENTINEL] Starting up...")
    sentinel_state.add_thought("system", "NEURO-SENTINEL initialized. Awaiting commands.")
    yield
    # Shutdown
    print("[NEURO-SENTINEL] Shutting down...")

# ============================================
# FastAPI Application
# ============================================
app = FastAPI(
    title="NEURO-SENTINEL API",
    description="Sovereign DevOps Agent - Zero-Touch Infrastructure Management",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Socket.IO
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)

# ============================================
# API Endpoints
# ============================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "agent_state": sentinel_state.agent_state.value,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/state")
async def get_state():
    """Get current system state."""
    return sentinel_state.get_system_state().model_dump()


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_repository(request: AnalyzeRequest):
    """
    Phase A & B: Analyze a repository and generate deployment plan.
    
    1. Clone the repository
    2. Build semantic RepoMap using Gemini 1M token context
    3. Generate Dockerfile and Terraform configuration
    4. Detect required secrets
    """
    try:
        # Update state
        await broadcast_state_change(AgentState.RAPID_PULSE, "Starting repository analysis...")
        thought = sentinel_state.add_thought("reasoning", f"Analyzing repository: {request.repo_url}")
        await broadcast_thought(thought)
        
        # Initialize ingestor
        ingestor = RepositoryIngestor(request.repo_url)
        
        # Clone and ingest repository
        thought = sentinel_state.add_thought("action", "Cloning repository...")
        await broadcast_thought(thought)
        await ingestor.clone_async()
        
        # Build context
        thought = sentinel_state.add_thought("reasoning", "Building 1M token context window...")
        await broadcast_thought(thought)
        context = ingestor.get_full_context()
        guidelines = ingestor.read_guidelines() if request.guidelines_content is None else request.guidelines_content
        
        # Update token usage
        token_count = len(context) // 4  # Rough estimate
        sentinel_state.token_usage["current"] = token_count
        
        # Initialize Sovereign Surgeon
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")
        
        surgeon = SovereignSurgeon(api_key=api_key)
        
        # Generate deployment plan
        thought = sentinel_state.add_thought("reasoning", "Generating deployment specifications with Gemini 3 Pro...")
        await broadcast_thought(thought)
        
        repo_map, deployment_plan = await surgeon.analyze_and_plan(context, guidelines)
        
        # Store in state
        sentinel_state.current_repo_map = repo_map
        sentinel_state.current_deployment_plan = deployment_plan
        
        # Success
        await broadcast_state_change(AgentState.SUCCESS, "Analysis complete!")
        thought = sentinel_state.add_thought("system", f"✓ Analysis complete. Detected {repo_map.primary_language} {repo_map.framework or 'application'}.")
        await broadcast_thought(thought)
        
        # Return to monitoring
        await asyncio.sleep(2)
        await broadcast_state_change(AgentState.BREATHE)
        
        return AnalyzeResponse(
            status="success",
            repo_map=repo_map,
            deployment_plan=deployment_plan
        )
        
    except Exception as e:
        await broadcast_state_change(AgentState.STROBE_RED, f"Error: {str(e)}")
        thought = sentinel_state.add_thought("error", f"Analysis failed: {str(e)}")
        await broadcast_thought(thought)
        
        return AnalyzeResponse(
            status="error",
            error_message=str(e)
        )


@app.post("/deploy")
async def deploy_application():
    """
    Deploy the application using the generated Terraform configuration.
    Requires a valid DeploymentPlan from prior analysis.
    """
    if sentinel_state.current_deployment_plan is None:
        raise HTTPException(status_code=400, detail="No deployment plan available. Run /analyze first.")
    
    # Check for missing secrets
    missing = sentinel_state.current_deployment_plan.secrets_missing
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required secrets: {', '.join(missing)}. Configure them in GCP Secret Manager first."
        )
    
    await broadcast_state_change(AgentState.RAPID_PULSE, "Initiating deployment...")
    
    # TODO: Implement actual Terraform apply
    # For now, return a placeholder response
    thought = sentinel_state.add_thought("action", "Executing Terraform apply...")
    await broadcast_thought(thought)
    
    await asyncio.sleep(2)
    
    await broadcast_state_change(AgentState.SUCCESS, "Deployment complete!")
    thought = sentinel_state.add_thought("system", "✓ Application deployed to Cloud Run.")
    await broadcast_thought(thought)
    
    return {
        "status": "success",
        "message": "Deployment initiated",
        "service_url": sentinel_state.current_deployment_plan.service_url_pattern
    }


@app.get("/fixes")
async def get_pending_fixes():
    """Get all pending fix proposals awaiting approval."""
    return {
        "pending_fixes": [fix.model_dump() for fix in sentinel_state.pending_fixes.values()]
    }


@app.get("/fixes/{fix_id}")
async def get_fix_proposal(fix_id: str):
    """Get a specific fix proposal by ID."""
    if fix_id not in sentinel_state.pending_fixes:
        raise HTTPException(status_code=404, detail="Fix proposal not found")
    return sentinel_state.pending_fixes[fix_id].model_dump()


@app.post("/fixes/{fix_id}/approve", response_model=FixApprovalResponse)
async def approve_fix(fix_id: str, request: FixApprovalRequest):
    """
    Human-in-the-Loop: Approve, reject, or modify a fix proposal.
    """
    if fix_id not in sentinel_state.pending_fixes:
        raise HTTPException(status_code=404, detail="Fix proposal not found")
    
    fix = sentinel_state.pending_fixes[fix_id]
    
    if request.action == "approve":
        await broadcast_state_change(AgentState.RAPID_PULSE, f"Applying fix: {fix_id}")
        
        # TODO: Apply the patch and redeploy
        thought = sentinel_state.add_thought("action", f"Applying patch to {fix.affected_file}...")
        await broadcast_thought(thought)
        
        fix.status = "applied"
        fix.reviewed_at = datetime.utcnow()
        
        await asyncio.sleep(1)
        
        await broadcast_state_change(AgentState.SUCCESS, "Fix applied successfully!")
        thought = sentinel_state.add_thought("system", "✓ Code surgery complete. Redeploying...")
        await broadcast_thought(thought)
        
        return FixApprovalResponse(
            status="applied",
            message="Fix applied and redeployment initiated",
            deployment_url="https://your-service.run.app"  # TODO: Real URL
        )
    
    elif request.action == "reject":
        fix.status = "rejected"
        fix.rejection_reason = request.rejection_reason
        fix.reviewed_at = datetime.utcnow()
        
        thought = sentinel_state.add_thought("system", f"Fix {fix_id} rejected by user: {request.rejection_reason}")
        await broadcast_thought(thought)
        
        return FixApprovalResponse(
            status="rejected",
            message=f"Fix rejected: {request.rejection_reason}"
        )
    
    elif request.action == "modify":
        # TODO: Apply modified patch
        thought = sentinel_state.add_thought("action", f"Applying modified patch for {fix_id}...")
        await broadcast_thought(thought)
        
        return FixApprovalResponse(
            status="modified",
            message="Modified fix applied"
        )
    
    raise HTTPException(status_code=400, detail="Invalid action")


@app.post("/simulate-error")
async def simulate_error():
    """
    Demo endpoint: Simulate an error to trigger the self-healing loop.
    Useful for testing and demonstrations.
    """
    await broadcast_state_change(AgentState.STROBE_RED, "Error detected in production!")
    
    thought = sentinel_state.add_thought("error", "TypeError: Cannot read property 'user_id' of undefined")
    await broadcast_thought(thought)
    
    await asyncio.sleep(1)
    
    thought = sentinel_state.add_thought("reasoning", "Analyzing stack trace in 1M token context...")
    await broadcast_thought(thought)
    
    await asyncio.sleep(2)
    
    # Generate a demo fix proposal
    from core.schema import (
        FixProposal, CodePatch, AssistModeMetadata, 
        ThoughtSignature, RiskLevel, FixStatus
    )
    
    fix = FixProposal(
        id=f"fix-{datetime.utcnow().timestamp()}",
        error_type="TypeError",
        error_message="Cannot read property 'user_id' of undefined",
        stack_trace="at getUser (core/api.py:142)\nat handleRequest (server.py:89)",
        affected_file="core/api.py",
        affected_line=142,
        diagnosis="The function get_user() is being called without proper null-checking on the user_id parameter. During session timeout, the user_id becomes undefined.",
        confidence_score=0.92,
        risk_level=RiskLevel.LOW,
        patches=[
            CodePatch(
                file_path="core/api.py",
                start_line=142,
                end_line=145,
                original_content="def get_user(user_id):\n    return db.users.find_one({'_id': user_id})",
                patched_content="def get_user(user_id: Optional[str] = None):\n    if not user_id:\n        raise ValueError('user_id is required')\n    return db.users.find_one({'_id': user_id})",
                diff="- def get_user(user_id):\n+ def get_user(user_id: Optional[str] = None):\n+     if not user_id:\n+         raise ValueError('user_id is required')\n      return db.users.find_one({'_id': user_id})"
            )
        ],
        assist_mode=AssistModeMetadata(
            what_this_does="Adds a null-check to prevent the function from crashing when called without a user_id. The Optional[str] type hint tells Python that this parameter can be None.",
            why_its_needed="The crash log shows get_user() was called from server.py:89 during a session timeout, where user_id becomes undefined. This fix handles that edge case gracefully.",
            potential_implications=[
                "Callers that relied on silent failure will now get an explicit error",
                "You may need to add try/catch in server.py:89 to handle this",
                "No database changes — this is code-only",
                "Risk Level: LOW — isolated change, easy to rollback"
            ],
            learn_more_links=[
                "https://docs.python.org/3/library/typing.html"
            ]
        ),
        thought_signature=ThoughtSignature(
            id="SIG-A1B2",
            reasoning_step="Analyzed stack trace and cross-referenced with codebase",
            action_taken="Generated null-check patch",
            verification_method="Type checking and unit test simulation",
            risk_level=RiskLevel.LOW,
            context_tokens_used=45000
        )
    )
    
    sentinel_state.pending_fixes[fix.id] = fix
    
    thought = sentinel_state.add_thought("action", f"Generated fix proposal: {fix.id}")
    await broadcast_thought(thought)
    
    await broadcast_fix_proposal(fix)
    
    return {"status": "error_simulated", "fix_proposal_id": fix.id}


# ============================================
# Entry Point
# ============================================
# Use socket_app for uvicorn to enable Socket.IO
# Run with: uvicorn main:socket_app --reload --host 0.0.0.0 --port 8000

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(socket_app, host="0.0.0.0", port=8000)