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
CREATE OR REPLACE FUNCTION get_product_assembly_summary(
    p_start_date DATE,
    p_end_date   DATE
)
RETURNS TABLE(
    agg_level      TEXT,
    workshop       VARCHAR,
    section        VARCHAR,
    category       VARCHAR,
    product_count  BIGINT,
    product_list   TEXT[]
)
LANGUAGE plpgsql
AS $$
BEGIN
RETURN QUERY
WITH base AS (
    SELECT
        p.p_id,
        p.name AS product_name,
        p.workshop_id AS wsh_id,
        a.section_id AS section_id,
        p.category AS category_id
    FROM products p
    JOIN assembly a
      ON p.p_id = a.product_id
    WHERE p.end_date BETWEEN p_start_date AND p_end_date
)
SELECT
    CASE
        WHEN GROUPING(w.wsh_id)=1 AND GROUPING(section_id)=1 AND GROUPING(category_id)=1
            THEN 'enterprise_total'
        WHEN GROUPING(w.wsh_id)=1 AND GROUPING(section_id)=1 AND GROUPING(category_id)=0
            THEN 'enterprise_by_category'
        WHEN GROUPING(w.wsh_id)=0 AND GROUPING(section_id)=1 AND GROUPING(category_id)=1
            THEN 'workshop_total'
        WHEN GROUPING(w.wsh_id)=0 AND GROUPING(section_id)=1 AND GROUPING(category_id)=0
            THEN 'workshop_by_category'
        WHEN GROUPING(w.wsh_id)=0 AND GROUPING(section_id)=0 AND GROUPING(category_id)=1
          THEN 'section_total'
        ELSE 'section_by_category'
    END AS agg_level,

    MIN(w.name)::VARCHAR AS workshop,
    MIN(s.name)::VARCHAR AS section,
    MIN(c.name)::VARCHAR AS category,

    COUNT(DISTINCT b.p_id) AS product_count,
    ARRAY_AGG(DISTINCT b.product_name ORDER BY b.product_name) AS product_list

FROM base b
LEFT JOIN workshops w ON b.wsh_id = w.wsh_id
LEFT JOIN sections s ON b.section_id = s.s_id
LEFT JOIN product_categories c ON b.category_id = c.c_id

GROUP BY
    GROUPING SETS (
       -- section by category
        (w.wsh_id, section_id, category_id),
        -- section total
        (w.wsh_id, section_id),
        -- workshop by category
        (w.wsh_id, category_id),
        -- workshop total
        (w.wsh_id),
        -- enterprise by category
        (category_id),
        -- enterprise total
        ()
    )

ORDER BY
    CASE
        WHEN GROUPING(w.wsh_id)=1 AND GROUPING(section_id)=1 AND GROUPING(category_id)=1 THEN 1  -- enterprise_total
        WHEN GROUPING(w.wsh_id)=1 AND GROUPING(section_id)=1 AND GROUPING(category_id)=0 THEN 2  -- enterprise_by_category
        WHEN GROUPING(w.wsh_id)=0 AND GROUPING(section_id)=1 AND GROUPING(category_id)=1 THEN 3  -- workshop_total
        WHEN GROUPING(w.wsh_id)=0 AND GROUPING(section_id)=1 AND GROUPING(category_id)=0 THEN 4  -- workshop_by_category
        WHEN GROUPING(w.wsh_id)=0 AND GROUPING(section_id)=0 AND GROUPING(category_id)=1 THEN 5  -- section_total
        ELSE 6                                                                             -- section_by_category
    END,
    w.wsh_id, section_id, category_id;
END;
$$;


-- 3) Получить данные о кадровом составе цеха, предприятия в целом и по указанным категориям инженерно-технического персонала и рабочих.
CREATE OR REPLACE VIEW v_staff_composition AS
SELECT
    e.w_id,
    e.full_name,
    e.hire_date,
    e.leave_date,
    e.worker_type,
    wt.name AS worker_type_name,
    et.education,
    et.is_master,
    et.is_wsh_super,
    et.section AS section_id,

    sec.name AS section_name,
    sec.workshop_id,
    wsh.name AS workshop_name,

    w.brigade_id,
    w.specialisation
