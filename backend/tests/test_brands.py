"""Brand CRUD and cross-tenant isolation."""


async def test_create_primary_brand(client, auth_headers, test_project):
    resp = await client.post(
        f"/api/projects/{test_project.id}/brands",
        headers=auth_headers,
        json={"name": "Acme", "is_primary": True, "aliases": ["acme inc"]},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["is_primary"] is True
    assert body["aliases"] == ["acme inc"]


async def test_create_competitor_brand(client, auth_headers, test_project):
    resp = await client.post(
        f"/api/projects/{test_project.id}/brands",
        headers=auth_headers,
        json={"name": "Globex", "is_primary": False},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["is_primary"] is False


async def test_list_brands_for_project(client, auth_headers, test_project, test_brand):
    resp = await client.get(
        f"/api/projects/{test_project.id}/brands", headers=auth_headers
    )
    assert resp.status_code == 200, resp.text
    assert str(test_brand.id) in [b["id"] for b in resp.json()]


async def test_brand_from_other_org_project_returns_404(
    client, other_org_headers, test_project
):
    resp = await client.get(
        f"/api/projects/{test_project.id}/brands", headers=other_org_headers
    )
    assert resp.status_code == 404
