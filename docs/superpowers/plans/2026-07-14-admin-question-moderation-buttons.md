# Admin Control Buttons für Fragen-Moderation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Admins und Moderatoren können eine Frage direkt auf der Detailseite verstecken/einblenden und löschen — über ein Moderations-Panel mit zwei Buttons.

**Architecture:** Eine gebündelte Berechtigungsmethode `Profile.can_moderate()` (`is_staff OR Badge-Moderator`) gated Template-Panel und View-Aktionen identisch. Verstecken toggelt `Question.is_active`; Löschen nutzt den bestehenden `delete_question`-Endpoint mit erweiterter Autorisierung. Keine neuen Model-Felder, keine Migration.

**Tech Stack:** Django 5.x, function-based views, Django-Templates (Bootstrap), Django-`TestCase` mit SQLite.

## Global Constraints

- Sprache im UI: Deutsch (Umlaute korrekt: ö, ü, ä, ß).
- Tests laufen mit SQLite (automatisch via `sys.argv`); Kommando: `python manage.py test <dotted.path> -v 2`.
- Session-Login in Tests via `self.client.force_login(user)` (nicht JWT — die Views sind session-basiert).
- Berechtigung überall über `request.user.profile.can_moderate()` (View) bzw. `request.user.profile.can_moderate` (Template) — kein direktes `is_staff`/`is_moderator` an neuen Stellen.
- Neue/erweiterte Endpoints folgen dem Bestandsmuster: `@login_required` + Inline-Re-Check + Redirect (GET-Link, kein CSRF — bewusster, dokumentierter Tradeoff).
- Commit-Trailer an jede Commit-Message anhängen:
  ```
  Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
  Claude-Session: https://claude.ai/code/session_01DQq5ReKsk6FnLTysGngmcz
  ```

---

## File Structure

| Datei | Verantwortung |
|---|---|
| `mathefragen/apps/user/models.py` | `Profile.can_moderate()` — einzige Berechtigungsquelle |
| `mathefragen/apps/user/tests/test_permissions.py` (neu) | Tests für `can_moderate()` |
| `mathefragen/apps/question/views.py` | neue View `toggle_question_visibility`; `delete_question`-Gate erweitern |
| `mathefragen/apps/question/urls.py` | Route für `toggle_question_visibility` |
| `mathefragen/apps/question/tests/test_moderation.py` (neu) | View- + Template-Integrationstests |
| `mathefragen/templates/question/question_content.html` | Moderations-Panel |

---

## Task 1: `Profile.can_moderate()`

**Files:**
- Modify: `mathefragen/apps/user/models.py` (nahe `is_moderator`, ~Zeile 410)
- Test: `mathefragen/apps/user/tests/test_permissions.py` (neu)

**Interfaces:**
- Consumes: `Profile.is_moderator()` (existiert, delegiert an Badge `can_edit_questions`); `Profile.user` (OneToOne zu `User`, hat `is_staff`).
- Produces: `Profile.can_moderate() -> bool` — `True` wenn der User `is_staff` ist ODER einen Moderator-Badge (`can_edit_questions=True`) hat.

- [ ] **Step 1: Write the failing test**

Create `mathefragen/apps/user/tests/test_permissions.py`:

```python
from django.test import TestCase
from django.contrib.auth.models import User

from mathefragen.apps.user.models import Badge


class CanModerateTestCase(TestCase):

    def test_normal_user_cannot_moderate(self):
        user = User.objects.create(username='normalo', email='normalo@mail.com')
        self.assertFalse(user.profile.can_moderate())

    def test_staff_user_can_moderate(self):
        user = User.objects.create(username='staffie', email='staffie@mail.com')
        user.is_staff = True
        user.save()
        self.assertTrue(user.profile.can_moderate())

    def test_badge_moderator_can_moderate(self):
        user = User.objects.create(username='modmod', email='modmod@mail.com')
        badge = Badge.objects.create(name='mod', can_edit_questions=True)
        user.profile.badges.add(badge)
        self.assertTrue(user.profile.can_moderate())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test mathefragen.apps.user.tests.test_permissions -v 2`
Expected: FAIL — `AttributeError: 'Profile' object has no attribute 'can_moderate'`

