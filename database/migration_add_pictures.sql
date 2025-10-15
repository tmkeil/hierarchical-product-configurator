-- Migration: Bilder-Unterstützung für Nodes
-- Datum: 2025-11-24
-- Fügt pictures JSONB Feld zur nodes Tabelle hinzu

-- SQLite unterstützt kein natives JSONB, aber JSON als TEXT funktioniert
ALTER TABLE nodes ADD COLUMN pictures TEXT DEFAULT '[]';

-- Kommentar: pictures speichert ein JSON-Array mit folgendem Format:
-- [
--   {
--     "url": "/uploads/node_123_20251124_103045.png",
--     "description": "Schaltplan Variante A",
--     "uploaded_at": "2025-11-24T10:30:45.123456"
--   }
-- ]
