import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Kotaemon FastAPI server is running"}

# You can add more tests here for chat and file routes
# For example:
# def test_upload_file():
#     with open("test_file.txt", "rb") as f:
#         response = client.post("/files/upload", files={"file": ("test_file.txt", f, "text/plain")})
#     assert response.status_code == 200
#     assert response.json()["status"] == "success"
#     # Add assertions for file_id and file_name if needed

# def test_post_message():
#     response = client.post(
#         "/chat/message",
#         json={
#             "message": "Hello, what is Kotaemon?",
#             "history": [],
#             "reasoning_type": "simple",
#         },
#     )
#     assert response.status_code == 200
#     # Since it's a streaming response, we'd need a more complex assertion
#     # For now, just check for successful connection and some content
#     for chunk in response.iter_content():
#         assert chunk is not None