- [ ] **Step 3: Write minimal implementation**

In `mathefragen/apps/user/models.py`, direkt nach der bestehenden `is_moderator`-Methode (die `return self.can_edit_questions()` enthält, ~Zeile 410-412) einfügen:

```python
    def can_moderate(self):
        return self.user.is_staff or self.is_moderator()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python manage.py test mathefragen.apps.user.tests.test_permissions -v 2`
Expected: PASS (3 Tests)

- [ ] **Step 5: Commit**

```bash
git add mathefragen/apps/user/models.py mathefragen/apps/user/tests/test_permissions.py
git commit -m "feat(user): add Profile.can_moderate() permission helper

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01DQq5ReKsk6FnLTysGngmcz"
```

---

## Task 2: View + URL `toggle_question_visibility`

**Files:**
- Modify: `mathefragen/apps/question/views.py` (neue Funktion, z.B. nach `delete_question`, ~Zeile 391)
- Modify: `mathefragen/apps/question/urls.py` (Import-Tuple + `urlpatterns`)
- Test: `mathefragen/apps/question/tests/test_moderation.py` (neu)

**Interfaces:**
- Consumes: `Profile.can_moderate()` (Task 1); `Question.is_active` (BooleanField); `Question.get_absolute_url()`; `login_required`, `redirect` (bereits in `views.py` importiert).
- Produces: View `toggle_question_visibility(request, question_id)`; URL-Name `toggle_question_visibility` (kwarg `question_id`). Toggelt `Question.is_active` und redirected zur Frage.

- [ ] **Step 1: Write the failing test**

Create `mathefragen/apps/question/tests/test_moderation.py`:

```python
from django.test import Client, TestCase
from django.shortcuts import reverse
from django.contrib.auth.models import User

from mathefragen.apps.user.models import Badge
from mathefragen.apps.stats.models import GlobalStats
from ..models import Question


class ToggleVisibilityTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create(username='owner', email='owner@mail.com')
        cls.normal = User.objects.create(username='normal', email='normal@mail.com')
        cls.staff = User.objects.create(username='staff', email='staff@mail.com')
        cls.staff.is_staff = True
        cls.staff.save()

    def setUp(self):
        self.client = Client()
        self.question = Question.objects.create(
            title='Test', text='Test', user_id=self.owner.id, is_active=True
        )

    def _url(self):
        return reverse('toggle_question_visibility', kwargs={'question_id': self.question.id})

    def test_staff_toggles_visibility_off_then_on(self):
        self.client.force_login(self.staff)
        self.client.get(self._url())
        self.question.refresh_from_db()
        self.assertFalse(self.question.is_active)

        self.client.get(self._url())
        self.question.refresh_from_db()
        self.assertTrue(self.question.is_active)

    def test_normal_user_cannot_toggle_visibility(self):
        self.client.force_login(self.normal)
        self.client.get(self._url())
        self.question.refresh_from_db()
        self.assertTrue(self.question.is_active)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test mathefragen.apps.question.tests.test_moderation -v 2`
Expected: FAIL — `NoReverseMatch: Reverse for 'toggle_question_visibility' not found`

- [ ] **Step 3: Write minimal implementation — view**

In `mathefragen/apps/question/views.py`, nach `delete_question` (endet ~Zeile 390) einfügen:

```python
@login_required
def toggle_question_visibility(request, question_id):
    question = Question.objects.get(id=question_id)

    if request.user.profile.can_moderate():
        question.is_active = not question.is_active
        question.save()

    return redirect(question.get_absolute_url())
```

- [ ] **Step 4: Register the URL**

In `mathefragen/apps/question/urls.py`:

1. Import-Tuple erweitern — nach `delete_question,` die Zeile hinzufügen:
   ```python
       toggle_question_visibility,
   ```
2. In `urlpatterns` direkt nach der `delete_question`-Route hinzufügen:
   ```python
       path('moderate/<int:question_id>/visibility/', toggle_question_visibility, name='toggle_question_visibility'),
   ```

- [ ] **Step 5: Run test to verify it passes**

Run: `python manage.py test mathefragen.apps.question.tests.test_moderation -v 2`
Expected: PASS (2 Tests)

- [ ] **Step 6: Commit**

