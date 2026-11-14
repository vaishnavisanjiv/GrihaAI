def test_register(client):
    response = client.post(
        "/api/auth/register",
        json={"email": "newuser@example.com", "name": "New User", "password": "password123"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert "id" in data

def test_login(client, test_user):
    response = client.post(
        "/api/auth/login",
        data={"username": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_credentials(client):
    response = client.post(
        "/api/auth/login",
        data={"username": "wrong@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401

def test_get_me(client, user_token_headers):
    response = client.get("/api/auth/me", headers=user_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
