from django.db import migrations

# Leftovers of apps removed from INSTALLED_APPS long ago. social_auth_usersocialauth
# still had a FK to auth_user and blocked user deletes.
# Backup before drop: /root/backups/legacy_tables_before_drop_20260929_2336.dump on the app server.
LEGACY_TABLES = [
    'django_site',
    'django_summernote_attachment',
    'messenger_message_to_users',
    'messenger_message',
    'social_auth_association',
    'social_auth_code',
    'social_auth_nonce',
    'social_auth_partial',
    'social_auth_usersocialauth',
    'wolfram_wolframquery',
]


def drop_legacy_tables(apps, schema_editor):
    existing = set(schema_editor.connection.introspection.table_names())
    for table in LEGACY_TABLES:
        if table in existing:
            schema_editor.execute('DROP TABLE %s' % schema_editor.quote_name(table))


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0024_remove_profile_synced'),
    ]

    operations = [
        migrations.RunPython(drop_legacy_tables, migrations.RunPython.noop),
    ]
