"""Golden anchors for the Elder Futhark corpus (spec 9.3).

Draws are random, so nothing here pins a cast: the engine's properties live in
``tests/test_runes.py`` and the corpus invariants in ``tests/content/``. What is
anchored here is the small set of static facts that are expensive to get wrong
and easy to get wrong silently. Each is transcribed from the spec rather than
read back out of the corpus, so a coordinated edit to both cannot leave the
suite merely agreeing with itself.

Two of the five exist because of the design mockup, which printed four
characters that are not Elder Futhark runes at all and dropped Dagaz entirely,
putting the modern blank stone in its place.
"""

from app.content.rune_futhark import DECK_24, DECK_25, FUTHARK, WYRD

#: The row is named acrophonically: "futhark" *is* the first six runes read in
#: order. The third letter is thorn (U+00FE), not the digraph "th" -- which is
#: exactly why the first six letters of the English word "futhark" (f u t h a r)
#: match nothing. Written as an escape so the anchor cannot be silently retyped.
FUTHORC = "fu\u00feark"

#: The first six runes by their common names, in Kylver order.
FIRST_SIX_KEYS = ("fehu", "uruz", "thurisaz", "ansuz", "raido", "kenaz")

#: spec 2.5: the eight runes whose glyph is unchanged by a 180 degree rotation,
#: and which therefore have no merkstave reading. Kylver order, as the spec
#: lists them. Eihwaz (yew) is here and Ehwaz (horse) is not -- the two names
#: differ by one letter and their geometry is opposite, so this is transcribed
#: rather than derived anywhere.
SYMMETRIC_KEYS = (
    "gebo", "hagalaz", "isa", "jera", "eihwaz", "sowilo", "ingwaz", "dagaz",
)

#: The four characters the mockup printed that are not Elder Futhark runes:
#: AESC and ING belong to the Anglo-Saxon futhorc, SIGEL LONG-BRANCH-SOL S to
#: the Danish long-branch row, and RUNIC CROSS PUNCTUATION is a word divider
#: rather than a letter. All four sit outside the 24 and must stay outside.
MOCKUP_CODEPOINTS = frozenset({0x16AB, 0x16CB, 0x16DD, 0x16ED})


def test_the_first_six_letters_spell_the_name_of_the_row() -> None:
    """Anchor 1: Kylver order, held by the six letters the futhorc is named after."""
    assert "".join(rune.transliteration for rune in FUTHARK[:6]) == FUTHORC
    assert [rune.key for rune in FUTHARK[:6]] == list(FIRST_SIX_KEYS)
    # The third letter really is thorn and not "th", which is the whole point.
    assert FUTHARK[2].transliteration == "\u00fe"
    assert len(FUTHORC) == 6


def test_the_deck_is_twenty_four_and_twenty_five_with_the_blank_stone() -> None:
    """Anchor 2: deck size, per PRD 4.4 (a card system asserts its own size)."""
    assert len(FUTHARK) == 24
    assert len(DECK_24) == 24
    assert len(DECK_25) == 25
    assert DECK_25[:24] == tuple(DECK_24)
    assert DECK_25[24] is WYRD


def test_exactly_the_eight_symmetric_runes_lack_a_reversed_reading() -> None:
    """Anchor 3: the merkstave list from spec 2.5, key for key."""
    assert {rune.key for rune in DECK_24 if not rune.reversible} == set(SYMMETRIC_KEYS)
    # They appear in Kylver order inside the deck, not merely as a set.
    in_deck_order = [rune.key for rune in DECK_24 if not rune.reversible]
    assert in_deck_order == list(SYMMETRIC_KEYS)
    assert len(SYMMETRIC_KEYS) == 8
    # The other sixteen all carry a reversed reading; none is left ambiguous.
    assert sum(1 for rune in DECK_24 if rune.reversible) == 16


def test_none_of_the_mockups_four_characters_is_in_the_deck() -> None:
    """Anchor 4: the three lookalikes and the piece of punctuation stay out."""
    codepoints = {rune.codepoint for rune in DECK_25}
    assert not (codepoints & MOCKUP_CODEPOINTS)
    # Nor do they sneak in through a glyph string rather than a codepoint.
    glyphs = {rune.glyph for rune in DECK_25}
    assert not (glyphs & {chr(code) for code in MOCKUP_CODEPOINTS})
    # Every real rune has a codepoint; only the blank stone has none.
    assert all(rune.codepoint is not None for rune in DECK_24)
    assert WYRD.codepoint is None


def test_the_last_two_orders_are_dagaz_then_othala() -> None:
    """Anchor 5: where the mockup dropped Dagaz and seated Wyrd instead.

    Dagaz is order 23 and Othala 24; the blank stone is 25 and only ever an
    addition, never a replacement. Its glyph is empty and it belongs to no aett.
    """
    assert [rune.key for rune in DECK_24 if rune.order in (23, 24)] == ["dagaz", "othala"]
    assert [rune.order for rune in DECK_24] == list(range(1, 25))
    assert (WYRD.order, WYRD.glyph, WYRD.aett) == (25, "", None)
    assert WYRD.is_wyrd is True
    assert not any(rune.is_wyrd for rune in DECK_24)
