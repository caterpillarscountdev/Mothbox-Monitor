
def test_datasets_list(admin_client, mocker):
    c = mocker.patch("boto3.client")
    c.return_value.list_objects.return_value = {"CommonPrefixes": [{"Prefix": "one/"}]}

    res = admin_client.get('/datasets/list')

    assert res.status_code == 200

    c.assert_called_with("s3")
    c.return_value.list_objects.assert_has_calls([
        mocker.call(Bucket='lo-mmm-test', Delimiter="/"),
        mocker.call(Bucket='lo-mmm-test', Delimiter="/", Prefix="one/")
    ])
    
