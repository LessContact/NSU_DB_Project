\connect aerospace_factory


COPY "product_categories" (name)
    FROM '/csv-data/product_categories.csv'
    WITH (FORMAT csv, HEADER true, DELIMITER ',', ENCODING 'UTF8');

COPY "workshops" (name, location)
    FROM '/csv-data/workshops.csv'
    WITH (FORMAT csv, HEADER true, DELIMITER ',', ENCODING 'UTF8');

COPY "labs" (name, location)
    FROM '/csv-data/labs.csv'
    WITH (FORMAT csv, HEADER true, DELIMITER ',', ENCODING 'UTF8');

COPY "workshop_labs" (wsh_id, l_id)
    FROM '/csv-data/workshop_labs.csv'
    WITH (FORMAT csv, HEADER true, DELIMITER ',', ENCODING 'UTF8');

COPY "sections" (name, workshop_id)
    FROM '/csv-data/sections.csv'
    WITH (FORMAT csv, HEADER true, DELIMITER ',', ENCODING 'UTF8');

COPY "grades" (grade_title, payment)
    FROM '/csv-data/grades.csv'
    WITH (FORMAT csv, HEADER true, DELIMITER ',', ENCODING 'UTF8');

COPY "work_types" (name)
    FROM '/csv-data/work_types.csv'
    WITH (FORMAT csv, HEADER true, DELIMITER ',', ENCODING 'UTF8');

COPY "worker_types" (name)
    FROM '/csv-data/worker_types.csv'
    WITH (FORMAT csv, HEADER true, DELIMITER ',', ENCODING 'UTF8');

COPY "employees" (full_name, hire_date, leave_date, worker_type, experience, grade_id)
    FROM '/csv-data/employees.csv'
    WITH (FORMAT csv, HEADER true, DELIMITER ',', ENCODING 'UTF8');

COPY "brigade" (name)
    FROM '/csv-data/brigade.csv'
    WITH (FORMAT csv, HEADER true, DELIMITER ',', ENCODING 'UTF8');

COPY "workers" (w_id, brigade_id, specialisation, is_brigadier)
    FROM '/csv-data/workers.csv'
    WITH (FORMAT csv, HEADER true, DELIMITER ',', ENCODING 'UTF8');

COPY "ete" (w_id, specialisation, education, is_wsh_super, is_master, section)
    FROM '/csv-data/ete.csv'
    WITH (FORMAT csv, HEADER true, DELIMITER ',', ENCODING 'UTF8');

COPY "employee_movements" (w_id, move_date, old_pos, new_pos, comment)
    FROM '/csv-data/employee_movements.csv'
    WITH (FORMAT csv, HEADER true, DELIMITER ',', ENCODING 'UTF8');

COPY "products" (name, category, begin_date, end_date, workshop_id)
    FROM '/csv-data/products.csv'
    WITH (FORMAT csv, HEADER true, DELIMITER ',', ENCODING 'UTF8');

COPY "vehicles" (p_id, use_type, vehicle_type, cargo_cap, pass_count, eng_count, armaments)
    FROM '/csv-data/vehicles.csv'
    WITH (FORMAT csv, HEADER true, DELIMITER ',', ENCODING 'UTF8');

COPY "missiles" (p_id, type, payload, range)
    FROM '/csv-data/missiles.csv'
    WITH (FORMAT csv, HEADER true, DELIMITER ',', ENCODING 'UTF8');

COPY "other" (p_id, text_specification)
    FROM '/csv-data/other.csv'
    WITH (FORMAT csv, HEADER true, DELIMITER ',', ENCODING 'UTF8');

COPY "masters" (w_id, s_id)
    FROM '/csv-data/masters.csv'
    WITH (FORMAT csv, HEADER true, DELIMITER ',', ENCODING 'UTF8');

COPY "assembly" (brigade_id, section_id, product_id, begin_date, end_date, work_type, description)
    FROM '/csv-data/assembly.csv'
    WITH (FORMAT csv, HEADER true, DELIMITER ',', ENCODING 'UTF8');

COPY "equipment" (l_id, name, type)
    FROM '/csv-data/equipment.csv'
    WITH (FORMAT csv, HEADER true, DELIMITER ',', ENCODING 'UTF8');

COPY "testers" (w_id, l_id)
    FROM '/csv-data/testers.csv'
    WITH (FORMAT csv, HEADER true, DELIMITER ',', ENCODING 'UTF8');

COPY "test" (product_id, lab_id, test_date, result, equipment_id)
    FROM '/csv-data/test.csv'
    WITH (FORMAT csv, HEADER true, DELIMITER ',', ENCODING 'UTF8');

COPY "test_testers" (test_id, tw_id)
    FROM '/csv-data/test_testers.csv'
    WITH (FORMAT csv, HEADER true, DELIMITER ',', ENCODING 'UTF8');

COPY "sections_products" (s_id, p_id)
    FROM '/csv-data/sections_products.csv'
    WITH (FORMAT csv, HEADER true, DELIMITER ',', ENCODING 'UTF8');

