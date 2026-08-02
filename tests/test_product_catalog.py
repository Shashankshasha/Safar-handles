from safar_agent.content.product_catalog import load_catalog


def test_loads_five_weekday_fragrances_plus_weekend_spotlight():
    catalog = load_catalog()
    assert len(catalog.weekday_fragrances) == 5
    assert set(catalog.weekday_fragrances.keys()) == {0, 1, 2, 3, 4}
    assert catalog.weekend_spotlight.id == "diamond-bottle-hero"


def test_fragrance_for_weekday_rotates_monday_to_friday():
    catalog = load_catalog()
    monday_fragrance = catalog.fragrance_for_weekday(0)
    friday_fragrance = catalog.fragrance_for_weekday(4)
    assert monday_fragrance.id != friday_fragrance.id


def test_weekend_falls_back_to_spotlight():
    catalog = load_catalog()
    saturday = catalog.fragrance_for_weekday(5)
    sunday = catalog.fragrance_for_weekday(6)
    assert saturday.id == sunday.id == catalog.weekend_spotlight.id


def test_all_fragrances_returns_six_products():
    catalog = load_catalog()
    ids = {f.id for f in catalog.all_fragrances()}
    assert len(ids) == 6
