import json

import pytest

from src.tools import (
    get_albums_by_artist, get_songs_by_artist, get_songs_by_genre,
    search_song_by_title, get_track_details,
    get_invoices_by_customer_sorted_by_date, get_purchased_tracks_sorted_by_price,
    get_support_rep_for_invoice, get_invoice_line_items,
)


def data(tool, **kwargs):
    return json.loads(tool.invoke(kwargs))


@pytest.mark.parametrize("artist,expected", [("AC/DC", 1), ("AC", 1), ("Miles Davis", 1)])
def test_albums_found(artist, expected):
    assert data(get_albums_by_artist, artist_name=artist)["count"] == expected


@pytest.mark.parametrize("artist", ["nobody", "No Such Artist"])
def test_albums_not_found(artist):
    assert "No albums found" in data(get_albums_by_artist, artist_name=artist)["message"]


def test_album_json():
    assert isinstance(get_albums_by_artist.invoke({"artist_name": "AC/DC"}), str)


def test_artist_songs_count_and_sample():
    result = data(get_songs_by_artist, artist_name="AC/DC")
    assert result["total_count"] == 1 and result["sample"][0]["Artist"] == "AC/DC"


def test_artist_songs_not_found():
    assert data(get_songs_by_artist, artist_name="missing")["total_count"] == 0


def test_artist_songs_fuzzy():
    assert data(get_songs_by_artist, artist_name="AC")["total_count"] == 1


def test_genre_has_artist_diversity():
    artists = {r["Artist"] for r in data(get_songs_by_genre, genre="Rock")["sample"]}
    assert len(artists) == 2


def test_genre_deterministic():
    assert get_songs_by_genre.invoke({"genre": "Rock"}) == get_songs_by_genre.invoke({"genre": "Rock"})


def test_genre_not_found():
    assert data(get_songs_by_genre, genre="No genre")["total_count"] == 0


def test_genre_fuzzy():
    assert data(get_songs_by_genre, genre="Roc")["total_count"] == 2


def test_song_title_found():
    assert data(search_song_by_title, title="Blue in") ["count"] == 1


def test_song_title_not_found():
    assert data(search_song_by_title, title="missing")["count"] == 0


def test_song_title_case_insensitive():
    assert data(search_song_by_title, title="blue in green")["count"] == 1


def test_track_complete_details():
    result = data(get_track_details, track_id="1")
    assert result["TrackId"] == 1 and result["MediaType"] and result["Genre"]


@pytest.mark.parametrize("track_id", ["abc", "0", "-2", "1 OR 1=1"])
def test_track_invalid_ids_are_json_errors(track_id):
    assert "error" in data(get_track_details, track_id=track_id)


def test_track_missing():
    assert "No track found" in data(get_track_details, track_id="999")["message"]


def test_invoices_sorted_newest_first():
    result = data(get_invoices_by_customer_sorted_by_date, customer_id="1")["results"]
    assert [r["InvoiceId"] for r in result] == [11, 10]


def test_invoices_missing_customer():
    assert data(get_invoices_by_customer_sorted_by_date, customer_id="999")["count"] == 0


@pytest.mark.parametrize("value", ["x", "-1", "1; DROP TABLE Invoice"])
def test_invoice_bad_customer_id(value):
    assert "error" in data(get_invoices_by_customer_sorted_by_date, customer_id=value)


def test_purchases_sorted_by_price():
    rows = data(get_purchased_tracks_sorted_by_price, customer_id="1")["results"]
    assert rows and rows[0]["UnitPrice"] >= rows[-1]["UnitPrice"]


def test_purchases_missing():
    assert data(get_purchased_tracks_sorted_by_price, customer_id="2")["count"] == 0


def test_support_rep_for_owned_invoice():
    assert data(get_support_rep_for_invoice, invoice_id="10", customer_id="1")["LastName"] == "Doe"


def test_support_rep_cannot_cross_customer():
    assert "No support representative" in data(get_support_rep_for_invoice, invoice_id="10", customer_id="2")["message"]


def test_line_items_for_owned_invoice():
    assert data(get_invoice_line_items, invoice_id="10", customer_id="1")["count"] == 1


def test_line_items_cannot_cross_customer():
    assert data(get_invoice_line_items, invoice_id="10", customer_id="2")["count"] == 0


@pytest.mark.parametrize("tool,args", [
    (get_albums_by_artist, {"artist_name": "AC/DC"}), (get_songs_by_artist, {"artist_name": "AC/DC"}),
    (get_songs_by_genre, {"genre": "Rock"}), (search_song_by_title, {"title": "Blue"}),
    (get_track_details, {"track_id": "1"}), (get_invoices_by_customer_sorted_by_date, {"customer_id": "1"}),
    (get_purchased_tracks_sorted_by_price, {"customer_id": "1"}),
    (get_support_rep_for_invoice, {"invoice_id": "10", "customer_id": "1"}),
    (get_invoice_line_items, {"invoice_id": "10", "customer_id": "1"}),
])
def test_every_tool_returns_valid_json(tool, args):
    json.loads(tool.invoke(args))

