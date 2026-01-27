
def test_check_key_cors(client):
    res = client.options('/upload/check_key')
    assert res.headers["Access-Control-Allow-Origin"] == "*"

def test_check_key_no_key(client):
    res = client.get('/upload/check_key')
    assert res.status_code == 401

def test_check_key_invalid_key(client, device):
    res = client.get('/upload/check_key?key=asdf')
    assert res.status_code == 401

def test_check_key_valid_key(client, device):
    res = client.get('/upload/check_key?key='+device.upload_key)
    assert res.status_code == 200


def test_check_manifest_user(admin_client):
    res = admin_client.post('/upload/check_manifest', json={
        "deviceName": "testDevice",
        "night": "2026-01-01",
        "files": []
    })
    assert res.status_code == 200
    
def test_check_manifest(client, device):
    res = client.post('/upload/check_manifest?key='+device.upload_key, json={
        "deviceName": "testDevice",
        "night": "2026-01-01",
        "files": []
    })
    assert res.status_code == 200
    

def test_check_manifest_existing_file(client, device, mocker):
    c = mocker.patch("boto3.client")
    c.return_value.head_object.return_value = {"ContentLength": 1048}
    c.return_value.generate_presigned_url.return_value = "url"
    res = client.post('/upload/check_manifest?key='+device.upload_key, json={
        "deviceName": "testDevice",
        "night": "2026-01-01",
        "files": [{"filename": "test.jpg", "size": 1048, "type": "image/jpeg"}]
    })

    assert res.status_code == 200

    c.assert_called_with("s3")
    c.return_value.head_object.assert_called_with(Bucket='lo-mmm-test', Key='testDevice/2026-01-01/test.jpg')
    c.return_value.generate_presigned_url.assert_not_called()

    assert len(res.json["files"]) == 1
    assert res.json["files"][0]["filename"] == "test.jpg"
    assert res.json["files"][0]["location"] == "https://lo-mmm-test.s3.amazonaws.com/testDevice/2026-01-01/test.jpg"
    assert res.json["files"][0]["missing"] == False
    assert "upload_url" not in res.json["files"][0]

    
def test_check_manifest_missing_file(client, device, mocker):
    c = mocker.patch("boto3.client")
    c.return_value.head_object.raiseError.side_effect = c.exceptions.ClientError()
    c.return_value.generate_presigned_url.return_value = "signed_url"
    res = client.post('/upload/check_manifest?key='+device.upload_key, json={
        "deviceName": "testDevice",
        "night": "2026-01-01",
        "files": [{"filename": "test.jpg", "size": 1048, "type": "image/jpeg"}]
    })

    assert res.status_code == 200

    c.assert_called_with("s3")
    c.return_value.head_object.assert_called_with(Bucket='lo-mmm-test', Key='testDevice/2026-01-01/test.jpg')
    c.return_value.generate_presigned_url.assert_called_with('put_object', Params={'Bucket': 'lo-mmm-test', 'Key': 'testDevice/2026-01-01/test.jpg'}, ExpiresIn=3600)

    assert len(res.json["files"]) == 1
    assert res.json["files"][0]["filename"] == "test.jpg"
    assert res.json["files"][0]["location"] == "https://lo-mmm-test.s3.amazonaws.com/testDevice/2026-01-01/test.jpg"
    assert res.json["files"][0]["missing"] == True
    assert res.json["files"][0]["upload_url"] == "signed_url"
