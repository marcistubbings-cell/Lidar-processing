# Importing Python libraries
import logging
import os
from datetime import date, datetime
from decimal import Decimal

from flask import Flask, jsonify
from flask_cors import CORS
import oracledb
from pyproj import Transformer

# Setting up logging and coordinate conversion

LOGGER = logging.getLogger(__name__)

# The stored plot points are in British National Grid. GeoJSON must use WGS84.
BNG_TO_WGS84 = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)

# Main SQL query

PLOT_SELECT = """
SELECT p.plot_id, p.greenspace_id, p.zone_code, p.survey_date,
       p.x_coord, p.y_coord, p.crs_name, p.radius_m, p.notes,
       c.carbon_kg_c
FROM cgs_field_plot p
JOIN cgs_plot_carbon c ON c.plot_id = p.plot_id
"""

# Statistical SQL query

SUMMARY_SELECT = """
SELECT COUNT(*) AS total_plots,
       COUNT(c.carbon_kg_c) AS plots_with_carbon,
       SUM(c.carbon_kg_c) AS measured_carbon_sum_kg_c,
       ROUND(AVG(c.carbon_kg_c), 2) AS mean_plot_carbon_kg_c,
       MIN(c.carbon_kg_c) AS min_plot_carbon_kg_c,
       MAX(c.carbon_kg_c) AS max_plot_carbon_kg_c
FROM cgs_field_plot p
JOIN cgs_plot_carbon c ON c.plot_id = p.plot_id
"""

# Converting Oracle values into JSON-compatible values

def _json_value(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value

# Connecting to Oracle and executing SQL

def fetch_records(query, binds=None):
    """Execute predefined read-only SQL and return a list of dicts.

    Connection parameters are intentionally obtained from environment variables.
    Never put credentials in GitHub or pass SQL text from website users.
    """

  # Getting the database credentials
  
    user = os.environ.get("ORACLE_USER")
    password = os.environ.get("ORACLE_PASSWORD")
    dsn = os.environ.get("ORACLE_DSN")
    if not all((user, password, dsn)):
        raise RuntimeError("Oracle connection environment variables are missing")

  # Establishing the connection, executing the SQL query and retrieving the results

    with oracledb.connect(user=user, password=password, dsn=dsn) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, binds or {})
            keys = [col[0].lower() for col in cursor.description]
            return [dict(zip(keys, map(_json_value, row))) for row in cursor.fetchall()]

# Creating the app

def create_app():
    app = Flask(__name__)
    # Default same-origin requests work without CORS. Set a trusted frontend origin
    # when running frontend and backend on different hosts during development.
    origins = [v.strip() for v in os.environ.get("CORS_ORIGINS", "").split(",") if v.strip()]
    if origins:
        CORS(app, resources={r"/api/*": {"origins": origins}})

# Handling errors
  
    @app.errorhandler(500)
    def handle_internal_error(error):
        LOGGER.error("API internal error: %s", error)
        return jsonify({"error": "Internal server error"}), 500

  # The API endpoints

    @app.get("/api/health")
    def health():
        # Health endpoint proves process is running, not that Oracle is available.
        return jsonify({"status": "ok", "database_checked": False})

  # Retrieve all field plots

    @app.get("/api/plots")
    def plots():
        data = fetch_records(PLOT_SELECT + " ORDER BY p.plot_id")
        return jsonify({"count": len(data), "plots": data})

  # Retrieve carbon statistics

    @app.get("/api/plots/summary")
    def summary():
        rows = fetch_records(SUMMARY_SELECT)
        result = rows[0] if rows else {}
        result["note"] = (
            "These are descriptive statistics for sampled plots, not "
            "greenspace-wide or citywide carbon estimates."
        )
        result["carbon_unit"] = "kg C"
        return jsonify(result)

  # Retrieve plot coordinates for the map

    @app.get("/api/plots/geojson")
    def plots_geojson():
        data = fetch_records(
            PLOT_SELECT + " WHERE p.x_coord IS NOT NULL AND p.y_coord IS NOT NULL"
            " ORDER BY p.plot_id"
        )
        features = []
        skipped = 0
        for plot in data:
            crs = str(plot.get("crs_name") or "").upper().replace(" ", "")
            # Reject unknown / conflicting CRS rather than silently place points wrongly.
            if crs not in ("EPSG:27700", "27700"):
                skipped += 1
                continue
            lon, lat = BNG_TO_WGS84.transform(float(plot["x_coord"]), float(plot["y_coord"]))
            features.append({
                "type": "Feature",
                "id": plot["plot_id"],
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": {k: v for k, v in plot.items() if k not in ("x_coord", "y_coord")},
            })
        return jsonify({"type": "FeatureCollection", "features": features,
                        "metadata": {"skipped_unknown_crs": skipped, "coordinates": "WGS84 longitude/latitude"}})

    # Retrieve one particular plot
  
    @app.get("/api/plots/<plot_id>")
    def plot_detail(plot_id):
        if len(plot_id) > 30:
            return jsonify({"error": "Invalid plot ID"}), 400
        rows = fetch_records(PLOT_SELECT + " WHERE p.plot_id = :plot_id", {"plot_id": plot_id})
        if not rows:
            return jsonify({"error": "Plot not found"}), 404
        return jsonify(rows[0])

    return app

# Starting the application

app = create_app()

if __name__ == "__main__":
    # Development only. Use gunicorn or an approved WSGI host for deployment.
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=False)
