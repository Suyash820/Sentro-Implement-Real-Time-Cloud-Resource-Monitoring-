import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_home(client):
    rv = client.get('/')
    assert rv.status_code == 200
    assert b'Welcome to the Sentro Workload API!' in rv.data

def test_health(client):
    rv = client.get('/health')
    assert rv.status_code == 200
    assert b'healthy' in rv.data
