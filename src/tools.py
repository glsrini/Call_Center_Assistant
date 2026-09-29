"""Nine safe, JSON-string database tools for catalog and billing agents."""
from __future__ import annotations

import json
import logging
import re
from typing import Callable

from langchain_core.tools import tool

from .db import get_engine, normalize_phone, query

log = logging.getLogger(__name__)


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def _safe_int(value: str, label: str) -> int:
    if not re.fullmatch(r"\s*\d+\s*", str(value)):
        raise ValueError(f"Invalid {label}: {value}. Please provide a numeric value.")
    number = int(value)
    if number < 1:
        raise ValueError(f"Invalid {label}: {value}. Please provide a positive number.")
    return number


def _run(fn: Callable, *args) -> str:
    try:
        return _json(fn(*args))
    except ValueError as exc:
        return _json({"error": str(exc)})
    except Exception:
        log.exception("Database tool failed")
        return _json({"error": "The database lookup failed. Please try again."})


def _albums(artist: str):
    rows = query("SELECT al.AlbumId, al.Title, ar.Name AS Artist FROM Album al JOIN Artist ar ON al.ArtistId=ar.ArtistId WHERE ar.Name LIKE :name COLLATE NOCASE ORDER BY ar.Name, al.Title LIMIT 100", {"name": f"%{artist.strip()}%"})
    return {"count": len(rows), "results": rows} if rows else {"message": f"No albums found for artist: {artist}"}


@tool
def get_albums_by_artist(artist_name: str) -> str:
    """Find albums by a fuzzy artist-name match."""
    return _run(_albums, artist_name)


def _artist_tracks(artist: str):
    rows = query("SELECT t.TrackId, t.Name AS Track, al.Title AS Album, ar.Name AS Artist FROM Track t JOIN Album al ON t.AlbumId=al.AlbumId JOIN Artist ar ON al.ArtistId=ar.ArtistId WHERE ar.Name LIKE :name COLLATE NOCASE ORDER BY t.TrackId", {"name": f"%{artist.strip()}%"})
    return {"total_count": len(rows), "sample": rows[:10], "truncated": len(rows) > 10} if rows else {"message": f"No songs found for artist: {artist}", "total_count": 0, "sample": []}


@tool
def get_songs_by_artist(artist_name: str) -> str:
    """Find tracks by artist with exact total and up to ten examples."""
    return _run(_artist_tracks, artist_name)


def _genre_tracks(genre: str):
    rows = query("WITH ranked AS (SELECT t.TrackId, t.Name AS Track, ar.Name AS Artist, al.Title AS Album, g.Name AS Genre, ROW_NUMBER() OVER (PARTITION BY ar.ArtistId ORDER BY t.TrackId) AS rn FROM Track t JOIN Genre g ON t.GenreId=g.GenreId JOIN Album al ON t.AlbumId=al.AlbumId JOIN Artist ar ON al.ArtistId=ar.ArtistId WHERE g.Name LIKE :name COLLATE NOCASE) SELECT TrackId, Track, Artist, Album, Genre FROM ranked WHERE rn=1 ORDER BY TrackId LIMIT 10", {"name": f"%{genre.strip()}%"})
    count = query("SELECT COUNT(*) AS total FROM Track t JOIN Genre g ON t.GenreId=g.GenreId WHERE g.Name LIKE :name COLLATE NOCASE", {"name": f"%{genre.strip()}%"})[0]["total"]
    return {"total_count": count, "sample": rows, "truncated": count > len(rows)} if count else {"message": f"No songs found for genre: {genre}", "total_count": 0, "sample": []}


@tool
def get_songs_by_genre(genre: str) -> str:
    """Browse a deterministic sample across different artists in a genre."""
    return _run(_genre_tracks, genre)


def _title(title: str):
    rows = query("SELECT t.TrackId, t.Name AS Track, ar.Name AS Artist, al.Title AS Album, g.Name AS Genre, t.Composer, t.Milliseconds, t.Bytes, t.UnitPrice FROM Track t LEFT JOIN Album al ON t.AlbumId=al.AlbumId LEFT JOIN Artist ar ON al.ArtistId=ar.ArtistId LEFT JOIN Genre g ON t.GenreId=g.GenreId WHERE t.Name LIKE :name COLLATE NOCASE ORDER BY t.Name, t.TrackId LIMIT 20", {"name": f"%{title.strip()}%"})
    return {"count": len(rows), "results": rows, "truncated": len(rows) == 20} if rows else {"message": f"No songs found with title matching: {title}", "count": 0, "results": []}


@tool
def search_song_by_title(title: str) -> str:
    """Search for a song title using a case-insensitive substring match."""
    return _run(_title, title)


def _track(track_id: str):
    tid = _safe_int(track_id, "track ID")
    rows = query("SELECT t.TrackId, t.Name AS Track, t.AlbumId, al.Title AS Album, ar.Name AS Artist, t.MediaTypeId, mt.Name AS MediaType, t.GenreId, g.Name AS Genre, t.Composer, t.Milliseconds, t.Bytes, t.UnitPrice FROM Track t LEFT JOIN Album al ON t.AlbumId=al.AlbumId LEFT JOIN Artist ar ON al.ArtistId=ar.ArtistId LEFT JOIN Genre g ON t.GenreId=g.GenreId LEFT JOIN MediaType mt ON t.MediaTypeId=mt.MediaTypeId WHERE t.TrackId=:id", {"id": tid})
    return rows[0] if rows else {"message": f"No track found with ID: {tid}"}


