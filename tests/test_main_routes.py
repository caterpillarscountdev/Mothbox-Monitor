

def test_index(client):
    res = client.get('/')
    assert b'Moth Monitor' in res.data

def test_dashboard_auth_required(client):
    res = client.get('/dashboard')
    assert res.status_code == 302
    assert res.headers["Location"] == '/auth/login?next=/dashboard'
    
