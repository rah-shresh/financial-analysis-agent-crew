"""The startup config check must say WHICH mistake was made, not just 'it's broken'."""
 
import pytest
from dotenv import dotenv_values
 
import config
 
 
def _broken_settings(monkeypatch):
    s = config.Settings()
    monkeypatch.setattr(s, "mongodb_uri", "")
    monkeypatch.setattr(s, "jwt_secret", "")
    return s
 
 
def test_missing_env_file_is_explained(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "_ENV_PATH", tmp_path / ".env")
    with pytest.raises(RuntimeError) as err:
        _broken_settings(monkeypatch).validate()
    assert "No .env file exists at" in str(err.value) and "MONGODB_URI" in str(err.value)
 
 
def test_notepad_txt_extension_is_detected(monkeypatch, tmp_path):
    (tmp_path / ".env.txt").write_text("JWT_SECRET=x")
    monkeypatch.setattr(config, "_ENV_PATH", tmp_path / ".env")
    with pytest.raises(RuntimeError) as err:
        _broken_settings(monkeypatch).validate()
    assert "rename it to exactly '.env'" in str(err.value)
 
 
def test_existing_but_incomplete_env_file_is_explained(monkeypatch, tmp_path):
    (tmp_path / ".env").write_text("SOMETHING_ELSE=1\n")
    monkeypatch.setattr(config, "_ENV_PATH", tmp_path / ".env")
    with pytest.raises(RuntimeError) as err:
        _broken_settings(monkeypatch).validate()
    assert "doesn't define the value(s) above" in str(err.value)
 
 
def test_bom_at_start_of_file_does_not_corrupt_first_key(tmp_path):
    """config.py loads .env with encoding="utf-8-sig", which must read a Notepad-style BOM file correctly.
 
    Deliberately NOT asserted: that plain utf-8 would fail. python-dotenv <= 1.2.2 does
    (the BOM corrupts the first key's name); 1.2.3+ strips the BOM itself. That is
    third-party behaviour that changed between versions, so only our own guarantee is tested.
    """
    f = tmp_path / ".env"
    f.write_bytes(b"\xef\xbb\xbfMONGODB_URI=mongodb://example\nJWT_SECRET=abc\n")   # what Notepad can produce
    values = dotenv_values(f, encoding="utf-8-sig")
    assert values["MONGODB_URI"] == "mongodb://example"
    assert values["JWT_SECRET"] == "abc"
 
 
def test_config_really_loads_the_env_file_with_utf8_sig():
    """Guard the actual line in config.py, so nobody 'simplifies' it away and brings the old-version bug back."""
    import inspect
    assert 'encoding="utf-8-sig"' in inspect.getsource(config)
 












