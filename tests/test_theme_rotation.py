from safar_agent.content.themes import THEMES, theme_by_id
from safar_agent.storage.history import pick_theme


def test_theme_ids_are_unique():
    ids = [t.id for t in THEMES]
    assert len(ids) == len(set(ids))


def test_theme_by_id_lookup():
    theme = theme_by_id("action-figure-diorama")
    assert theme.category == "comedy"


def test_pick_theme_avoids_excluded_ids_when_alternatives_exist():
    all_but_one = {t.id for t in THEMES[1:]}
    picked = pick_theme(exclude=all_but_one)
    assert picked.id == THEMES[0].id


def test_pick_theme_falls_back_to_full_list_when_all_excluded():
    all_ids = {t.id for t in THEMES}
    picked = pick_theme(exclude=all_ids)
    assert picked.id in all_ids
