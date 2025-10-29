import pytest
import os
import json
import shutil
from fastapi.testclient import TestClient
from io import BytesIO

# Adjust the import path according to your project structure
# This assumes your 'app' directory is at architecture_agent_project/app
# and your tests are in architecture_agent_project/tests
# To make this work, Python needs to know about the 'app' directory.
# One common way is to ensure your project root (architecture_agent_project) is in PYTHONPATH
# or to use a conftest.py to adjust sys.path, or install the app as a package.
# For simplicity in this environment, we might need to adjust sys.path here if direct import fails.
import sys
# Add the project root to sys.path to allow importing 'app'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.main import app, UPLOADS_DIR, SAVED_ARCHITECTURES_DIR
from app.models import ArchitectureDiagram, ArchitectureComponent, ArchitectureConnection

@pytest.fixture(scope="module")
def client():
    # Ensure test directories exist and are clean before tests run
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    os.makedirs(SAVED_ARCHITECTURES_DIR, exist_ok=True)
    
    # Clean up any old files before starting
    for d in [UPLOADS_DIR, SAVED_ARCHITECTURES_DIR]:
        for item in os.listdir(d):
            item_path = os.path.join(d, item)
            if os.path.isfile(item_path):
                os.unlink(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)

    with TestClient(app) as c:
        yield c
    
    # Clean up after all tests in the module are done
    # for d in [UPLOADS_DIR, SAVED_ARCHITECTURES_DIR]:
    #     if os.path.exists(d): # Check if exists, as they might be removed by tests
    #         shutil.rmtree(d, ignore_errors=True)


def test_read_root(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Architecture Agent API"}

def test_generate_architecture_basic(client: TestClient):
    payload = {"prompt": "Create a simple android app with a backend api and a database."}
    response = client.post("/api/v1/architecture/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "diagram_id" in data
    assert "components" in data
    assert "connections" in data
    assert len(data["components"]) > 0 # Expect some components
    # Check for specific components based on prompt
    component_names = [comp["name"] for comp in data["components"]]
    assert "Android Client" in component_names
    assert "API Gateway" in component_names
    assert "Primary Database" in component_names

def test_generate_architecture_empty_prompt(client: TestClient):
    payload = {"prompt": ""} # Empty prompt
    response = client.post("/api/v1/architecture/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "diagram_id" in data
    # Expect default component if prompt is empty or unspecific
    assert any(comp["name"] == "Default Application Core" for comp in data["components"])


def test_upload_architecture_diagram(client: TestClient):
    # Create a dummy file content
    dummy_file_content = b"This is a dummy diagram file."
    file_to_upload = ("test_diagram.txt", BytesIO(dummy_file_content), "text/plain")

    response = client.post("/api/v1/architecture/upload", files={"file": file_to_upload})
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "file_id" in data["data"]
    assert data["data"]["original_filename"] == "test_diagram.txt"
    
    # Check if file exists in upload directory
    uploaded_file_path = os.path.join(UPLOADS_DIR, data["data"]["file_id"])
    assert os.path.exists(uploaded_file_path)
    
    # Clean up the created file
    if os.path.exists(uploaded_file_path):
        os.remove(uploaded_file_path)

def test_save_architecture(client: TestClient):
    test_diagram_id = f"test_arch_{os.urandom(4).hex()}"
    architecture_data = {
        "diagram_id": test_diagram_id,
        "name": "Test Save Architecture",
        "components": [
            {"id": "comp1", "name": "Test Component", "type": "TestType"}
        ],
        "connections": []
    }
    response = client.post("/api/v1/architecture/save", json=architecture_data)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["diagram_id"] == test_diagram_id
    
    # Check if file exists
    saved_file_path = os.path.join(SAVED_ARCHITECTURES_DIR, f"{test_diagram_id}.json")
    assert os.path.exists(saved_file_path)
    
    # Verify content (optional, but good)
    with open(saved_file_path, "r") as f:
        saved_data = json.load(f)
        assert saved_data["name"] == "Test Save Architecture"

    # Clean up
    if os.path.exists(saved_file_path):
        os.remove(saved_file_path)

def test_get_architecture_found(client: TestClient):
    # First, save an architecture to retrieve
    arch_id = f"get_test_arch_{os.urandom(4).hex()}"
    architecture_data = ArchitectureDiagram(
        diagram_id=arch_id,
        name="Test Get Architecture",
        components=[ArchitectureComponent(id="c1", name="Comp 1", type="Service")],
        connections=[]
    )
    # Manually save it for the test
    file_path = os.path.join(SAVED_ARCHITECTURES_DIR, f"{arch_id}.json")
    with open(file_path, "w") as f:
        f.write(architecture_data.model_dump_json(indent=2))

    response = client.get(f"/api/v1/architecture/{arch_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["diagram_id"] == arch_id
    assert data["name"] == "Test Get Architecture"

    # Clean up
    if os.path.exists(file_path):
        os.remove(file_path)

def test_get_architecture_not_found(client: TestClient):
    non_existent_id = "arch_id_does_not_exist_12345"
    response = client.get(f"/api/v1/architecture/{non_existent_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == f"Architecture with ID '{non_existent_id}' not found."

# Basic tests for stub endpoints
def test_developer_build_stub(client: TestClient):
    payload = {"architecture_id": "some_arch_id", "specific_requirements": {"platform": "iOS"}}
    response = client.post("/api/v1/developer/build", json=payload)
    assert response.status_code == 200 # As per current stub
    # Current stub just returns a message, might need adjustment if stub changes
    assert "Developer agent build placeholder" in response.json()["message"]
    assert response.json()["received_payload"] == payload


def test_tester_generate_tests_stub(client: TestClient):
    payload = {"architecture_id": "some_arch_id", "test_scope": "regression"}
    response = client.post("/api/v1/tester/generate-tests", json=payload)
    assert response.status_code == 200 # As per current stub
    assert "Tester agent generate tests placeholder" in response.json()["message"]
    assert response.json()["received_payload"] == payload

# Fixture for cleaning up directories after all tests in the file run
# This is an alternative to cleaning in client() fixture's exit part if preferred
# For simplicity, the client fixture already handles cleanup.
# @pytest.fixture(scope="session", autouse=True)
# def cleanup_test_directories(request):
#     # This function will be called once after all tests in the session are done.
#     def final_cleanup():
#         for d in [UPLOADS_DIR, SAVED_ARCHITECTURES_DIR]:
#             if os.path.exists(d):
#                 shutil.rmtree(d, ignore_errors=True)
#     request.addfinalizer(final_cleanup)
