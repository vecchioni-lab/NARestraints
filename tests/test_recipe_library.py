from restraints.recipe_library import PAIR_RECIPES, recipe_for


def test_configured_recipes():
    assert recipe_for("A", "T").name == "AT"
    assert recipe_for("T", "A").name == "AT"
    assert recipe_for("G", "C").name == "GC"
    assert recipe_for("D", "T").name == "GC"
    assert recipe_for("B", "S").name == "GC"
    assert recipe_for("Z", "P").name == "GC"
    assert recipe_for("K", "X").name == "GC"
    assert recipe_for("I", "C").name == "AT"


def test_wobble_is_not_yet_supported():
    assert recipe_for("G", "T") is None
    assert recipe_for("A", "C") is None


def test_library_is_explicitly_closed():
    assert len(PAIR_RECIPES) == 7
