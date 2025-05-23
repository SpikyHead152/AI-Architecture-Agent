from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class TextPromptRequest(BaseModel):
    prompt: str = Field(..., example="I want to build an architecture for a social media app with live streaming.")

class ArchitectureComponent(BaseModel):
    id: str = Field(..., example="component_001")
    name: str = Field(..., example="User Service")
    type: str = Field(..., example="Microservice") # e.g., Microservice, Database, Frontend, API Gateway
    technology: Optional[str] = Field(None, example="Python, FastAPI, PostgreSQL")
    description: Optional[str] = Field(None, example="Handles user authentication and profile management.")
    properties: Optional[Dict[str, Any]] = Field(None, example={"version": "1.2", "replicas": 3})

class ArchitectureConnection(BaseModel):
    id: str = Field(..., example="conn_001")
    source_component_id: str = Field(..., example="component_001")
    target_component_id: str = Field(..., example="component_002")
    protocol: Optional[str] = Field(None, example="HTTPS/REST")
    description: Optional[str] = Field(None, example="Fetches user data for feed generation.")
    properties: Optional[Dict[str, Any]] = Field(None, example={"retries": 3, "timeout_ms": 500})

class ArchitectureDiagram(BaseModel):
    diagram_id: str = Field(..., example="arch_diag_001")
    name: str = Field(..., example="Social Media App Architecture")
    description: Optional[str] = Field(None, example="Initial architecture design for the social media platform.")
    components: List[ArchitectureComponent] = []
    connections: List[ArchitectureConnection] = []
    metadata: Optional[Dict[str, Any]] = Field(None, example={"version": "1.0", "author": "AI Agent"})

# For saving, we might just use the ArchitectureDiagram model itself.
# class SaveArchitectureRequest(ArchitectureDiagram):
#     pass

class ApiResponse(BaseModel):
    message: str
    data: Optional[Any] = None
    success: bool = True

class DeveloperBuildRequest(BaseModel):
    architecture_id: str = Field(..., example="arch_diag_001")
    specific_requirements: Optional[Dict[str, Any]] = Field(None, example={"platform": "Android", "language": "Kotlin"})

class TesterGenerateRequest(BaseModel):
    architecture_id: Optional[str] = Field(None, example="arch_diag_001")
    build_id: Optional[str] = Field(None, example="build_001") # If tests are generated after a build
    test_scope: Optional[str] = Field("basic", example="basic, regression, security")