@tool
def get_track_details(track_id: str) -> str:
    """Get complete catalog details for a numeric track ID."""
    return _run(_track, track_id)


def _customer_invoices(customer_id: str):
    cid = _safe_int(customer_id, "customer ID")
    rows = query("SELECT InvoiceId, CustomerId, InvoiceDate, BillingAddress, BillingCity, BillingState, BillingCountry, BillingPostalCode, Total FROM Invoice WHERE CustomerId=:cid ORDER BY InvoiceDate DESC, InvoiceId DESC", {"cid": cid})
    return {"count": len(rows), "results": rows} if rows else {"message": f"No invoices found for customer ID: {cid}", "count": 0, "results": []}


@tool
def get_invoices_by_customer_sorted_by_date(customer_id: str) -> str:
    """List a verified customer's invoices newest first."""
    return _run(_customer_invoices, customer_id)


def _purchases(customer_id: str):
    cid = _safe_int(customer_id, "customer ID")
    rows = query("SELECT i.InvoiceId, i.InvoiceDate, il.InvoiceLineId, t.TrackId, t.Name AS Track, ar.Name AS Artist, il.UnitPrice, il.Quantity FROM Invoice i JOIN InvoiceLine il ON i.InvoiceId=il.InvoiceId JOIN Track t ON il.TrackId=t.TrackId LEFT JOIN Album al ON t.AlbumId=al.AlbumId LEFT JOIN Artist ar ON al.ArtistId=ar.ArtistId WHERE i.CustomerId=:cid ORDER BY il.UnitPrice DESC, i.InvoiceDate DESC, il.InvoiceLineId", {"cid": cid})
    return {"count": len(rows), "results": rows} if rows else {"message": f"No purchased tracks found for customer ID: {cid}", "count": 0, "results": []}


@tool
def get_purchased_tracks_sorted_by_price(customer_id: str) -> str:
    """List a customer's purchased track line items from highest unit price."""
    return _run(_purchases, customer_id)


def _rep(invoice_id: str, customer_id: str):
    iid, cid = _safe_int(invoice_id, "invoice ID"), _safe_int(customer_id, "customer ID")
    rows = query("SELECT e.EmployeeId, e.FirstName, e.LastName, e.Title, e.Email, i.InvoiceId FROM Invoice i JOIN Customer c ON c.CustomerId=i.CustomerId JOIN Employee e ON e.EmployeeId=c.SupportRepId WHERE i.InvoiceId=:iid AND i.CustomerId=:cid", {"iid": iid, "cid": cid})
    return rows[0] if rows else {"message": f"No support representative found for invoice ID: {iid}"}


@tool
def get_support_rep_for_invoice(invoice_id: str, customer_id: str) -> str:
    """Find the support representative for an invoice belonging to a verified customer."""
    return _run(_rep, invoice_id, customer_id)


def _lines(invoice_id: str, customer_id: str):
    iid, cid = _safe_int(invoice_id, "invoice ID"), _safe_int(customer_id, "customer ID")
    rows = query("SELECT il.InvoiceLineId, il.InvoiceId, t.TrackId, t.Name AS Track, ar.Name AS Artist, al.Title AS Album, il.UnitPrice, il.Quantity FROM Invoice i JOIN InvoiceLine il ON il.InvoiceId=i.InvoiceId JOIN Track t ON t.TrackId=il.TrackId LEFT JOIN Album al ON t.AlbumId=al.AlbumId LEFT JOIN Artist ar ON al.ArtistId=ar.ArtistId WHERE i.InvoiceId=:iid AND i.CustomerId=:cid ORDER BY il.InvoiceLineId", {"iid": iid, "cid": cid})
    return {"invoice_id": iid, "count": len(rows), "results": rows} if rows else {"message": f"No line items found for invoice ID: {iid}", "invoice_id": iid, "count": 0, "results": []}


@tool
def get_invoice_line_items(invoice_id: str, customer_id: str) -> str:
    """Get line items for a specific invoice owned by a verified customer."""
    return _run(_lines, invoice_id, customer_id)


MUSIC_TOOLS = [get_albums_by_artist, get_songs_by_artist, get_songs_by_genre, search_song_by_title, get_track_details]
INVOICE_TOOLS = [get_invoices_by_customer_sorted_by_date, get_purchased_tracks_sorted_by_price, get_support_rep_for_invoice, get_invoice_line_items]


def verify_customer(identifier: str, engine=None) -> int | None:
    """Verify numeric ID, case-insensitive email, or normalized phone."""
    value = identifier.strip()
    if re.fullmatch(r"\d+", value):
        found = query("SELECT CustomerId FROM Customer WHERE CustomerId=:value", {"value": int(value)}, engine)
    elif "@" in value:
        found = query("SELECT CustomerId FROM Customer WHERE LOWER(Email)=LOWER(:value)", {"value": value}, engine)
    else:
        normalized = normalize_phone(value)
        if len(re.sub(r"\D", "", normalized)) < 7:
            return None
        normalized_digits = re.sub(r"\D", "", normalized)
        found = [row for row in query("SELECT CustomerId, Phone FROM Customer WHERE Phone IS NOT NULL", engine=engine) if normalize_phone(row["Phone"]) == normalized or re.sub(r"\D", "", normalize_phone(row["Phone"])) == normalized_digits]
    return int(found[0]["CustomerId"]) if found else None

