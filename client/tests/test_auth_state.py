from state.auth_state import AuthState


def test_new_state_is_anonymous():
    s = AuthState()
    assert not s.is_authenticated
    assert s.token is None and s.user is None
    assert s.name == "" and s.email == "" and s.points == 0


def test_set_session_and_user():
    s = AuthState()
    s.set_session("tok")
    assert s.is_authenticated and s.user is None
    s.set_user({"name": "Іван", "email": "i@x.ua", "points": 150})
    assert (s.name, s.email, s.points) == ("Іван", "i@x.ua", 150)


def test_points_survive_missing_or_null_value():
    s = AuthState()
    s.set_session("t", {"name": "A", "points": None})
    assert s.points == 0


def test_clear_resets_everything():
    s = AuthState()
    s.set_session("t", {"name": "A", "points": 5})
    s.clear()
    assert not s.is_authenticated and s.user is None and s.points == 0
