# 🌍 Translation Guide

## Supported Languages

- 🇬🇧 English (en) - Default
- 🇩🇪 Deutsch (de) - German
- 🇷🇺 Русский (ru) - Russian

## How to Add/Update Translations

### 1. Mark strings for translation in code

In Python files:
```python
from django.utils.translation import gettext_lazy as _

_('String to translate')
```

In templates:
```django
{% load i18n %}
{% trans "String to translate" %}
```

### 2. Extract translatable strings

```bash
python manage.py makemessages -l de  # For German
python manage.py makemessages -l ru  # For Russian
```

This creates/updates `.po` files in `locale/de/LC_MESSAGES/` and `locale/ru/LC_MESSAGES/`

### 3. Edit translation files

Open the `.po` files and add translations:

```po
#: inventory/models.py:28
msgid "Location"
msgstr "Локация"  # Russian translation
```

### 4. Compile translations

```bash
python manage.py compilemessages
```

### 5. Restart server

The translations will be available after server restart.

## Translation Files Location

```
locale/
├── de/
│   └── LC_MESSAGES/
│       └── django.po
└── ru/
    └── LC_MESSAGES/
        └── django.po
```

## Language Switcher

Users can switch languages using the language switcher in the top-right corner of the page.

## Current Translation Status

- ✅ Settings configured
- ✅ Base template with language switcher
- ✅ Home page template updated
- ⚠️ Other templates need translation tags
- ⚠️ Translation files need to be filled

## Next Steps

1. Add `{% trans %}` tags to all templates
2. Add `_()` to all model verbose names and validation messages
3. Fill in translations in `.po` files
4. Compile messages
5. Test all languages

