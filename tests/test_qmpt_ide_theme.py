from code.qmpt_ide.theme import DARK_THEME


def test_dark_theme_keys_present() -> None:
    required = {"bg", "panel", "accent", "fg", "border"}
    assert required.issubset(DARK_THEME.keys())


def test_dark_theme_hex_values() -> None:
    for value in DARK_THEME.values():
        assert isinstance(value, str)
        assert value.startswith("#")
        # hex color should have 7 characters like #rrggbb
        assert len(value) in {7, 4}
