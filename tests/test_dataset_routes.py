from mothmonitor.database import db
from mothmonitor.models import Night, Device
import datetime

def test_datasets_list_from_s3(admin_client, mocker):
    c = mocker.patch("boto3.client")
    c.return_value.list_objects.side_effect = [
        {"CommonPrefixes": [{"Prefix": "one/"}]},
        {"CommonPrefixes": [{"Prefix": "2025-12-31/"}]},
        {'Contents': [{'Key': 'one/2025-12-31/one_2025_12_31__18_40_10_HDR0.jpg', 'LastModified': datetime.datetime(2026, 1, 29, 14, 35, 18), 'ETag': '"cd8e167ee507db4933bec6493b0ea499"', 'ChecksumAlgorithm': ['CRC64NVME'], 'ChecksumType': 'FULL_OBJECT', 'Size': 22179295, 'StorageClass': 'STANDARD', 'Owner': {'ID': 'f4a5b1702a148cd25ba2419d72d5e036112b75c6d93225c1719da9d33045f4a2'}}, {'Key': 'one/2025-12-31/one_2025_12_31__19_20_10_HDR0.jpg', 'LastModified': datetime.datetime(2026, 1, 29, 14, 35), 'ETag': '"5fb9fd29ef9e108736f388d782ed9f55"', 'ChecksumAlgorithm': ['CRC64NVME'], 'ChecksumType': 'FULL_OBJECT', 'Size': 22291229, 'StorageClass': 'STANDARD', 'Owner': {'ID': 'f4a5b1702a148cd25ba2419d72d5e036112b75c6d93225c1719da9d33045f4a2'}}], 'Name': 'lo-mmm-test', 'Prefix': 'one/2025-12-31/', 'Delimiter': '/'}
        ]

    res = admin_client.get('/datasets/list?refresh=1')

    assert res.status_code == 200

    c.assert_called_with("s3")
    c.return_value.list_objects.assert_has_calls([
        mocker.call(Bucket='lo-mmm-test', Delimiter="/"),
        mocker.call(Bucket='lo-mmm-test', Delimiter="/", Prefix="one/"),
        mocker.call(Bucket='lo-mmm-test', Delimiter="/", Prefix="one/2025-12-31/")
    ])

    nights = list(db.session.execute(db.select(Night)).scalars())
    assert len(nights) == 1
    assert nights[0].device_id == 1
    assert nights[0].photo_count == 2
    assert nights[0].night.strftime("%Y-%m-%d") == '2025-12-31'

def test_datasets_list_from_s3_by_db(admin_client, mocker, device):
    c = mocker.patch("boto3.client")
    c.return_value.list_objects.side_effect = [
        {"CommonPrefixes": [{"Prefix": "one/"}]},
        {"CommonPrefixes": [{"Prefix": "2025-12-31/"}]},
        {'Contents': [{'Key': 'one/2025-12-31/one_2025_12_31__18_40_10_HDR0.jpg', 'LastModified': datetime.datetime(2026, 1, 29, 14, 35, 18), 'ETag': '"cd8e167ee507db4933bec6493b0ea499"', 'ChecksumAlgorithm': ['CRC64NVME'], 'ChecksumType': 'FULL_OBJECT', 'Size': 22179295, 'StorageClass': 'STANDARD', 'Owner': {'ID': 'f4a5b1702a148cd25ba2419d72d5e036112b75c6d93225c1719da9d33045f4a2'}}, {'Key': 'one/2025-12-31/one_2025_12_31__19_20_10_HDR0.jpg', 'LastModified': datetime.datetime(2026, 1, 29, 14, 35), 'ETag': '"5fb9fd29ef9e108736f388d782ed9f55"', 'ChecksumAlgorithm': ['CRC64NVME'], 'ChecksumType': 'FULL_OBJECT', 'Size': 22291229, 'StorageClass': 'STANDARD', 'Owner': {'ID': 'f4a5b1702a148cd25ba2419d72d5e036112b75c6d93225c1719da9d33045f4a2'}}], 'Name': 'lo-mmm-test', 'Prefix': 'one/2025-12-31/', 'Delimiter': '/'}
        ]

    device.last_seen = datetime.datetime.now()
    device.last_refreshed = datetime.datetime.now() - datetime.timedelta(days=1)
    
    res = admin_client.get('/datasets/list')

    assert res.status_code == 200

    c.assert_called_with("s3")
    c.return_value.list_objects.assert_has_calls([
        mocker.call(Bucket='lo-mmm-test', Delimiter="/"),
        mocker.call(Bucket='lo-mmm-test', Delimiter="/", Prefix="one/"),
        mocker.call(Bucket='lo-mmm-test', Delimiter="/", Prefix="one/2025-12-31/")
    ])

    nights = list(db.session.execute(db.select(Night)).scalars())
    assert len(nights) == 1
    assert nights[0].device_id == 2
    assert nights[0].device_id != device.id
    assert nights[0].photo_count == 2
    assert nights[0].night.strftime("%Y-%m-%d") == '2025-12-31'

    
def test_datasets_list_from_db(admin_client, mocker, night):
    c = mocker.patch("boto3.client")
        
    res = admin_client.get('/datasets/list')

    assert res.status_code == 200

    assert f"<td>{night.night.strftime('%Y-%m-%d')}</td>" in  res.text
