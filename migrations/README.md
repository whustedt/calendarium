# Database Migrations Folder

This folder contains the migration scripts for your Flask application. Migrations are used to manage the evolution of your database schema over time in a consistent and organized manner. This setup supports a single-database configuration.

## Getting Started with Migrations

### Initialize Migrations
Before you can start managing database migrations, you need to initialize the migrations directory and scripts:

```bash
flask db init
```

This command will create the necessary configuration and directory structure (`migrations/`) for handling database migrations.

### Create Migration Scripts
Whenever you modify your database models (in `models.py`), you need to generate new migration scripts:

```bash
flask db migrate -m "Description of the changes"
```

Replace `"Description of the changes"` with a brief description of the model changes you have made. This command will autogenerate a migration script in the `migrations/versions/` directory that describes the changes needed to update the database schema.

### Apply Migrations
To apply the generated migration scripts to your database, use the following command:

```bash
flask db upgrade
```

This command will apply the migration scripts to the database, updating the schema according to the instructions defined in the migration scripts. It's recommended to backup your database before running migrations, especially in a production environment.

## Best Practices
- **Version Control**: Keep your migration scripts under version control. They are an essential part of your application's codebase.
- **Regular Commits**: Generate migration scripts and commit them to your version control system regularly whenever you make changes to your models.
- **Manual Review**: Always review the generated migration scripts before applying them. This helps avoid unintended database schema changes.
- **Testing**: Test your migration scripts in a development environment before applying them in production. This practice helps catch issues that may not be apparent in the model code alone.

## Troubleshooting
If you encounter issues while running migration commands, consider the following:
- Ensure that the Flask application context is set up correctly, especially when running commands from outside your main application script.
- Check the database URI and other related settings in your configuration to ensure they are correct for your database server.

By following these guidelines, you can effectively manage and evolve your database schema as your application develops.