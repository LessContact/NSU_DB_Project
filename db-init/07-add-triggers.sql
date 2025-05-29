\connect aerospace_factory
-- 1)
CREATE OR REPLACE FUNCTION log_employee_grade_change_func()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.grade_id <> NEW.grade_id THEN
        INSERT INTO employee_movements(w_id, old_pos, new_pos)
        VALUES(NEW.w_id, OLD.grade_id, NEW.grade_id);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER log_employee_grade_change
AFTER UPDATE OF grade_id ON employees
FOR EACH ROW
EXECUTE FUNCTION log_employee_grade_change_func();

-- 2)
CREATE OR REPLACE FUNCTION validate_master_employee_func()
RETURNS TRIGGER AS $$
BEGIN
    -- Check if the employee doesnt exist in ete table and is marked as master
    IF NOT EXISTS (
        SELECT 1 
        FROM ete
        WHERE w_id = NEW.w_id 
        AND is_master = true
    ) THEN
        RAISE EXCEPTION 'Employee % must be in the ETE table and marked as master to be added as a section master', NEW.w_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER validate_master_employee
BEFORE INSERT OR UPDATE ON masters
FOR EACH ROW
EXECUTE FUNCTION validate_master_employee_func();

-- 3)
CREATE OR REPLACE FUNCTION prevent_delete_active_master_func()
RETURNS TRIGGER AS $$
BEGIN
    -- Check if the employee is an active master
    IF EXISTS (
        SELECT 1 FROM masters WHERE w_id = OLD.w_id
    ) THEN
        RAISE EXCEPTION 'Cannot delete employee % who is an active master', OLD.w_id;
    END IF;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER prevent_delete_active_master
BEFORE DELETE ON employees
FOR EACH ROW
EXECUTE FUNCTION prevent_delete_active_master_func();

-- 4)
CREATE OR REPLACE FUNCTION check_worker_brigadier_func()
RETURNS TRIGGER AS $$
BEGIN
    -- If employee is marked as brigadier, they must be assigned to a brigade
    IF NEW.is_brigadier = true AND NEW.brigade_id IS NULL THEN
        RAISE EXCEPTION 'Brigadier must be assigned to a brigade';
    END IF;
    
    -- If this employee is marked as brigadier, check that there's no other brigadier in the same brigade
    IF NEW.is_brigadier = true AND NEW.brigade_id IS NOT NULL THEN
        IF EXISTS (
            SELECT 1 
            FROM workers 
            WHERE brigade_id = NEW.brigade_id 
            AND is_brigadier = true 
            AND w_id <> NEW.w_id
        ) THEN
            RAISE EXCEPTION 'Brigade % already has a brigadier', NEW.brigade_id;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER check_worker_brigadier
BEFORE INSERT OR UPDATE ON workers
FOR EACH ROW
EXECUTE FUNCTION check_worker_brigadier_func();

-- 5)
CREATE OR REPLACE FUNCTION fix_grade_change_employees_func()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE employees 
    SET grade_id = NEW.new_pos 
    WHERE w_id = NEW.w_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER fix_grade_change_employees
AFTER INSERT ON employee_movements
FOR EACH ROW
EXECUTE FUNCTION fix_grade_change_employees_func();

-- 6)
CREATE OR REPLACE FUNCTION section_products_insert_on_assembly_func()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO sections_products (s_id, p_id)
    SELECT NEW.s_id, NEW.p_id
    WHERE NOT EXISTS (
        SELECT 1 
        FROM sections_products 
        WHERE s_id = NEW.section_id AND p_id = NEW.product_id
    );
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER section_products_insert_on_assembly
AFTER INSERT ON assembly
FOR EACH ROW
EXECUTE FUNCTION section_products_insert_on_assembly_func();

-- 7)
CREATE OR REPLACE FUNCTION master_insert_on_ete_create_func()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_master AND NEW.section IS NOT NULL THEN
        INSERT INTO masters (w_id, s_id)
        VALUES (NEW.w_id, NEW.s_id);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER master_insert_on_ete_create
AFTER INSERT ON ete
FOR EACH ROW
EXECUTE FUNCTION master_insert_on_ete_create_func();
