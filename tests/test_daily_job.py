import pytest

from safar_agent.scheduler.daily_job import run


def test_copy_override_requires_theme_id_in_meta():
    with pytest.raises(ValueError, match="_meta.theme_id"):
        run(publish=False, copy_override={"instagram_caption": "no meta here"})


def test_copy_override_rejects_unknown_theme_id():
    with pytest.raises(KeyError):
        run(publish=False, copy_override={"_meta": {"theme_id": "not-a-real-theme"}})