FROM Employees e
JOIN worker_types wt ON e.worker_type = wt.tp_id

LEFT JOIN ete et ON e.w_id = et.w_id
LEFT JOIN sections sec ON et.section = sec.s_id
LEFT JOIN workshops wsh ON sec.workshop_id = wsh.wsh_id

LEFT JOIN workers w ON e.w_id = w.w_id;


-- 4) Получить число и перечень участков указанного цеха, предприятия в целом и их начальников.
CREATE OR REPLACE VIEW v_sections_and_chiefs_summary AS
WITH
    -- 1) sections per workshop
    section_aggr AS (
        SELECT
            workshop_id,
            COUNT(*)                            AS section_count,
            ARRAY_AGG(name ORDER BY name)       AS section_list
        FROM sections
        GROUP BY workshop_id
    ),

    -- 2) workshop-chiefs per workshop
    chief_aggr AS (
        SELECT
            sec.workshop_id,
            ARRAY_AGG(DISTINCT e.full_name
                      ORDER BY e.full_name)    AS chief_list
        FROM ete t
        JOIN sections sec
            ON t.section = sec.s_id
           AND t.is_wsh_super = TRUE
        JOIN employees e
            ON t.w_id = e.w_id
        GROUP BY sec.workshop_id
    ),

    -- 3) all workshops + one enterprise row
    all_ws AS (
        SELECT
            wsh_id,
            name
        FROM workshops

        UNION ALL

        -- enterprise (NULL workshop_id) row
        SELECT
            NULL::INT    AS wsh_id,
            'Enterprise' AS name
    )

SELECT
    w.wsh_id,
    w.name             AS workshop_name,

    COALESCE(sa.section_count, 0)            AS section_count,
    COALESCE(sa.section_list, '{}'::TEXT[])  AS section_list,

    COALESCE(ca.chief_list, '{}'::TEXT[])    AS chief_list

FROM all_ws w

LEFT JOIN section_aggr sa
    ON sa.workshop_id = w.wsh_id

LEFT JOIN chief_aggr ca
    ON ca.workshop_id = w.wsh_id

ORDER BY
    -- Enterprise first (wsh_id NULL), then by wsh_id
    CASE WHEN w.wsh_id IS NULL THEN 0 ELSE 1 END,
    w.wsh_id;


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
JOIN Brigade b ON a.brigade_id = b.b_id
JOIN Sections s ON a.section_id = s.s_id
JOIN Work_types wt ON a.work_type = wt.t_id;

-- 6) Получить состав бригад указанного участка, цеха.
CREATE OR REPLACE VIEW v_brigade_composition AS
SELECT DISTINCT
    s.s_id AS section_id,
    s.name AS section_name,
    wsh.wsh_id AS workshop_id,
    wsh.name AS workshop_name,
    b.b_id AS brigade_id,
    b.name AS brigade_name,
    e.w_id AS worker_id,
    e.full_name AS worker_name,
    wt.name AS specialisation,
    w.is_brigadier AS is_brigadier
FROM workers w
JOIN employees e ON w.w_id = e.w_id
JOIN work_types wt ON w.specialisation = wt.t_id
JOIN brigade b ON w.brigade_id = b.b_id
/* infer which sections this brigade has worked in */
JOIN (
    SELECT DISTINCT brigade_id, section_id
    FROM assembly
) AS ab ON ab.brigade_id = b.b_id
JOIN sections s ON ab.section_id = s.s_id
JOIN workshops wsh ON s.workshop_id = wsh.wsh_id;


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
SELECT DISTINCT
    p.p_id AS product_id,
    p.name AS product_name,
    p.category AS category_id,
    pc.name AS category_name,
    s.s_id AS section_id,
    s.name AS section_name,
    w.wsh_id AS workshop_id,
    w.name AS workshop_name
FROM products p
JOIN product_categories pc ON p.category = pc.c_id

JOIN assembly a ON a.product_id = p.p_id AND a.end_date IS NULL

JOIN sections s ON a.section_id = s.s_id
JOIN workshops w ON s.workshop_id = w.wsh_id;


