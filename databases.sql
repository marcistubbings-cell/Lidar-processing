-- Examples to demonstrate how the tables link together.

-- 1. DATA ZONES

CREATE TABLE cgs_data_zone (
    zone_code VARCHAR2(20) PRIMARY KEY,
    zone_name VARCHAR2(150)
);


-- 2. ENVIRONMENTAL RESULTS

CREATE TABLE cgs_envdep_result (
    zone_code VARCHAR2(20) PRIMARY KEY,
    canopy_pct NUMBER,
    index_score NUMBER,
    dep_class VARCHAR2(30) NOT NULL,
    missing_reason VARCHAR2(300),

    CONSTRAINT cgs_env_zone_fk
        FOREIGN KEY (zone_code)
        REFERENCES cgs_data_zone (zone_code)
);


-- 3. GREENSPACES

CREATE TABLE cgs_greenspace (
    greenspace_id VARCHAR2(100) PRIMARY KEY,
    site_name VARCHAR2(150),
    site_type VARCHAR2(100),
    area_m2 NUMBER CHECK (area_m2 >= 0)
);


-- 4. FIELD PLOTS
-- A plot can be linked to a greenspace and a data zone.

CREATE TABLE cgs_field_plot (
    plot_id VARCHAR2(30) PRIMARY KEY,
    greenspace_id VARCHAR2(100),
    zone_code VARCHAR2(20),
    survey_date DATE,
    x_coord NUMBER,
    y_coord NUMBER,
    crs_name VARCHAR2(50),
    radius_m NUMBER CHECK (radius_m > 0),
    notes VARCHAR2(500),

    CONSTRAINT cgs_plot_site_fk
        FOREIGN KEY (greenspace_id)
        REFERENCES cgs_greenspace (greenspace_id),

    CONSTRAINT cgs_plot_zone_fk
        FOREIGN KEY (zone_code)
        REFERENCES cgs_data_zone (zone_code)
);


-- 5. TREES
-- Each tree belongs to a plot.
-- Plot ID and tree number together identify a tree record.

CREATE TABLE cgs_tree (
    plot_id VARCHAR2(30),
    tree_no NUMBER,
    species VARCHAR2(150),
    dbh_cm NUMBER CHECK (dbh_cm > 0),
    height_m NUMBER CHECK (height_m > 0),
    notes VARCHAR2(500),

    CONSTRAINT cgs_tree_pk
        PRIMARY KEY (plot_id, tree_no),

    CONSTRAINT cgs_tree_plot_fk
        FOREIGN KEY (plot_id)
        REFERENCES cgs_field_plot (plot_id)
);


-- 6. GREENSPACE CARBON RESULTS
-- One carbon result per greenspace.
-- Units to be confirmed?

CREATE TABLE cgs_site_carbon (
    greenspace_id VARCHAR2(100) PRIMARY KEY,
    carbon_stock_kg_carbon NUMBER
        CHECK (carbon_stock_kg_carbon >= 0),

    CONSTRAINT cgs_carbon_site_fk
        FOREIGN KEY (greenspace_id)
        REFERENCES cgs_greenspace (greenspace_id)
);


-- EXAMPLE DATA

INSERT INTO cgs_data_zone (zone_code, zone_name)
VALUES ('TEST_ZONE_01', 'Fictional neighbourhood');

INSERT INTO cgs_envdep_result (
    zone_code, canopy_pct, index_score, dep_class
)
VALUES ('TEST_ZONE_01', 25, 0.65, 'High');

INSERT INTO cgs_greenspace (
    greenspace_id, site_name, site_type, area_m2
)
VALUES ('TEST_GS01', 'Fictional Park', 'Public park', 10000);

INSERT INTO cgs_field_plot (
    plot_id, greenspace_id, zone_code, radius_m
)
VALUES ('TEST_PLOT01', 'TEST_GS01', 'TEST_ZONE_01', 11.3);

INSERT INTO cgs_tree (
    plot_id, tree_no, species, dbh_cm, height_m
)
VALUES ('TEST_PLOT01', 1, 'Example species', 30, 15);

INSERT INTO cgs_site_carbon (
    greenspace_id, carbon_stock_kg_carbon
)
VALUES ('TEST_GS01', 2500);

COMMIT;


-- EXAMPLE QUERY
-- Shows a greenspace, its plot and tree, the plot's environmental class and the greenspace carbon result.

SELECT
    g.site_name,
    p.plot_id,
    t.tree_no,
    t.species,
    t.dbh_cm,
    t.height_m,
    e.dep_class,
    c.carbon_stock_kg_carbon
FROM cgs_greenspace g
JOIN cgs_field_plot p
    ON g.greenspace_id = p.greenspace_id
JOIN cgs_tree t
    ON p.plot_id = t.plot_id
JOIN cgs_envdep_result e
    ON p.zone_code = e.zone_code
JOIN cgs_site_carbon c
    ON g.greenspace_id = c.greenspace_id;
