-- Imported field plot data and field-derived carbon results from Elin.


-- 1. Staging table.

CREATE TABLE elin_plot_import (
    pointid VARCHAR2(30),
    xcoord NUMBER,
    ycoord NUMBER,
    carbon_kg NUMBER
);

--2. Load plot file
LOAD elin_plot_import /path/to/Field_data.csv

SELECT *
FROM elin_plot_import
ORDER BY TO_NUMBER(pointid);


SELECT pointid
FROM elin_plot_import
WHERE pointid IN (
    SELECT plot_id
    FROM cgs_field_plot
);


-- 3. Inserted plot centres.

INSERT INTO cgs_field_plot (
    plot_id, x_coord, y_coord, crs_name, radius_m
)
SELECT
    pointid, xcoord, ycoord, 'EPSG:27700', 10
FROM elin_plot_import;


-- 4. Inserted carbon results from allometric equations.

INSERT INTO cgs_plot_carbon (
    plot_id, carbon_kg_c
)
SELECT
    pointid, carbon_kg
FROM elin_plot_import;

COMMIT;

SELECT
    p.plot_id,
    p.x_coord,
    p.y_coord,
    p.crs_name,
    p.radius_m,
    c.carbon_kg_c
FROM cgs_field_plot p
JOIN cgs_plot_carbon c
    ON p.plot_id = c.plot_id
ORDER BY p.plot_id;
