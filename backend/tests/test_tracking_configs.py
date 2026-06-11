"""Tracking-config create / bulk / duplicate / toggle."""


def _payload(prompt, platform, country):
    return {
        "prompt_id": str(prompt.id),
        "platform_id": str(platform.id),
        "country_id": str(country.id),
    }


async def test_create_tracking_config(
    client, auth_headers, test_project, test_prompt, seed_reference
):
    resp = await client.post(
        f"/api/projects/{test_project.id}/tracking-configs",
        headers=auth_headers,
        json=_payload(test_prompt, seed_reference["platform"], seed_reference["country"]),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["prompt_id"] == str(test_prompt.id)
    assert body["is_active"] is True


async def test_duplicate_tracking_config_rejected(
    client, auth_headers, test_project, test_prompt, seed_reference
):
    payload = _payload(test_prompt, seed_reference["platform"], seed_reference["country"])
    first = await client.post(
        f"/api/projects/{test_project.id}/tracking-configs",
        headers=auth_headers, json=payload,
    )
    assert first.status_code == 200, first.text
    dup = await client.post(
        f"/api/projects/{test_project.id}/tracking-configs",
        headers=auth_headers, json=payload,
    )
    assert dup.status_code == 400


async def test_bulk_create_configs(
    client, auth_headers, db_session, test_project, test_prompt, seed_reference
):
    # A second prompt so the bulk payload has two distinct scopes.
    from backend.database.models.prompt import Prompt
    prompt2 = await Prompt.create(
        db_session, project_id=test_project.id, text="second prompt"
    )
    platform, country = seed_reference["platform"], seed_reference["country"]
    resp = await client.post(
        f"/api/projects/{test_project.id}/tracking-configs/bulk",
        headers=auth_headers,
        json={"configs": [
            _payload(test_prompt, platform, country),
            _payload(prompt2, platform, country),
        ]},
    )
    assert resp.status_code == 200, resp.text
    assert len(resp.json()) == 2


async def test_toggle_config_active(
    client, auth_headers, db_session, test_project, test_prompt, seed_reference
):
    from backend.database.models.tracking_config import TrackingConfig
    cfg = await TrackingConfig.create(
        db_session, project_id=test_project.id, prompt_id=test_prompt.id,
        platform_id=seed_reference["platform"].id,
        country_id=seed_reference["country"].id,
    )
    assert cfg.is_active is True
    resp = await client.patch(
        f"/api/projects/{test_project.id}/tracking-configs/{cfg.id}/toggle",
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["is_active"] is False
