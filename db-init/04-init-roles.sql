\connect aerospace_factory

GRANT SELECT, INSERT, UPDATE, DELETE
    ON TABLE
        "employees",
        "workers",
        "ete",
        "grades",
        "work_types",
        "worker_types",
        "masters",
        "brigade"
    TO HR;

GRANT SELECT, INSERT
    ON TABLE
        "employee_movements"
    TO HR;


GRANT SELECT, INSERT, UPDATE, DELETE
    ON TABLE
        "equipment"
    TO Testers;

GRANT SELECT, INSERT
    ON TABLE
        "test"
    TO Testers;

GRANT SELECT
    ON TABLE
        "labs",
        "testers"
    TO Testers;


GRANT SELECT, INSERT, UPDATE, DELETE
    ON TABLE
        "products",
        "vehicles",
        "missiles",
        "other",
        "assembly",
        "product_categories"
    TO Workshop_manager;
