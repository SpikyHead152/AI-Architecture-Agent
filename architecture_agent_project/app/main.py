import uuid
import shutil
import os
import json # Added
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import ValidationError # Added
from .models import TextPromptRequest, ArchitectureDiagram, ArchitectureComponent, ArchitectureConnection, ApiResponse

UPLOADS_DIR = "uploaded_architectures"
os.makedirs(UPLOADS_DIR, exist_ok=True)

SAVED_ARCHITECTURES_DIR = "saved_architectures" # Added
os.makedirs(SAVED_ARCHITECTURES_DIR, exist_ok=True) # Added

app = FastAPI(
    title="Architecture Agent API",
    version="0.1.0",
    description='''
API for generating, managing, and retrieving software architecture diagrams.
Supports:
- Generating architecture from text prompts.
- Uploading existing architecture diagrams (as files).
- Saving and retrieving architecture data in JSON format.
- Stub endpoints for conceptual Developer and Tester Agents.
'''
)

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Architecture Agent API"}

# Placeholder for future agent endpoints
@app.post("/api/v1/architecture/generate", response_model=ArchitectureDiagram)
async def generate_architecture_endpoint(request: TextPromptRequest):
    diagram_id = f"arch_{uuid.uuid4()}"
    components = []
    connections = []
    prompt_lower = request.prompt.lower()

    # Client Components
    client_components = []
    if "android" in prompt_lower:
        comp_id = f"comp_{uuid.uuid4()}"
        components.append(ArchitectureComponent(id=comp_id, name="Android Client", type="MobileClient", technology="Android/Kotlin/Java", description="Native Android application interface."))
        client_components.append(comp_id)
    if "ios" in prompt_lower:
        comp_id = f"comp_{uuid.uuid4()}"
        components.append(ArchitectureComponent(id=comp_id, name="iOS Client", type="MobileClient", technology="iOS/Swift", description="Native iOS application interface."))
        client_components.append(comp_id)
    if "web" in prompt_lower or "browser" in prompt_lower:
        comp_id = f"comp_{uuid.uuid4()}"
        components.append(ArchitectureComponent(id=comp_id, name="Web Client", type="WebClient", technology="React/Angular/Vue", description="Browser-based web application interface."))
        client_components.append(comp_id)

    # Backend Components
    backend_services = []
    api_gateway_id = None
    if "api" in prompt_lower or "backend" in prompt_lower:
        api_gateway_id = f"comp_{uuid.uuid4()}"
        components.append(ArchitectureComponent(id=api_gateway_id, name="API Gateway", type="APIGateway", technology="e.g., Kong/NGINX/AWS API Gateway", description="Single entry point for all client requests."))
        
        user_service_id = f"comp_{uuid.uuid4()}"
        components.append(ArchitectureComponent(id=user_service_id, name="User Service", type="Microservice", technology="e.g., Python/FastAPI", description="Manages user authentication, profiles, and settings."))
        backend_services.append(user_service_id)
        connections.append(ArchitectureConnection(id=f"conn_{uuid.uuid4()}", source_component_id=api_gateway_id, target_component_id=user_service_id, protocol="HTTPS/REST", description="Routes user-related requests to User Service."))

        # Add another generic service for illustration (Product Service as per original instructions)
        product_service_id = f"comp_{uuid.uuid4()}"
        components.append(ArchitectureComponent(id=product_service_id, name="Product Service", type="Microservice", technology="e.g., Node.js/Express", description="Manages product information or another specific domain."))
        backend_services.append(product_service_id)
        connections.append(ArchitectureConnection(id=f"conn_{uuid.uuid4()}", source_component_id=api_gateway_id, target_component_id=product_service_id, protocol="HTTPS/REST", description="Routes product-related requests to Product Service."))

    # Connect Clients to API Gateway
    if api_gateway_id and client_components:
        for client_id in client_components:
            connections.append(ArchitectureConnection(id=f"conn_{uuid.uuid4()}", source_component_id=client_id, target_component_id=api_gateway_id, protocol="HTTPS", description="Client communication to backend via API Gateway."))

    # Database Component
    if "database" in prompt_lower or "storage" in prompt_lower:
        db_id = f"comp_{uuid.uuid4()}"
        components.append(ArchitectureComponent(id=db_id, name="Primary Database", type="Database", technology="e.g., PostgreSQL/MongoDB/DynamoDB", description="Persistent storage for application data."))
        if backend_services: # Connect backend services to database
            for service_id in backend_services:
                connections.append(ArchitectureConnection(id=f"conn_{uuid.uuid4()}", source_component_id=service_id, target_component_id=db_id, protocol="TCP/IP (specific to DB)", description=f"Service connection to Database."))
    
    # Fallback if no components were generated
    if not components:
        default_comp_id = f"comp_{uuid.uuid4()}"
        components.append(ArchitectureComponent(id=default_comp_id, name="Default Application Core", type="Monolith", technology="Generic", description="Basic application component generated due to lack of specific keywords."))
        # Still add DB if requested, even for the default component
        if "database" in prompt_lower or "storage" in prompt_lower:
             db_id = f"comp_{uuid.uuid4()}"
             components.append(ArchitectureComponent(id=db_id, name="Primary Database", type="Database", technology="e.g., PostgreSQL/MongoDB/DynamoDB", description="Persistent storage for application data."))
             connections.append(ArchitectureConnection(id=f"conn_{uuid.uuid4()}", source_component_id=default_comp_id, target_component_id=db_id, protocol="TCP/IP (specific to DB)", description="Default core connection to Database."))

    return ArchitectureDiagram(
        diagram_id=diagram_id,
        name=f"Generated Architecture for: {request.prompt[:50]}...",
        description="This architecture was automatically generated based on the provided prompt.",
        components=components,
        connections=connections,
        metadata={"prompt": request.prompt, "generator_version": "0.1.0"}
    )

