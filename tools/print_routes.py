from app import create_app
app = create_app()

with app.app_context():
    routes = sorted([
        (r.endpoint, list(r.methods)) for r in app.url_map.iter_rules() if not str(r.endpoint).startswith('static')
    ])
    for ep, methods in routes:
        print(ep, methods)
