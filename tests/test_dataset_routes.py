from mothmonitor.database import db
from mothmonitor.models import Night, Device

def test_datasets_list_from_s3(admin_client, mocker):
    c = mocker.patch("boto3.client")
    c.return_value.list_objects.side_effect = [
        {"CommonPrefixes": [{"Prefix": "one/"}]},
        {"CommonPrefixes": [{"Prefix": "2025-12-31/"}]}
        ]

    res = admin_client.get('/datasets/list?refresh=1')

    assert res.status_code == 200

    c.assert_called_with("s3")
    c.return_value.list_objects.assert_has_calls([
        mocker.call(Bucket='lo-mmm-test', Delimiter="/"),
        mocker.call(Bucket='lo-mmm-test', Delimiter="/", Prefix="one/")
    ])

    nights = list(db.session.execute(db.select(Night)).scalars())
    assert len(nights) == 1
    assert nights[0].device_id == 1
    assert nights[0].night.strftime("%Y-%m-%d") == '2025-12-31'

def test_datasets_list_from_db(admin_client, mocker, night):
    c = mocker.patch("boto3.client")
        
    res = admin_client.get('/datasets/list')

    assert res.status_code == 200

    assert f"<td>{night.night.strftime('%Y-%m-%d')}</td>" in  res.text