@app.post("/api/v1/architecture/upload", response_model=ApiResponse)
async def upload_architecture_endpoint(file: UploadFile = File(...)):
    try:
        original_filename = file.filename
        file_extension = os.path.splitext(original_filename)[1]
        # Ensure the extension, if present, starts with a dot or is empty
        if file_extension and not file_extension.startswith('.'):
            file_extension = f".{file_extension}"
        elif not file_extension and original_filename and '.' in original_filename: # handle cases like "archive.tar.gz"
             # try to get the full extension
            parts = original_filename.split('.')
            if len(parts) > 1:
                file_extension = "." + ".".join(parts[1:])


        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(UPLOADS_DIR, unique_filename)

        with open(file_path, "wb") as f_out:
            shutil.copyfileobj(file.file, f_out)
        
        return ApiResponse(
            success=True,
            message=f"File '{original_filename}' uploaded successfully as '{unique_filename}'.",
            data={"file_id": unique_filename, "original_filename": original_filename, "stored_path": file_path}
        )
    except IOError as e:
        # Log the error e internally if you have logging setup
        raise HTTPException(status_code=500, detail=f"Could not save uploaded file: {e}")
    except Exception as e:
        # Log the error e
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during file upload: {e}")
    finally:
        if hasattr(file, 'file') and file.file and not file.file.closed:
            file.file.close()

@app.post("/api/v1/architecture/save", response_model=ApiResponse)
async def save_architecture_endpoint(architecture_data: ArchitectureDiagram):
    # Pydantic model ArchitectureDiagram already validates that diagram_id is present.
    # No need for: if not architecture_data.diagram_id: raise HTTPException(...)

    filename = f"{architecture_data.diagram_id}.json"
    file_path = os.path.join(SAVED_ARCHITECTURES_DIR, filename)

    try:
        with open(file_path, "w") as f_out:
            f_out.write(architecture_data.model_dump_json(indent=2))
        
        return ApiResponse(
            success=True,
            message=f"Architecture '{architecture_data.diagram_id}' saved successfully.",
            data={"diagram_id": architecture_data.diagram_id, "saved_path": file_path}
        )
    except IOError as e:
        # Log the error e (actual logging setup would be needed for this to be effective)
        # print(f"Error saving architecture: {e}") 
        raise HTTPException(status_code=500, detail=f"Could not save architecture file: {e}")
    except Exception as e:
        # Log the error e
        # print(f"Unexpected error saving architecture: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while saving architecture: {e}")

@app.get("/api/v1/architecture/{architecture_id}", response_model=ArchitectureDiagram)
async def get_architecture_endpoint(architecture_id: str):
    filename = f"{architecture_id}.json"
    file_path = os.path.join(SAVED_ARCHITECTURES_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Architecture with ID '{architecture_id}' not found.")

    try:
        with open(file_path, "r") as f_in:
            file_content = f_in.read()
            # Validate file content is not empty
            if not file_content.strip():
                 raise HTTPException(status_code=500, detail=f"Architecture file for ID '{architecture_id}' is empty.")
            architecture_model = ArchitectureDiagram.model_validate_json(file_content)
        return architecture_model
    except FileNotFoundError: # Should be caught by os.path.exists, but good for defense
        raise HTTPException(status_code=404, detail=f"Architecture file for ID '{architecture_id}' not found (race condition).")
    except json.JSONDecodeError:
        # Log the error (e.g., print or use a logging library)
        # print(f"JSONDecodeError for {architecture_id}")
        raise HTTPException(status_code=500, detail=f"Error parsing architecture file for ID '{architecture_id}'. File is not valid JSON.")
    except ValidationError as ve: # Pydantic's validation error
        # Log the error (e.g., print(ve.errors()))
        # print(f"ValidationError for {architecture_id}: {ve.errors()}")
        raise HTTPException(status_code=500, detail=f"Error validating architecture file for ID '{architecture_id}'. Invalid data structure: {ve.errors()}")
    except IOError as e:
        # Log the error e
        # print(f"IOError for {architecture_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Could not read architecture file for ID '{architecture_id}': {e}")
    except Exception as e: 
        # Log the error e
        # print(f"Unexpected error for {architecture_id}: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred when retrieving architecture for ID '{architecture_id}': {str(e)}")

@app.post("/api/v1/developer/build")
async def developer_build_endpoint(payload: dict):
    return {"message": "Developer agent build placeholder", "received_payload": payload}

@app.post("/api/v1/tester/generate-tests")
async def tester_generate_tests_endpoint(payload: dict):
    return {"message": "Tester agent generate tests placeholder", "received_payload": payload}
