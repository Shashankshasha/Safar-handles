import json

from safar_agent.storage.history import recent_visual_notes


def test_recent_visual_notes_reads_and_filters_empty(tmp_path, monkeypatch):
    history_path = tmp_path / "history.json"
    history_path.write_text(
        json.dumps(
            [
                {"visual_note": "comic panel, orange"},
                {"visual_note": None},
                {},
                {"visual_note": "diorama, blue"},
            ]
        )
    )
    monkeypatch.setattr("safar_agent.storage.history.HISTORY_PATH", history_path)

    notes = recent_visual_notes()

    assert notes == ["comic panel, orange", "diorama, blue"]


def test_recent_visual_notes_empty_when_no_history(tmp_path, monkeypatch):
    monkeypatch.setattr("safar_agent.storage.history.HISTORY_PATH", tmp_path / "missing.json")
    assert recent_visual_notes() == []
