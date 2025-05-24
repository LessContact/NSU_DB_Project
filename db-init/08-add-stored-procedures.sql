\connect aerospace_factory

CREATE OR REPLACE PROCEDURE sp_add_employee(
    p_full_name VARCHAR(255),
    p_worker_type INTEGER,
    p_experience INTEGER,
    p_grade_id INTEGER,
    p_hire_date DATE DEFAULT CURRENT_DATE,
    -- Parameters for Workers
    p_brigade_id INTEGER DEFAULT NULL,
    p_specialisation INTEGER DEFAULT NULL,
    p_is_brigadier BOOLEAN DEFAULT FALSE,
    -- Parameters for ETE (Engineers, Technicians, Executives)
    p_education VARCHAR(255) DEFAULT NULL,
    p_is_wsh_super BOOLEAN DEFAULT FALSE,
    p_is_master BOOLEAN DEFAULT FALSE,
    p_section INTEGER DEFAULT NULL,
    -- Parameters for Testers
    p_lab_id INTEGER DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_employee_id INTEGER;
    v_worker_type_name VARCHAR(255);
BEGIN
    
    SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;

    -- Get the worker type name
    SELECT name INTO v_worker_type_name
    FROM worker_types
    WHERE tp_id = p_worker_type
    FOR SHARE;

    IF v_worker_type_name IS NULL THEN
        RAISE EXCEPTION 'Invalid worker type ID: %', p_worker_type;
    END IF;

    PERFORM 1 FROM grades 
    WHERE g_id = p_grade_id 
    FOR SHARE;

    -- Insert the employee record
    INSERT INTO employees (
        full_name, 
        hire_date, 
        worker_type, 
        experience, 
        grade_id
    )
    VALUES (
        p_full_name, 
        p_hire_date, 
        p_worker_type, 
        p_experience, 
        p_grade_id
    )
    RETURNING w_id INTO v_employee_id;
    
    -- Insert into subtype based on worker type
    IF v_worker_type_name = 'Worker' THEN
        IF p_specialisation IS NULL THEN
            ROLLBACK;
            RAISE EXCEPTION 'Specialisation is required for workers';
        END IF;
        
        IF p_brigade_id IS NOT NULL THEN
            PERFORM 1 FROM brigade 
            WHERE b_id = p_brigade_id 
            FOR SHARE;
            
            -- There is a trigger, but we should make it one transaction to allow correct concurrent access
            IF p_is_brigadier = true THEN
                IF EXISTS (
                    SELECT 1 
                    FROM workers 
                    WHERE brigade_id = p_brigade_id 
                    AND is_brigadier = true
                    FOR UPDATE
                ) THEN
                    ROLLBACK;
                    RAISE EXCEPTION 'Brigade % already has a brigadier', p_brigade_id;
                END IF;
            END IF;
        END IF;
        
        INSERT INTO workers (
            w_id,
            brigade_id,
            specialisation,
            is_brigadier
        )
        VALUES (
            v_employee_id,
            p_brigade_id,
            p_specialisation,
            p_is_brigadier
        );
        
    ELSIF v_worker_type_name = 'ETE' THEN
        IF p_education IS NULL THEN
            ROLLBACK;
            RAISE EXCEPTION 'Education is required for ETE employees';
        END IF;
        
        IF p_specialisation IS NULL THEN
            ROLLBACK;
            RAISE EXCEPTION 'Specialisation is required for ETE employees';
        END IF;

        IF p_section IS NOT NULL THEN
            PERFORM 1 FROM sections 
            WHERE s_id = p_section 
            FOR SHARE;
        END IF;
        
        INSERT INTO ete (
            w_id,
            specialisation,
            education,
            is_wsh_super,
            is_master,
            section
        )
        VALUES (
            v_employee_id,
            p_specialisation,
            p_education,
            p_is_wsh_super,
            p_is_master,
            p_section
        );
        
    ELSIF v_worker_type_name = 'Tester' THEN
        IF p_lab_id IS NULL THEN
            ROLLBACK;
            RAISE EXCEPTION 'Lab ID is required for testers';
        END IF;
        
        PERFORM 1 FROM labs 
        WHERE l_id = p_lab_id 
        FOR SHARE;
        
        INSERT INTO testers (
            w_id,
            l_id
        )
        VALUES (
            v_employee_id,
            p_lab_id
        );
        
    ELSE
        RAISE EXCEPTION 'Unsupported worker type: %', v_worker_type_name;
    END IF;
    
    RAISE NOTICE 'Employee % added successfully with ID %', p_full_name, v_employee_id;
    COMMIT;
END;
$$;


CREATE OR REPLACE PROCEDURE sp_remove_employee(
    p_employee_id INTEGER
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_worker_type_name VARCHAR(255);
    v_employee_name VARCHAR(255);
BEGIN
    
    SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;

    -- Check if employee exists
    SELECT full_name, wt.name 
    INTO v_employee_name, v_worker_type_name
    FROM employees e
    JOIN worker_types wt ON e.worker_type = wt.tp_id
    WHERE e.w_id = p_employee_id
    FOR UPDATE;
    
    IF v_employee_name IS NULL THEN
        ROLLBACK;
        RAISE EXCEPTION 'Employee with ID % not found', p_employee_id;
    END IF;

    -- There is a trigger, but we should make it one transaction to allow correct concurrent access
    IF EXISTS (
        SELECT 1 
        FROM masters 
        WHERE w_id = p_employee_id
        FOR UPDATE
    ) THEN
        ROLLBACK;
        RAISE EXCEPTION 'Cannot delete employee % who is an active master', p_employee_id;
    END IF;
    
    -- Delete the employee, cascades to subtype table
    DELETE FROM employees WHERE w_id = p_employee_id;
    
    RAISE NOTICE 'Employee % removed successfully', v_employee_name;
    COMMIT;
END;
$$;


CREATE OR REPLACE PROCEDURE sp_add_product(
    p_name VARCHAR(255),
    p_category INTEGER,
    p_workshop_id INTEGER,
    p_begin_date DATE DEFAULT CURRENT_DATE,
    -- Parameters for Vehicle
    p_product_type VARCHAR(50) DEFAULT NULL,
    p_use_type VARCHAR(50) DEFAULT NULL,
    p_vehicle_type VARCHAR(50) DEFAULT NULL,
    p_cargo_cap INTEGER DEFAULT NULL,
    p_pass_count INTEGER DEFAULT NULL,
    p_eng_count INTEGER DEFAULT NULL,
    p_armaments VARCHAR(255) DEFAULT NULL,
    -- Parameters for Missile
    p_missile_type VARCHAR(50) DEFAULT NULL,
    p_payload INTEGER DEFAULT NULL,
    p_range INTEGER DEFAULT NULL,
    -- Parameters for Other
    p_text_specification TEXT DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_product_id INTEGER;
BEGIN
    
    SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;

    PERFORM 1 FROM product_categories 
    WHERE c_id = p_category 
    FOR SHARE;
    
    PERFORM 1 FROM workshops 
    WHERE wsh_id = p_workshop_id 
    FOR SHARE;

    -- Insert into products table
    INSERT INTO products (
        name,
        category,
        begin_date,
        workshop_id
    )
    VALUES (
        p_name,
        p_category,
        p_begin_date,
        p_workshop_id
    )
    RETURNING p_id INTO v_product_id;
    
    -- Insert into appropriate subtype based on product type
    IF p_product_type = 'vehicle' THEN
        IF p_use_type IS NULL OR p_vehicle_type IS NULL THEN
            ROLLBACK;
            RAISE EXCEPTION 'Use type and vehicle type are required for vehicles';
        END IF;
        
        INSERT INTO vehicles (
            p_id,
            use_type,
            vehicle_type,
            cargo_cap,
            pass_count,
            eng_count,
            armaments
        )
        VALUES (
            v_product_id,
            p_use_type,
            p_vehicle_type,
            p_cargo_cap,
            p_pass_count,
            p_eng_count,
            p_armaments
        );
        
    ELSIF p_product_type = 'missile' THEN
        IF p_missile_type IS NULL THEN
            ROLLBACK;
            RAISE EXCEPTION 'Missile type is required for missiles';
        END IF;
        
        INSERT INTO missiles (
            p_id,
            type,
            payload,
            range
        )
        VALUES (
            v_product_id,
            p_missile_type,
            p_payload,
            p_range
        );
        
    ELSIF p_product_type = 'other' THEN
        IF p_text_specification IS NULL THEN
            ROLLBACK;
            RAISE EXCEPTION 'Text specification is required for other products';
        END IF;
        
        INSERT INTO other (
            p_id,
            text_specification
        )
        VALUES (
            v_product_id,
            p_text_specification
        );
        
    ELSE
        ROLLBACK;
        RAISE EXCEPTION 'Invalid product type: %. Must be "vehicle", "missile", or "other"', p_product_type;
    END IF;
    
    RAISE NOTICE 'Product % added successfully with ID %', p_name, v_product_id;
    COMMIT;
END;
$$;


