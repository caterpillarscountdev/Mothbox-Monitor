
def test_user_manage(admin_client):
    res = admin_client.get('/users-manage')
    assert res.status_code == 200
    assert b"User List" in res.data

def test_user_manage_lists_user(admin_user, admin_client):
    res = admin_client.get('/users-manage')
    assert admin_user.email in str(res.data)
    
