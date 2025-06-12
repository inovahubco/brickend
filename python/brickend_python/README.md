# Brickend Alpha – Python

**Brickend** is a code generation framework for Python back-end projects, designed to accelerate API development with FastAPI, SQLAlchemy/Alembic, and Jinja2 templates.

## 📋 Requirements

* Python 3.11+
* Git
* PostgreSQL or SQLite (depending on the example)

## ⚙️ Installation

```bash
# Clone the repository
git clone https://github.com/inovahubco/brickend.git
cd python/brickend_python

# Install in editable mode
pip install -e .[dev]
```

## 🚀 Quickstart

1. **Initialize a project**

   ```bash
   brickend init project my_project
   cd my_project
   ```
2. **Add an entity**

   ```bash
   brickend add_entity entity
   ```
3. **Generate code**

   ```bash
   brickend generate code entities.yaml -o .
   ```
4. **Run migrations**

   ```bash
   brickend migrate db
   ```
5. **Start the server**

   ```bash
   uvicorn app.main:app --reload
   ```
6. **Open** `http://localhost:8000/docs` to explore the API.

## 🛠 CLI Commands

* `brickend init project <name>`: Create the base project structure.
* `brickend add_entity entity`: Add or update `entities.yaml`.
* `brickend generate code`: Generate models, schemas, CRUD operations, routers, and configuration.
* `brickend migrate db`: Apply Alembic migrations (create, upgrade, downgrade).

## 📂 Generated Folder Structure

```
my_project/
├── app/                  # Generated source code
│   ├── main.py
│   ├── models/
│   ├── schemas/
│   ├── crud/
│   └── routers/
├── migrations/           # Alembic migrations
├── entities.yaml         # Entity definitions
├── pyproject.toml        # Package configuration
├── alembic.ini           # Alembic configuration
└── README.txt
```

## 🔒 Protected Regions

To customize templates without losing changes on regeneration, use:

```jinja
{# Jinja2 template #}
# <protected>imports</protected>
# <protected>extra_functions</protected>
```

The engine will preserve content within `<protected>...</protected>` blocks.

## 🎨 Template Customization

* Default templates: `brickend_core/integrations/back/fastapi/`
* User templates: `templates_user/back/fastapi/` (takes precedence)

## ✅ Tests and Coverage

* Run tests with coverage report:

  ```bash
  pytest --cov=brickend_core --cov=brickend_cli
  ```
* Minimum coverage: 80%.

## 📈 CI/CD

Recommended GitHub Actions workflow:

1. Run tests with coverage:

   ```bash
   pytest --cov
   ```
2. Generate coverage report:

   ```bash
   coverage xml
   ```
3. Upload `coverage.xml` as an artifact.

## 🤝 Contributing

1. Fork the repository and create a feature branch: `feature/x`.
2. Add tests and update documentation.
3. Open a Pull Request describing your changes.
