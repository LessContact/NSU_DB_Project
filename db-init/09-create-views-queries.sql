\connect aerospace_factory

-- 1) Получить перечень видов изделий отдельной категории и в целом, собираемых указанным цехом, предприятием.
CREATE OR REPLACE VIEW v_product_types AS
SELECT 
    p.name AS product_name,
    pc.name AS category_name,
    w.name AS workshop_name
FROM products p
JOIN product_categories pc ON p.category = pc.c_id
JOIN workshops w ON p.workshop_id = w.wsh_id;

-- 2) Получить число и перечень изделий отдельной категории и в целом, собранных указанным цехом, участком, предприятием в целом за определенный отрезок времени.
CREATE OR REPLACE VIEW v_products_assembled AS
SELECT
    a.section_id,
    s.name AS section_name,
    a.product_id,
    p.name AS product_name,
    p.category,
    a.brigade_id,
    COUNT(*) OVER (PARTITION BY a.section_id, p.category) AS cnt_by_section_category,
    COUNT(*) OVER (PARTITION BY a.section_id) AS cnt_by_section,
    COUNT(*) OVER (PARTITION BY p.category) AS cnt_by_category,
    COUNT(*) OVER () AS cnt_total,
    a.begin_date,
    a.end_date
FROM Assembly a
JOIN Products p ON a.product_id = p.p_id
JOIN Sections s ON a.section_id = s.s_id;

-- 3) Получить данные о кадровом составе цеха, предприятия в целом и по указанным категориям инженерно-технического персонала и рабочих.
CREATE OR REPLACE VIEW v_staff_composition AS
SELECT
    e.w_id,
    e.full_name,
    e.worker_type,
    wt.name AS worker_type_name,
    e.hire_date,
    e.leave_date,
    et.education,
    et.is_master,
    et.is_wsh_super,
    t.brigade_id,
    t.specialisation
FROM Employees e
JOIN Worker_types wt ON e.worker_type = wt.tp_id
LEFT JOIN ETE et ON e.w_id = et.w_id
LEFT JOIN Workers t ON e.w_id = t.w_id;

-- 4) Получить число и перечень участков указанного цеха, предприятия в целом и их начальников.
CREATE OR REPLACE VIEW v_sections_and_chiefs AS
SELECT
    s.s_id,
    s.name AS section_name,
    s.workshop_id,
    w.name AS workshop_name,
    m.w_id AS master_w_id,
    e.full_name AS master_name
FROM Sections s
JOIN Workshops w ON s.workshop_id = w.wsh_id
LEFT JOIN Masters m ON s.s_id = m.s_id
LEFT JOIN Employees e ON m.w_id = e.w_id;

-- 5) Получить перечень работ, которые проходит указанное изделие.
CREATE OR REPLACE VIEW v_product_assembly_history AS
SELECT
    p.p_id,
    p.name AS product_name,
    a.a_id,
    a.brigade_id,
    b.name AS brigade_name,
    a.section_id,
    s.name AS section_name,
    a.begin_date,
    a.end_date,
    wt.name AS work_type_name,
    a.description
FROM Assembly a
JOIN Products p ON a.product_id = p.p_id
LEFT JOIN Brigade b ON a.brigade_id = b.b_id
LEFT JOIN Sections s ON a.section_id = s.s_id
LEFT JOIN Work_types wt ON a.work_type = wt.t_id;

-- 6) Получить состав бригад указанного участка, цеха.
CREATE OR REPLACE VIEW v_brigade_composition AS
SELECT 
    s.name AS section_name,
    w.name AS workshop_name,
    b.name AS brigade_name,
    e.full_name AS worker_name,
    wt.name AS specialisation,
    w1.is_brigadier
FROM workers w1
JOIN employees e ON w1.w_id = e.w_id
JOIN worker_types wt ON w1.specialisation = wt.tp_id
JOIN brigade b ON w1.brigade_id = b.b_id
JOIN assembly a ON a.brigade_id = b.b_id
JOIN sections s ON a.section_id = s.s_id
JOIN workshops w ON s.workshop_id = w.wsh_id;

-- 7) Получить список мастеров указанного участка, цеха.
CREATE OR REPLACE VIEW v_section_masters AS
SELECT
    m.s_id,
    s.name AS section_name,
    s.workshop_id AS workshop_id,
    w.name AS workshop_name,
    m.w_id AS master_id,
    e.full_name AS master_name
