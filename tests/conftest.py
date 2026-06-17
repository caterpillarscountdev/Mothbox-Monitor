import pytest
from mothmonitor import create_app, models, database
from flask_login import FlaskLoginClient
from datetime import date


@pytest.fixture()
def app(mocker):
    c = mocker.patch("boto3.client")
    database.connection_string = "sqlite:///:memory:"
    app = create_app(testing=True)
    app.config.update(
        TESTING= True,
        SECRET_KEY="test_secret_key_123",  # Use a secure key in real tests
        S3_BUCKET="test-bucket",
        SESSION_COOKIE_SECURE=False,
        SESSION_COOKIE_HTTPONLY=False,
        SESSION_COOKIE_PATH="/"
    )

    app.test_client_class = FlaskLoginClient

    with app.app_context():
        database.db.create_all()
        database.db.session.add(models.Role(name="Admin", description="Admin", permissions=["admin", "research", "site"]))
        database.db.session.add(models.Role(name="Site", description="Site", permissions=["site"]))
        database.db.session.commit()
        yield app
        database.db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def admin_user(app):
    admin = database.db.session.scalars(database.db.select(models.Role).where(models.Role.name=="Admin")).first()
    u = models.User(name='Test Test', email="test2@example.com", password="test", fs_uniquifier="2", active=True, roles=[admin])
    database.db.session.add(u)
    database.db.session.commit()
    yield u

@pytest.fixture()
def site_user(app, device):
    role = database.db.session.scalars(database.db.select(models.Role).where(models.Role.name=="Site")).first()
    u = models.User(name='Test Site', email="testsite@example.com", password="test", fs_uniquifier="3", active=True, roles=[role])
    database.db.session.add(u)
    database.db.session.commit()
    yield u


@pytest.fixture()
def site_user_assigned(site_user, device):
    device.site_users.append(site_user)

@pytest.fixture()
def client_site_user(app, site_user):
    return app.test_client(user=site_user)

    
@pytest.fixture()
def admin_client(admin_user, app):
    return app.test_client(user=admin_user)

@pytest.fixture()
def device(app):
    d = models.Device(name="", label="Test Device")
    d.generate_upload_key()
    database.db.session.add(d)
    database.db.session.commit()
    yield d

@pytest.fixture()
def night(app, device):
    n = models.Night(night=date(2025,12,30), device_id=device.id)
    database.db.session.add(n)
    database.db.session.commit()
    yield n

@pytest.fixture()
def mailer(app):
    with app.extensions['mail'].record_messages() as outbox:
        yield outbox
