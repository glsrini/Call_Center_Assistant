import json

from src.db import health_check, normalize_phone, query
from src.memory import PreferenceStore, extract_explicit_preferences
from src.tools import verify_customer
from src.agents import create_graph


def test_database_health_check(database):
    assert health_check(database)


def test_parameterized_query(database):
    assert query("SELECT Name FROM Artist WHERE Name=:name", {"name": "AC/DC"}, database)[0]["Name"] == "AC/DC"


def test_normalize_phone_with_country_code():
    assert normalize_phone("+1 (555) 123-4567") == "+15551234567"


def test_normalize_phone_without_country_code():
    assert normalize_phone("555-123-4567") == "5551234567"


def test_verify_customer_numeric_id(database):
    assert verify_customer("1", database) == 1


def test_verify_customer_email_case_insensitive(database):
    assert verify_customer("JOHN.SMITH@EXAMPLE.TEST", database) == 1


def test_verify_customer_phone_formatting(database):
    assert verify_customer("1-555-123-4567", database) == 1


def test_verify_customer_not_found(database):
    assert verify_customer("nobody@example.test", database) is None


def test_preferences_are_per_customer():
    store = PreferenceStore()
    store.merge(1, ["jazz"])
    assert store.get(2)["music_preferences"] == []


def test_preferences_merge_without_removal():
    store = PreferenceStore()
    store.merge(1, ["rock", "AC/DC"])
    profile = store.merge(1, ["jazz", "rock"])
    assert profile["music_preferences"] == ["rock", "AC/DC", "jazz"]


def test_questions_are_not_preferences():
    assert extract_explicit_preferences("Do you have jazz music?") == []


def test_explicit_preferences_are_extracted():
    assert extract_explicit_preferences("I love jazz and AC/DC.") == ["jazz", "AC/DC"]


def test_no_preference_does_not_change_existing():
    store = PreferenceStore()
    store.merge(1, ["rock"])
    before = store.get(1)
    assert store.merge(1, extract_explicit_preferences("Show me rock albums")) == before


def test_catalog_query_does_not_require_verification(database):
    result = create_graph().invoke({"message": "What rock songs do you have?"})
    assert result["response"] and not result.get("pending_verification")


def test_off_topic_query_is_rejected_directly(database):
    result = create_graph().invoke({"message": "What is the weather today?"})
    assert "digital music store" in result["response"]
    assert result["calls"] == []


def test_invoice_query_without_identity_requests_verification(database):
    result = create_graph().invoke({"message": "Show me my invoices"})
    assert result["pending_verification"]
    assert "verify your identity" in result["response"]


def test_verified_invoice_query_uses_state_customer_id(database):
    result = create_graph().invoke({"message": "Show me my invoices", "customer_id": 1})
    assert "2024-02-01" in result["response"]


def test_mixed_query_calls_both_specialists(database):
    result = create_graph().invoke({"message": "Show my invoices and what jazz songs are available", "customer_id": 1})
    assert result["calls"] == ["invoice", "music"]
    assert "2024-02-01" in result["response"] and "Blue in Green" in result["response"]