FROM Masters m
JOIN Sections s ON m.s_id = s.s_id
JOIN Workshops w ON s.workshop_id = w.wsh_id
JOIN Employees e ON m.w_id = e.w_id;

-- 8) Получить перечень изделий отдельной категории и в целом, собираемых в настоящий момент указанным участком, цехом, предприятием.
CREATE OR REPLACE VIEW v_currently_assembling AS
SELECT
    a.a_id,
    p.p_id AS product_id,
    p.name AS product_name,
    p.category,
    a.section_id,
    s.name AS section_name,
    s.workshop_id AS workshop_id,
    w.name AS workshop_name,
    a.brigade_id,
    b.name AS brigade_name,
    a.begin_date
FROM Assembly a
JOIN Products p ON a.product_id = p.p_id
JOIN Sections s ON a.section_id = s.s_id
JOIN Workshops w ON s.workshop_id = w.wsh_id
JOIN Brigade b ON a.brigade_id = b.b_id
WHERE a.end_date IS NULL;

-- 9) Получить состав бригад, участвующих в сборке указанного изделия.
CREATE OR REPLACE VIEW v_product_brigades AS
SELECT DISTINCT
    a.product_id,
    p.name AS product_name,
    a.brigade_id,
    b.name AS brigade_name
FROM Assembly a
JOIN Products p ON a.product_id = p.p_id
JOIN Brigade b ON a.brigade_id = b.b_id;

-- 10) Получить перечень испытательных лабораторий, участвующих в испытаниях некоторого конкретного изделия.
CREATE OR REPLACE VIEW v_product_test_labs AS
SELECT DISTINCT
    t.product_id,
    p.name AS product_name,
    t.lab_id,
    l.name AS lab_name,
    t.test_date
FROM Test t
JOIN Products p ON t.product_id = p.p_id
JOIN Labs l ON t.lab_id = l.l_id;

-- 11) Получить перечень изделий отдельной категории и в целом, проходивших испытание в указанной лаборатории за определенный период.
CREATE OR REPLACE VIEW v_lab_tests AS
SELECT
    t.lab_id,
    l.name AS lab_name,
    p.p_id,
    p.name AS product_name,
    p.category,
    t.test_date
FROM Test t
JOIN Products p ON t.product_id = p.p_id
JOIN Labs l ON t.lab_id = l.l_id;

-- 12) Получить список испытателей, участвующих в испытаниях указанного изделия, изделий отдельной категории и в целом в некоторой лаборатории за определенный период.
CREATE OR REPLACE VIEW v_testers_activity AS
SELECT
    tt.test_id,
    t.product_id,
    p.name AS product_name,
    p.category,
    t.lab_id,
    l.name AS lab_name,
    tt.tw_id AS tester_w_id,
    e.full_name AS tester_name,
    t.test_date
FROM Test_Testers tt
JOIN Test t ON tt.test_id = t.t_id
JOIN Products p ON t.product_id = p.p_id
JOIN Labs l ON t.lab_id = l.l_id
JOIN Employees e ON tt.tw_id = e.w_id;

-- 13) Получить состав оборудования, использовавшегося при испытании указанного изделия, изделий отдельной категории и в целом в некоторой лаборатории за определенный период.
CREATE OR REPLACE VIEW v_equipment_usage AS
SELECT
    t.t_id AS test_id,
    t.product_id,
    p.name AS product_name,
    p.category,
    t.lab_id,
    l.name AS lab_name,
    t.equipment_id,
    eq.name AS equipment_name,
    t.test_date
FROM Test t
JOIN Products p ON t.product_id = p.p_id
JOIN Labs l ON t.lab_id = l.l_id
LEFT JOIN Equipment eq ON t.equipment_id = eq.e_id;

-- 14) Получить число и перечень изделий отдельной категории и в целом, собираемых указанным цехом, участком, предприятием в целом в настоящее время.
CREATE OR REPLACE VIEW v_ongoing_product_counts AS
SELECT 
    w.name AS workshop_name,
    s.name AS section_name,
    pc.name AS category_name,
    COUNT(DISTINCT p.p_id) AS product_count,
    array_agg(DISTINCT p.name) AS product_names
FROM assembly a
JOIN products p ON a.product_id = p.p_id
JOIN product_categories pc ON p.category = pc.c_id
JOIN sections s ON a.section_id = s.s_id
JOIN workshops w ON s.workshop_id = w.wsh_id
WHERE a.end_date IS NULL OR a.end_date >= CURRENT_DATE
GROUP BY w.name, s.name, pc.name;
