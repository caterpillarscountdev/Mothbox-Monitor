import pytest
from mothmonitor import create_app, models, database
from flask_login import FlaskLoginClient

@pytest.fixture()
def app():
    database.connection_string = "sqlite:///:memory:"
    app = create_app()
    app.config.update(
        TESTING= True,
        SECRET_KEY="test_secret_key_123",  # Use a secure key in real tests
        SESSION_COOKIE_SECURE=False,
        SESSION_COOKIE_HTTPONLY=False,
        SESSION_COOKIE_PATH="/"
    )

    app.test_client_class = FlaskLoginClient

    with app.app_context():
        database.db.create_all()
        database.db.session.add(models.Role(name="Admin", description="Admin", permissions=["admin", "research", "site"]))
        database.db.session.add(models.Role(name="Site", description="Site", permissions=["admin", "site"]))
        database.db.session.commit()
        yield app
        database.db.drop_all()

@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def admin_user(app):
    with app.app_context():
        admin = database.db.session.scalars(database.db.select(models.Role).where(models.Role.name=="Admin")).first()
        u = models.User(name='Test Test', email="test2@example.com", password="test", fs_uniquifier="2", active=True, roles=[admin])
        database.db.session.add(u)
        database.db.session.commit()
        yield u

@pytest.fixture()
def admin_client(admin_user, app):
    return app.test_client(user=admin_user)

@pytest.fixture()
def device(app):
    with app.app_context():
        d = models.Device(name="")
        d.generate_upload_key()
        database.db.session.add(d)
        database.db.session.commit()
        yield d
