def test_user_access(client):
    res = client.get('/users/manage')
    assert res.status_code == 403


def test_user_manage(admin_client):
    res = admin_client.get('/users/manage')
    assert res.status_code == 200
    assert b"User List" in res.data

def test_user_manage_lists_user(admin_user, admin_client):
    res = admin_client.get('/users/manage')
    assert admin_user.email in str(res.data)

def test_user_manage_edit_new(admin_client):
    res = admin_client.get('/users/manage/edit/')
    assert b'ame="email" value=""' in res.data

def test_user_manage_edit_existing(admin_client):
    res = admin_client.get('/users/manage/edit/1')
    assert b'ame="email" value="test2@example.com"' in res.data
    
