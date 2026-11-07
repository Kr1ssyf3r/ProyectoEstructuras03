"""Debug script for CSRF test - checking abort behavior."""
from application import create_app
import tempfile, os
from flask import abort

tmp = tempfile.mkdtemp()

app = create_app()

client = app.test_client()

with client.session_transaction() as s:
    s['usuario_id'] = 'user1'
    s['csrf_feed'] = 'mytoken'
    s['csrf_token'] = 'mytoken'

print('Session keys:', list(s.keys()))

# Directly test if validar_token is being called
# by checking the route response
resp = client.post('/feed/me-gusta/1')
print('Status:', resp.status_code)
print('Location:', resp.location)
print('Data:', resp.data)

# Now let's try with empty form data explicitly
resp2 = client.post('/feed/me-gusta/1', data={})
print('\\nWith data={}:')
print('Status:', resp2.status_code)
print('Location:', resp2.location)