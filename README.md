# Vokabeltrainer Green Line

Web-App zum Vokabellernen mit Green Line 1 (Ausgabe 2021): Phasen 1–6 wie bei Phase 6,
eigene Bildschirm-Tastatur ohne Autokorrektur, englische Aussprache und Beispielsätze.

**App:** https://oottenjitsi.github.io/vokabeltrainer/

- `index.html` – die App (Hello + Unit 1 sind eingebaut)
- `decks/` – Decks zum Importieren (.txt für die App, .apkg für Anki)
- `werkzeug/` – Vokabellisten und Skripte, aus denen App und Anki-Decks gebaut werden

Der Lernstand wird im Browser gespeichert. Sicherung: „Decks & Daten“ → „Sicherung kopieren“.

## Android-App (ohne Chrome)

Download der aktuellen Version: https://github.com/oottenjitsi/vokabeltrainer/releases/latest/download/Vokabeltrainer.apk

Die App wird bei jeder Änderung im Ordner `android/` automatisch von GitHub Actions gebaut.
Sie zeigt die Seite in einer eingebauten Android-Ansicht und nutzt die Android-Sprachausgabe.
Inhalte und neue Vokabeln kommen von GitHub Pages – dafür muss die App nicht neu installiert werden.
Hinweis: `android/app/vokabeltrainer.keystore` ist ein bewusst öffentlicher Signaturschlüssel für diese Familien-App,
damit Updates über die alte Version installiert werden können.
