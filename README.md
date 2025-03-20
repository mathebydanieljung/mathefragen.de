<p align="center">
  <a href="https://mathefragen.de">
    <picture>
      <img src="https://github.com/user-attachments/assets/d7a8c81b-4ff0-4093-a979-a0028110bb00" height="80" alt="Logo of mathefragen.de">
    </picture>
    <div align="center">Die Lernplattform von Mathe by Daniel Jung</div>
  </a>
</p>

<div style="display: flex; justify-content: space-between;" align="center">
    <a href="https://www.paypal.com/donate/?hosted_button_id=5H4ZXE6GFWDC6">
      <picture>
        <img src="https://github.com/user-attachments/assets/d0372ef1-cbec-4404-a7f6-4e3b8d074e1f" height="40" alt="PayPal Donate Button">
      </picture>
    </a>
</div>

<img width="1348" alt="Screenshot of mathefragen.de" src="https://github.com/user-attachments/assets/ddf2fc7d-c3c9-4fa0-b63e-2b5d8498015e">

# mathefragen.de

This is the official repository of the mathefragen.de and affiliated projects. We are constantly working on improving the platform and adding
new features. Please feel free to contribute to the project by opening issues or pull requests.

Find the project at https://mathefragen.de

## Support this project

This software is maintained and run on the infrastructure of the [Daniel Jung Media GmbH](https://danieljung.io). If you
like the project and want to support us, please consider donating to us. This pays the infrastructure and new features
for this project.

## Development

### Via Docker

There is a docker-compose.yml-file which can be used to start the development environment. It will start a postgres
database, a redis server and the django app. The django app will be started with the `runserver` command and will reload
on code changes.

```sh
docker compose up
```

### Create a superuser

Create your first admin user:

```shell
docker compose exec django python manage.py createsuperuser
```

### Via poetry

You can also start the development environment via poetry. First you need to install the dependencies:

```sh
poetry install
```

Start a database:

```sh
docker compose up -d postgres
```

Then you can start the development server:

```sh
poetry run python manage.py runserver
```

### Compressor

On the first start, you might need to execute compressor manually:

```sh
python manage.py compress

# or
docker compose exec django python manage.py compress
```

## Deployment

Deployment process is done via gitlab CI/CD. All you need to do is pushing your changes and then create a git tag of the
commit you want to deploy containing a semantic versioning scheme:

MajorRelease.MinorRelease.HotFixes (e.g. 1.2.25)

### Updating .env files

If you want to update the .env files that the main server uses, you need to update them on the main production servers
on the directory:
`/var/www/aiedn/apps/mathefragen.de/`.

### Updating NGINX configs

To update the NGINX configs you need make your changes on the https://gitlab.com/new-learning/aiedn-group/configs/nginx
and then pull the changes on the server from the directory `/var/www/aiedn/setup`.

## Troubleshooting

### Remove a user

The previous developers have diverged the names of the tables from the Django default. This makes it difficult to delete spamming users. Here's a script to delete a user from the python shell:

```py
from django.db import connection

try:
    with connection.cursor() as cursor:
        # Begin transaction
        cursor.execute("BEGIN")

        # Define problematic question IDs - add the new one we found
        problem_questions = [56, 157]
        user_id = 1030  # The user we want to delete

        print(f"Handling specific problematic questions: {problem_questions}")

        # Step 1: Handle known problematic questions first
        for q_id in problem_questions:
            # First clear hashtag connections - this was explicitly mentioned in error
            cursor.execute(
                "DELETE FROM hashtag_hashtag_questions WHERE question_id = %s", [q_id])
            print(
                f"Removed {cursor.rowcount} hashtag connections from question {q_id}")

            # Handle stats views
            cursor.execute(
                "DELETE FROM stats_questionview WHERE question_id = %s", [q_id])
            print(
                f"Removed {cursor.rowcount} rows from stats_questionview for question {q_id}")

            # Handle other known potential references
            reference_tables = [
                'question_questionvote',
                'question_answer',
                'question_question_hashtags',
                'review_userreview',
                'user_review',
                'question_accepted_answer'  # Additional possible relation
            ]

            for table in reference_tables:
                try:
                    # Check if table exists
                    cursor.execute(f"SELECT to_regclass('{table}')")
                    table_exists = cursor.fetchone()[0] is not None

                    if table_exists:
                        # Check if column exists
                        cursor.execute(f"""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = '{table}' AND column_name LIKE '%question%'
                        """)
                        columns = cursor.fetchall()

                        for column in columns:
                            column_name = column[0]
                            cursor.execute(
                                f"DELETE FROM {table} WHERE {column_name} = %s", [q_id])
                            print(
                                f"Removed {cursor.rowcount} rows from {table}.{column_name} for question {q_id}")
                except Exception as e:
                    print(
                        f"Error handling {table} for question {q_id}: {str(e)}")

            # Try to delete the question now that references are cleared
            try:
                cursor.execute(
                    "DELETE FROM question_question WHERE id = %s", [q_id])
                print(
                    f"Deleted question {q_id}: {cursor.rowcount} rows affected")
            except Exception as e:
                print(f"Failed to delete question {q_id}: {str(e)}")
                # Get more details about remaining references
                cursor.execute("""
                SELECT tc.table_name, kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND ccu.table_name = 'question_question'
                AND ccu.column_name = 'id'
                """)

                possible_references = cursor.fetchall()
                print(
                    f"Possible remaining references to questions: {possible_references}")

                # Try to clear these references too
                for ref_table, ref_col in possible_references:
                    try:
                        cursor.execute(
                            f"DELETE FROM {ref_table} WHERE {ref_col} = %s", [q_id])
                        print(
                            f"Cleared {cursor.rowcount} rows from {ref_table}.{ref_col}")
                    except Exception as e2:
                        print(
                            f"Could not clear {ref_table}.{ref_col}: {str(e2)}")

                # Try one more time to delete the question
                try:
                    cursor.execute(
                        "DELETE FROM question_question WHERE id = %s", [q_id])
                    print(
                        f"Second attempt to delete question {q_id}: {cursor.rowcount} rows affected")
                except Exception as e3:
                    print(f"Still failed to delete question {q_id}: {str(e3)}")

        # Step 2: Handle remaining questions by this user
        cursor.execute(
            "SELECT id FROM question_question WHERE user_id = %s", [user_id])
        user_questions = [row[0] for row in cursor.fetchall()]
        print(
            f"Found {len(user_questions)} remaining questions by user {user_id}")

        if user_questions:
            for q_id in user_questions:
                # Same thorough process for each of user's questions
                # First clear hashtag connections
                cursor.execute(
                    "DELETE FROM hashtag_hashtag_questions WHERE question_id = %s", [q_id])
                print(
                    f"Removed {cursor.rowcount} hashtag connections from question {q_id}")

                # Handle stats views
                cursor.execute(
                    "DELETE FROM stats_questionview WHERE question_id = %s", [q_id])
                print(
                    f"Removed {cursor.rowcount} rows from stats_questionview for question {q_id}")

                # Handle other potential references one by one (safer than using IN clauses)
                for table in reference_tables:
                    try:
                        if cursor.execute(f"SELECT to_regclass('{table}')").fetchone()[0] is not None:
                            cursor.execute(f"""
                            SELECT column_name 
                            FROM information_schema.columns 
                            WHERE table_name = '{table}' AND column_name LIKE '%question%'
                            """)

                            for column in cursor.fetchall():
                                column_name = column[0]
                                cursor.execute(
                                    f"DELETE FROM {table} WHERE {column_name} = %s", [q_id])
                                print(
                                    f"Removed {cursor.rowcount} rows from {table}.{column_name} for question {q_id}")
                    except Exception as e:
                        print(
                            f"Error handling {table} for question {q_id}: {str(e)}")

                # Delete the question
                try:
                    cursor.execute(
                        "DELETE FROM question_question WHERE id = %s", [q_id])
                    print(
                        f"Deleted question {q_id}: {cursor.rowcount} rows affected")
                except Exception as e:
                    print(f"Failed to delete question {q_id}: {str(e)}")

        # Step 3: Delete all user references
        cursor.execute("""
        SELECT DISTINCT tc.table_name, kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
        AND ccu.table_name = 'auth_user'
        AND ccu.column_name = 'id'
        """)

        user_references = cursor.fetchall()
        print(f"Found {len(user_references)} tables referencing the user")

        # Process user references
        for table, column in user_references:
            try:
                cursor.execute(
                    f"DELETE FROM {table} WHERE {column} = %s", [user_id])
                print(f"Deleted {cursor.rowcount} rows from {table}.{column}")
            except Exception as e:
                print(f"Error with {table}.{column}: {str(e)}")

        # Step 4: Final attempt to delete the user
        cursor.execute("DELETE FROM auth_user WHERE id = %s", [user_id])

        if cursor.rowcount > 0:
            print(f"Successfully deleted user {user_id}")
            cursor.execute("COMMIT")
            print("Transaction committed successfully")
        else:
            print(f"Failed to delete user {user_id}")
            cursor.execute("ROLLBACK")
            print("Transaction rolled back")

except Exception as e:
    print(f"Fatal error: {str(e)}")
    try:
        cursor.execute("ROLLBACK")
        print("Transaction rolled back")
    except:
        pass
```
