import pytest

from src.db import initialize_database


FIXTURE_SQL = """
CREATE TABLE Artist (ArtistId INTEGER PRIMARY KEY, Name TEXT);
CREATE TABLE Album (AlbumId INTEGER PRIMARY KEY, Title TEXT, ArtistId INTEGER);
CREATE TABLE Genre (GenreId INTEGER PRIMARY KEY, Name TEXT);
CREATE TABLE MediaType (MediaTypeId INTEGER PRIMARY KEY, Name TEXT);
CREATE TABLE Track (TrackId INTEGER PRIMARY KEY, Name TEXT, AlbumId INTEGER, MediaTypeId INTEGER, GenreId INTEGER, Composer TEXT, Milliseconds INTEGER, Bytes INTEGER, UnitPrice REAL);
CREATE TABLE Customer (CustomerId INTEGER PRIMARY KEY, FirstName TEXT, LastName TEXT, Email TEXT, Phone TEXT, SupportRepId INTEGER);
CREATE TABLE Employee (EmployeeId INTEGER PRIMARY KEY, FirstName TEXT, LastName TEXT, Title TEXT, Email TEXT);
CREATE TABLE Invoice (InvoiceId INTEGER PRIMARY KEY, CustomerId INTEGER, InvoiceDate TEXT, BillingAddress TEXT, BillingCity TEXT, BillingState TEXT, BillingCountry TEXT, BillingPostalCode TEXT, Total REAL);
CREATE TABLE InvoiceLine (InvoiceLineId INTEGER PRIMARY KEY, InvoiceId INTEGER, TrackId INTEGER, UnitPrice REAL, Quantity INTEGER);
INSERT INTO Artist VALUES (1,'AC/DC'),(2,'Miles Davis'),(3,'Other Rock');
INSERT INTO Album VALUES (1,'For Those About to Rock',1),(2,'Kind of Blue',2),(3,'Rock Album',3);
INSERT INTO Genre VALUES (1,'Rock'),(2,'Jazz');
INSERT INTO MediaType VALUES (1,'MPEG audio file');
INSERT INTO Track VALUES (1,'For Those About to Rock',1,1,1,'Angus Young',343719,11170334,0.99),(2,'Blue in Green',2,1,2,'Miles Davis',337000,100,0.99),(3,'Rock Song',3,1,1,'Someone',200000,50,0.99);
INSERT INTO Employee VALUES (1,'Jane','Doe','Sales Support Agent','jane@example.test');
INSERT INTO Customer VALUES (1,'John','Smith','John.Smith@example.test','+1 (555) 123-4567',1),(2,'Amy','Lee','amy@example.test','555-111-2222',1);
INSERT INTO Invoice VALUES (10,1,'2024-01-01','1 Main','Town','','US','00001',0.99),(11,1,'2024-02-01','1 Main','Town','','US','00001',1.98);
INSERT INTO InvoiceLine VALUES (100,10,1,0.99,1),(101,11,2,0.99,2);
"""


@pytest.fixture(autouse=True)
def database():
    yield initialize_database(FIXTURE_SQL)