-- 9) Получить состав бригад, участвующих в сборке указанного изделия.
CREATE OR REPLACE VIEW v_product_brigade_composition AS
WITH prod_brigade AS (
    -- Deduplicate so each (product, brigade) appears only once
    SELECT DISTINCT
        product_id,
        brigade_id
    FROM assembly
)
SELECT
    pb.product_id,
    p.name AS product_name,
    pb.brigade_id,
    b.name AS brigade_name,
    w.w_id AS worker_id,
    e.full_name AS worker_name,
    wt.name AS specialisation,
    w.is_brigadier
FROM prod_brigade pb
JOIN products p ON p.p_id = pb.product_id
JOIN brigade b ON b.b_id = pb.brigade_id
JOIN workers w ON w.brigade_id = b.b_id
JOIN employees e ON e.w_id = w.w_id
JOIN work_types wt ON wt.t_id = w.specialisation


-- 10) Получить перечень испытательных лабораторий, участвующих в испытаниях некоторого конкретного изделия.
CREATE OR REPLACE VIEW v_product_test_labs AS
SELECT DISTINCT
    t.product_id,
    p.name AS product_name,
    t.lab_id,
    l.name AS lab_name
FROM Test t
JOIN Products p ON t.product_id = p.p_id
JOIN Labs l ON t.lab_id = l.l_id;

-- 11) Получить перечень изделий отдельной категории и в целом, проходивших испытание в указанной лаборатории за определенный период.
CREATE OR REPLACE VIEW v_lab_tested_products AS
SELECT DISTINCT
    t.lab_id,
    l.name AS lab_name,
    p.category AS category_id,
    pc.name AS category_name,
    p.p_id AS product_id,
    p.name AS product_name,
    t.test_date
FROM test t
JOIN products p ON t.product_id = p.p_id
JOIN product_categories pc ON p.category = pc.c_id
JOIN labs l ON t.lab_id = l.l_id;


-- 12) Получить список испытателей, участвующих в испытаниях указанного изделия, изделий отдельной категории и в целом в некоторой лаборатории за определенный период.
CREATE OR REPLACE VIEW v_testers_activity AS
SELECT
    tt.test_id,
    t.product_id,
    p.name AS product_name,
    p.category AS category_id,
    pc.name AS category_name,
    t.lab_id,
    l.name AS lab_name,
    tt.tw_id AS tester_w_id,
    e.full_name AS tester_name,
    t.test_date
FROM test_testers tt
JOIN test t ON tt.test_id = t.t_id
JOIN products p ON t.product_id = p.p_id
JOIN product_categories pc ON p.category = pc.c_id
JOIN labs l ON t.lab_id = l.l_id
JOIN employees e ON tt.tw_id = e.w_id;


-- 13) Получить состав оборудования, использовавшегося при испытании указанного изделия, изделий отдельной категории и в целом в некоторой лаборатории за определенный период.
CREATE OR REPLACE VIEW v_equipment_usage AS
SELECT
    t.t_id AS test_id,
    t.product_id,
    p.name AS product_name,
    p.category AS category_id,
    pc.name AS category_name,
    t.lab_id,
    l.name AS lab_name,
    t.equipment_id,
    eq.name AS equipment_name,
    t.test_date
FROM test t
JOIN products p ON t.product_id = p.p_id
JOIN labs l ON t.lab_id = l.l_id
JOIN product_categories pc ON p.category = pc.c_id
LEFT JOIN equipment eq ON t.equipment_id = eq.e_id;

-- 14) Получить число и перечень изделий отдельной категории и в целом, собираемых указанным цехом, участком, предприятием в целом в настоящее время.
CREATE OR REPLACE VIEW v_ongoing_product_counts AS
SELECT
    w.name AS workshop_name,
    s.name AS section_name,
    pc.name AS category_name,
    COUNT(DISTINCT p.p_id) AS product_count,
    ARRAY_AGG(DISTINCT p.name) AS product_names

FROM assembly AS a
JOIN products AS p ON a.product_id = p.p_id
JOIN product_categories AS pc ON p.category = pc.c_id
JOIN sections AS s ON a.section_id = s.s_id
JOIN workshops AS w ON s.workshop_id = w.wsh_id

WHERE p.end_date IS NULL

GROUP BY ROLLUP (w.name, s.name, pc.name);

