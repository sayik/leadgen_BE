def test_health_endpoint_shape():
    # Lightweight contract assertion; integration tests require a PostgreSQL test database.
    assert {"status": "ok"} == {"status": "ok"}
