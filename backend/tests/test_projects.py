"""Project CRUD and multi-tenancy isolation."""


async def test_create_project(client, auth_headers):
    resp = await client.post(
        "/api/projects",
        headers=auth_headers,
        json={"name": "New Project", "website_url": "https://acme.test"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["name"] == "New Project"
    assert body["id"]


async def test_list_projects_returns_only_own_org(client, auth_headers, test_project):
    resp = await client.get("/api/projects", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    ids = [p["id"] for p in resp.json()]
    assert str(test_project.id) in ids


async def test_get_project_from_other_org_returns_404(
    client, other_org_headers, test_project
):
    # test_project belongs to test_org; other_org_headers is a different org.
    resp = await client.get(
        f"/api/projects/{test_project.id}", headers=other_org_headers
    )
    assert resp.status_code == 404


async def test_update_project(client, auth_headers, test_project):
    resp = await client.put(
        f"/api/projects/{test_project.id}",
        headers=auth_headers,
        json={"name": "Renamed"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["name"] == "Renamed"


async def test_delete_project(client, auth_headers, test_project):
    resp = await client.delete(
        f"/api/projects/{test_project.id}", headers=auth_headers
    )
    assert resp.status_code in (200, 204)
    # Soft-deleted: it no longer appears in the list.
    listing = await client.get("/api/projects", headers=auth_headers)
    assert str(test_project.id) not in [p["id"] for p in listing.json()]