```bash
git add mathefragen/apps/question/views.py mathefragen/apps/question/urls.py mathefragen/apps/question/tests/test_moderation.py
git commit -m "feat(question): add moderator toggle_question_visibility view

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01DQq5ReKsk6FnLTysGngmcz"
```

---

## Task 3: `delete_question`-Gate auf `can_moderate()` erweitern

**Files:**
- Modify: `mathefragen/apps/question/views.py:379` (im bestehenden `delete_question`)
- Test: `mathefragen/apps/question/tests/test_moderation.py` (Klasse ergänzen)

**Interfaces:**
- Consumes: `Profile.can_moderate()` (Task 1); bestehende `delete_question`-Logik.
- Produces: `delete_question` erlaubt Löschen jetzt auch für `is_staff`-Admins ohne Badge (vorher nur Badge-Moderatoren via `is_moderator`).

- [ ] **Step 1: Write the failing test**

In `mathefragen/apps/question/tests/test_moderation.py` neue Testklasse anhängen:

```python
class DeleteQuestionAuthTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create(username='del_owner', email='del_owner@mail.com')
        cls.staff = User.objects.create(username='del_staff', email='del_staff@mail.com')
        cls.staff.is_staff = True
        cls.staff.save()
        cls.other = User.objects.create(username='del_other', email='del_other@mail.com')

    def setUp(self):
        self.client = Client()
        # delete_question ruft request.stats.update_total_questions();
        # die AccountCheckMiddleware setzt request.stats = GlobalStats.objects.last().
        # Ohne Row waere request.stats None -> AttributeError.
        GlobalStats.objects.create()
        self.question = Question.objects.create(
            title='ToDelete', text='ToDelete', user_id=self.owner.id
        )

    def _url(self):
        return reverse('delete_question', kwargs={'question_id': self.question.id})

    def test_staff_admin_can_soft_delete(self):
        self.client.force_login(self.staff)
        self.client.get(self._url())
        self.question.refresh_from_db()
        self.assertTrue(self.question.soft_deleted)

    def test_unrelated_normal_user_cannot_delete(self):
        self.client.force_login(self.other)
        self.client.get(self._url())
        self.question.refresh_from_db()
        self.assertFalse(self.question.soft_deleted)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test mathefragen.apps.question.tests.test_moderation.DeleteQuestionAuthTestCase -v 2`
Expected: FAIL — `test_staff_admin_can_soft_delete` schlägt fehl (`soft_deleted` bleibt `False`), weil das Gate aktuell nur `is_moderator` (Badge) erlaubt.

- [ ] **Step 3: Write minimal implementation**

In `mathefragen/apps/question/views.py` im `delete_question` die beiden Zeilen (~373 und ~379):

```python
    is_moderator = request.user.profile.is_moderator()
    ...
    elif is_moderator:
        delete_allowed = True
```

ändern zu:

```python
    can_moderate = request.user.profile.can_moderate()
    ...
    elif can_moderate:
        delete_allowed = True
```

(Die `can_be_deleted`-Zeile und der Owner-Zweig bleiben unverändert.)

- [ ] **Step 4: Run test to verify it passes**

Run: `python manage.py test mathefragen.apps.question.tests.test_moderation.DeleteQuestionAuthTestCase -v 2`
Expected: PASS (2 Tests)

- [ ] **Step 5: Commit**

```bash
git add mathefragen/apps/question/views.py mathefragen/apps/question/tests/test_moderation.py
git commit -m "feat(question): allow staff admins to delete via can_moderate gate

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01DQq5ReKsk6FnLTysGngmcz"
```

---

## Task 4: Moderations-Panel im Template

**Files:**
- Modify: `mathefragen/templates/question/question_content.html` (nach dem Aktions-Block, ~Zeile 95, innerhalb `<div class="col-md-11 ...">` aber außerhalb der `{% if question.is_active %}`-Blöcke)
- Test: `mathefragen/apps/question/tests/test_moderation.py` (Integrations-Testklasse ergänzen)

**Interfaces:**
- Consumes: `Profile.can_moderate` (Task 1, im Template ohne Klammern); URL-Name `toggle_question_visibility` (Task 2); URL-Name `delete_question` (existiert).
- Produces: sichtbares Panel mit zwei Buttons nur für Moderatoren.

