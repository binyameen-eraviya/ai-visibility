"""Prompt CRUD, tag attach, filtering, tenancy."""


async def test_create_prompt(client, auth_headers, test_project):
    resp = await client.post(
        f"/api/projects/{test_project.id}/prompts",
        headers=auth_headers,
        json={"text": "best project management tool"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["text"] == "best project management tool"
    assert body["tags"] == []


async def test_create_prompt_with_tags(
    client, auth_headers, db_session, test_project
):
    # Seed a tag in the same project, then create a prompt referencing it.
    from backend.database.migrations.tag import Tag as TagTable
    import uuid as _uuid
    tag = TagTable(id=_uuid.uuid4(), project_id=test_project.id, name="crm")
    db_session.add(tag)
    await db_session.commit()

    resp = await client.post(
        f"/api/projects/{test_project.id}/prompts",
        headers=auth_headers,
        json={"text": "tagged prompt", "tag_ids": [str(tag.id)]},
    )
    assert resp.status_code == 200, resp.text
    tags = resp.json()["tags"]
    assert [t["name"] for t in tags] == ["crm"]


async def test_list_prompts(client, auth_headers, test_project, test_prompt):
    resp = await client.get(
        f"/api/projects/{test_project.id}/prompts", headers=auth_headers
    )
    assert resp.status_code == 200, resp.text
    assert str(test_prompt.id) in [p["id"] for p in resp.json()]


async def test_prompt_from_other_org_returns_404(
    client, other_org_headers, test_project
):
    resp = await client.get(
        f"/api/projects/{test_project.id}/prompts", headers=other_org_headers
    )
    assert resp.status_code == 404
