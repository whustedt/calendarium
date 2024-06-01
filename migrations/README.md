Single-database configuration for Flask.

Run flask db init to create the migrations folder and the initial configurations if you haven't done so already.
Run flask db migrate to create the migration script(s) after any changes to your database models.
Run flask db upgrade to apply the migration script(s) to the database, which adjusts the schema as needed.