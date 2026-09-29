# Call_Center_Assistant Test Results

**Run date:** 2026-09-29
**Command:** `python -m pytest tests/ -v --tb=short`
**Runtime:** Python 3.12.14; pytest 9.1.1
**Result:** 60 passed in 0.89s
**Collected test cases:** 60

The tests use an isolated in-memory Chinook-shaped SQLite fixture. They do not require an API key or network access. Every case in the final run is listed below.

## tests/test_database_memory.py

- `test_database_health_check` — **PASSED**
- `test_parameterized_query` — **PASSED**
- `test_normalize_phone_with_country_code` — **PASSED**
- `test_normalize_phone_without_country_code` — **PASSED**
- `test_verify_customer_numeric_id` — **PASSED**
- `test_verify_customer_email_case_insensitive` — **PASSED**
- `test_verify_customer_phone_formatting` — **PASSED**
- `test_verify_customer_not_found` — **PASSED**
- `test_preferences_are_per_customer` — **PASSED**
- `test_preferences_merge_without_removal` — **PASSED**
- `test_questions_are_not_preferences` — **PASSED**
- `test_explicit_preferences_are_extracted` — **PASSED**
- `test_no_preference_does_not_change_existing` — **PASSED**
- `test_catalog_query_does_not_require_verification` — **PASSED**
- `test_off_topic_query_is_rejected_directly` — **PASSED**
- `test_invoice_query_without_identity_requests_verification` — **PASSED**
- `test_verified_invoice_query_uses_state_customer_id` — **PASSED**
- `test_mixed_query_calls_both_specialists` — **PASSED**

## tests/test_tools.py

- `test_albums_found[AC/DC-1]` — **PASSED**
- `test_albums_found[AC-1]` — **PASSED**
- `test_albums_found[Miles Davis-1]` — **PASSED**
- `test_albums_not_found[nobody]` — **PASSED**
- `test_albums_not_found[No Such Artist]` — **PASSED**
- `test_album_json` — **PASSED**
- `test_artist_songs_count_and_sample` — **PASSED**
- `test_artist_songs_not_found` — **PASSED**
- `test_artist_songs_fuzzy` — **PASSED**
- `test_genre_has_artist_diversity` — **PASSED**
- `test_genre_deterministic` — **PASSED**
- `test_genre_not_found` — **PASSED**
- `test_genre_fuzzy` — **PASSED**
- `test_song_title_found` — **PASSED**
- `test_song_title_not_found` — **PASSED**
- `test_song_title_case_insensitive` — **PASSED**
- `test_track_complete_details` — **PASSED**
- `test_track_invalid_ids_are_json_errors[abc]` — **PASSED**
- `test_track_invalid_ids_are_json_errors[0]` — **PASSED**
- `test_track_invalid_ids_are_json_errors[-2]` — **PASSED**
- `test_track_invalid_ids_are_json_errors[1 OR 1=1]` — **PASSED**
- `test_track_missing` — **PASSED**
- `test_invoices_sorted_newest_first` — **PASSED**
- `test_invoices_missing_customer` — **PASSED**
- `test_invoice_bad_customer_id[x]` — **PASSED**
- `test_invoice_bad_customer_id[-1]` — **PASSED**
- `test_invoice_bad_customer_id[1; DROP TABLE Invoice]` — **PASSED**
- `test_purchases_sorted_by_price` — **PASSED**
- `test_purchases_missing` — **PASSED**
- `test_support_rep_for_owned_invoice` — **PASSED**
- `test_support_rep_cannot_cross_customer` — **PASSED**
- `test_line_items_for_owned_invoice` — **PASSED**
- `test_line_items_cannot_cross_customer` — **PASSED**
- `test_every_tool_returns_valid_json[tool0-args0]` — **PASSED**
- `test_every_tool_returns_valid_json[tool1-args1]` — **PASSED**
- `test_every_tool_returns_valid_json[tool2-args2]` — **PASSED**
- `test_every_tool_returns_valid_json[tool3-args3]` — **PASSED**
- `test_every_tool_returns_valid_json[tool4-args4]` — **PASSED**
- `test_every_tool_returns_valid_json[tool5-args5]` — **PASSED**
- `test_every_tool_returns_valid_json[tool6-args6]` — **PASSED**
- `test_every_tool_returns_valid_json[tool7-args7]` — **PASSED**
- `test_every_tool_returns_valid_json[tool8-args8]` — **PASSED**

## Full pytest output

