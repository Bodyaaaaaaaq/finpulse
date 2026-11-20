import json

from state.home_state import DEFAULT_SELECTED, HOME_KEY, HomeState, HomeStore
from tests.helpers import run


class Prefs:
    def __init__(self, data=None, broken=False):
        self.data, self.broken = data or {}, broken

    async def get(self, key):
        if self.broken:
            raise RuntimeError("недоступно")
        return self.data.get(key)

    async def set(self, key, value):
        if self.broken:
            raise RuntimeError("недоступно")
        self.data[key] = value


def test_defaults_match_design():
    assert HomeState().selected == ["currency:USD", "currency:EUR", "crypto:BTC", "crypto:ETH", "metal:gold"]


def test_toggle_adds_and_removes():
    state = HomeState()
    assert state.toggle("currency:GBP") is True and state.is_selected("currency:GBP")
    assert state.toggle("currency:GBP") is False and not state.is_selected("currency:GBP")
    assert state.selected == DEFAULT_SELECTED  # типовий список не змінився


def test_save_and_load_roundtrip():
    prefs = Prefs()
    first = HomeState()
    run(first.load(HomeStore(prefs)))
    first.toggle("crypto:SOL")
    run(first.save())
    assert json.loads(prefs.data[HOME_KEY]) == first.selected
    second = HomeState()
    run(second.load(HomeStore(prefs)))
    assert second.selected == first.selected


def test_load_ignores_garbage_and_broken_storage():
    for prefs in (Prefs({HOME_KEY: "не json"}), Prefs({HOME_KEY: json.dumps({"a": 1})}),
                  Prefs({HOME_KEY: json.dumps([1, 2])}), Prefs(broken=True), Prefs()):
        state = HomeState()
        run(state.load(HomeStore(prefs)))
        assert state.selected == DEFAULT_SELECTED


def test_save_without_store_and_with_broken_store_does_not_raise():
    run(HomeState().save())
    state = HomeState()
    run(state.load(HomeStore(Prefs(broken=True))))
    run(state.save())


def test_empty_selection_is_remembered():
    prefs = Prefs()
    state = HomeState()
    run(state.load(HomeStore(prefs)))
    for key in list(state.selected):
        state.toggle(key)
    run(state.save())
    again = HomeState()
    run(again.load(HomeStore(prefs)))
    assert again.selected == []
