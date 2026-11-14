def test_create_project(client, user_token_headers):
    response = client.post(
        "/api/projects/",
        headers=user_token_headers,
        json={
            "name": "Test Project",
            "description": "A test project",
            "building_type": "residential",
            "jurisdiction": "NY"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Project"
    assert "id" in data

def test_list_projects(client, user_token_headers):
    # First create one
    client.post(
        "/api/projects/",
        headers=user_token_headers,
        json={"name": "Test Project"}
    )
    
    response = client.get("/api/projects/", headers=user_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1

def test_get_project(client, user_token_headers):
    create_resp = client.post(
        "/api/projects/",
        headers=user_token_headers,
        json={"name": "Test Project 2"}
    )
    project_id = create_resp.json()["id"]
    
    response = client.get(f"/api/projects/{project_id}", headers=user_token_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Test Project 2"

def test_update_project(client, user_token_headers):
    create_resp = client.post(
        "/api/projects/",
        headers=user_token_headers,
        json={"name": "Test Project Update"}
    )
    project_id = create_resp.json()["id"]
    
    response = client.put(
        f"/api/projects/{project_id}",
        headers=user_token_headers,
        json={"name": "Updated Name"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"

def test_delete_project(client, user_token_headers):
    create_resp = client.post(
        "/api/projects/",
        headers=user_token_headers,
        json={"name": "Test Project Delete"}
    )
    project_id = create_resp.json()["id"]
    
    response = client.delete(f"/api/projects/{project_id}", headers=user_token_headers)
    assert response.status_code == 204
    
    # Verify it's deleted
    get_resp = client.get(f"/api/projects/{project_id}", headers=user_token_headers)
    assert get_resp.status_code == 404