- [ ] **Step 1: Write the failing test**

In `mathefragen/apps/question/tests/test_moderation.py` neue Testklasse anhängen:

```python
class ModerationPanelRenderTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create(username='p_owner', email='p_owner@mail.com')
        cls.normal = User.objects.create(username='p_normal', email='p_normal@mail.com')
        cls.staff = User.objects.create(username='p_staff', email='p_staff@mail.com')
        cls.staff.is_staff = True
        cls.staff.save()

    def setUp(self):
        self.client = Client()
        # question_detail_hashed ruft request.stats.update_total_questions();
        # daher GlobalStats-Row noetig (siehe DeleteQuestionAuthTestCase).
        GlobalStats.objects.create()
        self.question = Question.objects.create(
            title='PanelTest', text='PanelTest', user_id=self.owner.id
        )

    def _visibility_url(self):
        return reverse('toggle_question_visibility', kwargs={'question_id': self.question.id})

    def test_panel_visible_for_staff(self):
        self.client.force_login(self.staff)
        response = self.client.get(self.question.get_absolute_url())
        self.assertContains(response, self._visibility_url())

    def test_panel_hidden_for_normal_user(self):
        self.client.force_login(self.normal)
        response = self.client.get(self.question.get_absolute_url())
        self.assertNotContains(response, self._visibility_url())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test mathefragen.apps.question.tests.test_moderation.ModerationPanelRenderTestCase -v 2`
Expected: FAIL — `test_panel_visible_for_staff` findet die Visibility-URL nicht im gerenderten HTML.

- [ ] **Step 3: Write minimal implementation**

In `mathefragen/templates/question/question_content.html` den bestehenden Authentifizierungs-Block bei ~Zeile 81-95 (der die owner/`is_moderator`-„Bearbeiten"-Links enthält) belassen und **unmittelbar danach**, noch vor dem schließenden `</div>` bei Zeile 96, das Panel einfügen:

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

- [ ] **Step 4: Run test to verify it passes**

Run: `python manage.py test mathefragen.apps.question.tests.test_moderation.ModerationPanelRenderTestCase -v 2`
Expected: PASS (2 Tests)

- [ ] **Step 5: Run full moderation + permission suite**

Run: `python manage.py test mathefragen.apps.question.tests.test_moderation mathefragen.apps.user.tests.test_permissions -v 2`
Expected: PASS (alle Tests aus Task 1–4)

- [ ] **Step 6: Commit**

```bash
git add mathefragen/templates/question/question_content.html mathefragen/apps/question/tests/test_moderation.py
git commit -m "feat(question): add moderation control panel to question detail

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01DQq5ReKsk6FnLTysGngmcz"
```

---

## Manuelle Verifikation (nach allen Tasks)

1. Als `is_staff`-User (oder Badge-Moderator) eine Frage öffnen → Panel „Moderation" mit **Verstecken** + **Löschen** sichtbar.
2. **Verstecken** klicken → Seite lädt neu, Antworten/Formular weg, Button heißt jetzt **Einblenden**, Panel weiterhin sichtbar.
3. **Einblenden** → Frage wieder normal.
4. **Löschen** → Confirm-Dialog; nach Bestätigung Redirect auf Startseite (`?deleted=1`), Frage nicht mehr in Listen.
5. Als normaler User dieselbe Frage öffnen → kein Panel.

## Self-Review (vom Plan-Autor durchgeführt)

- **Spec-Coverage:** `can_moderate` (Task 1) ✓ · Verstecken/Einblenden View+URL (Task 2) ✓ · Löschen-Gate erweitert (Task 3) ✓ · Panel-Template (Task 4) ✓ · Tests je Task ✓. Kein `locked`/„Schließen" — bewusst out of scope laut Spec.
- **Placeholder-Scan:** keine TBD/TODO; jeder Code-Step enthält vollständigen Code + konkrete Kommandos.
- **Typ-Konsistenz:** URL-Name `toggle_question_visibility` und View-Signatur `(request, question_id)` in Task 2, 4 identisch; `can_moderate()` (View) / `can_moderate` (Template) konsistent; Feldname `is_active`, `soft_deleted` gemäß Model.
