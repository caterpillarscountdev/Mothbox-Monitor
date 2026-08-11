import pytest
from mothmonitor import create_app, models, database
from flask_login import FlaskLoginClient
from datetime import date

import subprocess
import time

import ephemeral_port_reserve
import pytest
from redis import Redis
from redis.exceptions import ConnectionError as RedisConnectionError

@pytest.fixture(scope="session")
def redis_port() -> int:
    return ephemeral_port_reserve.reserve()  # type: ignore[no-any-return]

@pytest.fixture(scope="session", autouse=True)
def _start_redis(tmp_path_factory, redis_port):
    proc = subprocess.Popen(
        ["redis-server", "--port", str(redis_port)],
        cwd=tmp_path_factory.mktemp("redis-server"),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    while True:
        try:
            redis = Redis(port=redis_port, single_connection_client=True)
            redis.ping()
            break
        except (ConnectionError, RedisConnectionError):  # pragma: no cover
            time.sleep(0.1)

    yield
    proc.terminate()
    proc.wait()

@pytest.fixture(autouse=True)
def _reset_redis(redis_port):
    yield
    Redis(port=redis_port, single_connection_client=True).flushall()    

@pytest.fixture()
def app(requests_mock, mocker, redis_port):
    mocker.patch("boto3.client")
    database.connection_string = "sqlite:///:memory:"
    app = create_app(testing=True, redis_connection=f"redis://127.0.0.1:{redis_port}/0")
    app.config.update(
        TESTING= True,
        SECRET_KEY="test_secret_key_123",  # Use a secure key in real tests
        SESSION_COOKIE_SECURE=False,
        SESSION_COOKIE_HTTPONLY=False,
        SESSION_COOKIE_PATH="/",
        S3_BUCKET="Test-Test",
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
def device_2(app):
    d = models.Device(name="", label="Sample Device")
    d.generate_upload_key()
    database.db.session.add(d)
    database.db.session.commit()
    yield d

@pytest.fixture()
def device_3(app):
    d = models.Device(name="", label="Another Device")
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

