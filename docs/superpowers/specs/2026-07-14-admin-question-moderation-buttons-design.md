# Admin Control Buttons für Fragen-Moderation

**Datum:** 2026-07-14
**Status:** Design (zur Review)

## Ziel

Admins und Moderatoren sollen direkt auf der Fragen-Detailseite
(`/frage/q/<hash>/<slug>/`) eine Frage moderieren können, ohne den Umweg über
den Django-Adminbereich: **verstecken** (öffentlich unsichtbar, reversibel) und
**löschen**. Anlass: unnötige/Spam-Fragen sollen mit einem Klick weggeräumt
werden können.

## Scope-Entscheidung

Nur **zwei** Aktionen: Löschen + Verstecken/Einblenden. Ein „Schließen"-Button
(Frage sichtbar, aber keine neuen Antworten) wurde **bewusst verworfen** — für
den realen Bedarf („unnötige Frage weg") genügen Löschen und Verstecken. Damit
entfällt auch das ursprünglich angedachte neue `locked`-Feld inkl. Migration.

## Zielgruppe / Berechtigung

Buttons sind sichtbar und nutzbar für **Admins (`is_staff`) UND Badge-Moderatoren
(`can_edit_questions`)**.

Dafür eine gebündelte Berechtigungsmethode auf dem Profil, damit Template-Gate
und View-Check identisch sind:

```python
# mathefragen/apps/user/models.py  (nahe is_moderator, ~Zeile 410)
def can_moderate(self):
    return self.user.is_staff or self.is_moderator()
```

- Template-Gate: `{% if request.user.is_authenticated and request.user.profile.can_moderate %}`
- View: Inline-Re-Check `request.user.profile.can_moderate()` (gleiches Muster wie
  das bestehende `delete_question`, `views.py:373-380`).

## Views (`mathefragen/apps/question/views.py`)

Alle folgen dem bestehenden Muster: `@login_required` + Inline-`can_moderate()`-
Re-Check + Redirect zurück zur Frage.

1. **Löschen — bestehendes `delete_question` erweitern** (`views.py:369-390`).
   Autorisierung von `is_moderator` auf `can_moderate()` erweitern:
   ```python
   elif request.user.profile.can_moderate():
       delete_allowed = True
   ```
   Rest unverändert (Soft-Delete via `question.delete()`, Redirect Startseite mit
   `?deleted=1`).

2. **`toggle_question_visibility(request, question_id)` — neu.**
   ```python
   @login_required
   def toggle_question_visibility(request, question_id):
       question = Question.objects.get(id=question_id)
       if request.user.profile.can_moderate():
           question.is_active = not question.is_active
           question.save()
       return redirect(question.get_absolute_url())
   ```
   Setzt **nur** `is_active` — bewusst **nicht** `make_inactive()` verwenden, da
   dessen Owner-Mail („…scheint Unstimmigkeiten zu enthalten und wurde gemeldet",
   `models.py:365-381`) für eine Admin-Aktion inhaltlich falsch wäre.

## URLs (`mathefragen/apps/question/urls.py`)

```python
path('moderate/<int:question_id>/visibility/', toggle_question_visibility, name='toggle_question_visibility'),
```

Delete-Route existiert bereits (`delete/<int:question_id>/d/`).

## Template — Moderations-Panel (`mathefragen/templates/question/question_content.html`)

Neuer, optisch abgesetzter Block, gegated auf `can_moderate`, platziert im
Aktions-Bereich unter Titel/Vote (nahe der bestehenden Aktions-Leiste
`question_content.html:60-95`). Wichtig: dieser Bereich liegt **außerhalb** der
`{% if question.is_active %}`-Blöcke — dadurch bleibt das Panel auch bei einer
versteckten Frage sichtbar, sodass Moderatoren sie wieder einblenden können.

```django
{% if request.user.is_authenticated and request.user.profile.can_moderate %}
    <div class="mod-control-panel mt-1 mb-3">
        <small class="text-muted mr-2">Moderation</small>
        <a href="{% url 'toggle_question_visibility' question.id %}"
           class="btn btn-sm btn-outline-secondary mr-1">
            {% if question.is_active %}Verstecken{% else %}Einblenden{% endif %}
        </a>
        <a href="{% url 'delete_question' question.id %}"
           class="btn btn-sm btn-outline-danger"
           onclick="return confirm('Diese Frage wirklich löschen?');">
            Löschen
        </a>
    </div>
{% endif %}
```

- Verstecken-Label wechselt je nach `is_active`.
- **Löschen** rot + JS-`confirm()` (destruktiv). Verstecken ohne Confirm (sofort,
  reversibel).
- Styling an bestehende Bootstrap-Button-Klassen der Seite angelehnt; finale
  CSS-Feinheiten im Plan.

## Semantik / bekannte Grenzen

- **Verstecken (`is_active=False`)** entspricht exakt dem bestehenden Report-Hide
  (`make_inactive`): Frage verschwindet aus Feeds/Listen (die filtern `is_active`),
  Antworten + Formular werden ausgeblendet, der Fragetext bleibt bei direktem
  URL-Aufruf im `readonly_content`-Stil sichtbar. Kein hartes 404 für die
  Öffentlichkeit — das wäre zusätzlicher Scope und weicht vom bestehenden
  Verhalten ab. Reversibel über „Einblenden".
- **Löschen** ist ein Soft-Delete (`soft_deleted=True`, `closed=True`). Eine
  Wiederherstellung ist nur über den Django-Adminbereich möglich (kein
  Undo-Button auf der Seite).
- **Security-Hinweis (GET vs. POST):** Die neuen/erweiterten Endpoints folgen dem
  bestehenden Muster GET-Link ohne CSRF-Token (wie `delete_question`,
  `delete_answer`). Sauberer wären POST-Forms mit CSRF-Token; das wäre jedoch ein
  Bruch mit dem restlichen Code und wird hier bewusst zurückgestellt (konsistent
  statt korrekt). Kann in einem Folge-Schritt für alle Moderations-Endpoints
  gemeinsam auf POST umgestellt werden.

## Tests (`mathefragen/apps/question/tests*`)

- `can_moderate()`: `is_staff` → True, Badge-Moderator → True, normaler User → False.
- `toggle_question_visibility`: Moderator schaltet `is_active` um; normaler User
  bewirkt keine Änderung.
- `delete_question`: `is_staff`-Admin ohne Badge darf jetzt löschen (erweiterte
  Autorisierung).
- Template/Integration: Panel rendert nur für `can_moderate`.

## Betroffene Dateien (Zusammenfassung)

| Datei | Änderung |
|---|---|
| `mathefragen/apps/user/models.py` | `Profile.can_moderate()` |
| `mathefragen/apps/question/views.py` | 1 neue View + `delete_question`-Gate erweitern |
| `mathefragen/apps/question/urls.py` | 1 neue Route |
| `mathefragen/templates/question/question_content.html` | Moderations-Panel |
| `mathefragen/apps/question/tests*` | neue Tests |

## Nicht im Scope (YAGNI)

- „Schließen"-Button / `locked`-Feld.
- Undo/Restore-Button auf der Seite (Wiederherstellung via Django-Admin).
- Hartes 404 für versteckte Fragen.
- Umstellung aller Moderations-Endpoints auf POST/CSRF.
- Moderations-Log / Audit-Trail.
- Bulk-Aktionen.