```text
============================= test session starts =============================
platform win32 -- Python 3.12.14, pytest-9.1.1, pluggy-1.6.0 -- Python 3.12.14
cachedir: .pytest_cache
rootdir: <project root>
plugins: anyio-4.15.1, langsmith-0.14.1
collecting ... collected 60 items

tests/test_database_memory.py::test_database_health_check PASSED         [  1%]
tests/test_database_memory.py::test_parameterized_query PASSED           [  3%]
tests/test_database_memory.py::test_normalize_phone_with_country_code PASSED [  5%]
tests/test_database_memory.py::test_normalize_phone_without_country_code PASSED [  6%]
tests/test_database_memory.py::test_verify_customer_numeric_id PASSED    [  8%]
tests/test_database_memory.py::test_verify_customer_email_case_insensitive PASSED [ 10%]
tests/test_database_memory.py::test_verify_customer_phone_formatting PASSED [ 11%]
tests/test_database_memory.py::test_verify_customer_not_found PASSED     [ 13%]
tests/test_database_memory.py::test_preferences_are_per_customer PASSED  [ 15%]
tests/test_database_memory.py::test_preferences_merge_without_removal PASSED [ 16%]
tests/test_database_memory.py::test_questions_are_not_preferences PASSED [ 18%]
tests/test_database_memory.py::test_explicit_preferences_are_extracted PASSED [ 20%]
tests/test_database_memory.py::test_no_preference_does_not_change_existing PASSED [ 21%]
tests/test_database_memory.py::test_catalog_query_does_not_require_verification PASSED [ 23%]
tests/test_database_memory.py::test_off_topic_query_is_rejected_directly PASSED [ 25%]
tests/test_database_memory.py::test_invoice_query_without_identity_requests_verification PASSED [ 26%]
tests/test_database_memory.py::test_verified_invoice_query_uses_state_customer_id PASSED [ 28%]
tests/test_database_memory.py::test_mixed_query_calls_both_specialists PASSED [ 30%]
tests/test_tools.py::test_albums_found[AC/DC-1] PASSED                   [ 31%]
tests/test_tools.py::test_albums_found[AC-1] PASSED                      [ 33%]
tests/test_tools.py::test_albums_found[Miles Davis-1] PASSED             [ 35%]
tests/test_tools.py::test_albums_not_found[nobody] PASSED                [ 36%]
tests/test_tools.py::test_albums_not_found[No Such Artist] PASSED        [ 38%]
tests/test_tools.py::test_album_json PASSED                              [ 40%]
tests/test_tools.py::test_artist_songs_count_and_sample PASSED           [ 41%]
tests/test_tools.py::test_artist_songs_not_found PASSED                  [ 43%]
tests/test_tools.py::test_artist_songs_fuzzy PASSED                      [ 45%]
tests/test_tools.py::test_genre_has_artist_diversity PASSED              [ 46%]
tests/test_tools.py::test_genre_deterministic PASSED                     [ 48%]
tests/test_tools.py::test_genre_not_found PASSED                         [ 50%]
tests/test_tools.py::test_genre_fuzzy PASSED                             [ 51%]
tests/test_tools.py::test_song_title_found PASSED                        [ 53%]
tests/test_tools.py::test_song_title_not_found PASSED                    [ 55%]
tests/test_tools.py::test_song_title_case_insensitive PASSED             [ 56%]
tests/test_tools.py::test_track_complete_details PASSED                  [ 58%]
tests/test_tools.py::test_track_invalid_ids_are_json_errors[abc] PASSED  [ 60%]
tests/test_tools.py::test_track_invalid_ids_are_json_errors[0] PASSED    [ 61%]
tests/test_tools.py::test_track_invalid_ids_are_json_errors[-2] PASSED   [ 63%]
tests/test_tools.py::test_track_invalid_ids_are_json_errors[1 OR 1=1] PASSED [ 65%]
tests/test_tools.py::test_track_missing PASSED                           [ 66%]
tests/test_tools.py::test_invoices_sorted_newest_first PASSED            [ 68%]
tests/test_tools.py::test_invoices_missing_customer PASSED               [ 70%]
tests/test_tools.py::test_invoice_bad_customer_id[x] PASSED              [ 71%]
tests/test_tools.py::test_invoice_bad_customer_id[-1] PASSED             [ 73%]
tests/test_tools.py::test_invoice_bad_customer_id[1; DROP TABLE Invoice] PASSED [ 75%]
tests/test_tools.py::test_purchases_sorted_by_price PASSED               [ 76%]
tests/test_tools.py::test_purchases_missing PASSED                       [ 78%]
tests/test_tools.py::test_support_rep_for_owned_invoice PASSED           [ 80%]
tests/test_tools.py::test_support_rep_cannot_cross_customer PASSED       [ 81%]
tests/test_tools.py::test_line_items_for_owned_invoice PASSED            [ 83%]
tests/test_tools.py::test_line_items_cannot_cross_customer PASSED        [ 85%]
tests/test_tools.py::test_every_tool_returns_valid_json[tool0-args0] PASSED [ 86%]
tests/test_tools.py::test_every_tool_returns_valid_json[tool1-args1] PASSED [ 88%]
tests/test_tools.py::test_every_tool_returns_valid_json[tool2-args2] PASSED [ 90%]
tests/test_tools.py::test_every_tool_returns_valid_json[tool3-args3] PASSED [ 91%]
tests/test_tools.py::test_every_tool_returns_valid_json[tool4-args4] PASSED [ 93%]
tests/test_tools.py::test_every_tool_returns_valid_json[tool5-args5] PASSED [ 95%]
tests/test_tools.py::test_every_tool_returns_valid_json[tool6-args6] PASSED [ 96%]
tests/test_tools.py::test_every_tool_returns_valid_json[tool7-args7] PASSED [ 98%]
tests/test_tools.py::test_every_tool_returns_valid_json[tool8-args8] PASSED [100%]

============================= 60 passed in 0.87s ==============================
```


