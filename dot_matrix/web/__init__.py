"""Web interface for Dot Matrix Art (FastAPI + plain ES-module front end).

Contents:
    app          - FastAPI app: static front end, GET /api/info, /api/demo, POST /api/convert, /api/palette
    convert_api  - parameter parsing and JSON encoding around the real converter (patterns.py, effects.py, ...)
    static/      - front end; dm_*.js is the JS port of the conversion used by the static GitHub Pages site
"""
