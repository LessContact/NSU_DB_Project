\connect aerospace_factory

CREATE TABLE "product_categories" (
  "c_id" SERIAL PRIMARY KEY,
  "name" VARCHAR(255) NOT NULL
);

CREATE TABLE "workshops" (
  "wsh_id" SERIAL PRIMARY KEY,
  "name" VARCHAR(255) NOT NULL,
  "location" VARCHAR(255)
);

CREATE TABLE "labs" (
  "l_id" SERIAL PRIMARY KEY,
  "name" VARCHAR(255) NOT NULL,
  "location" VARCHAR(255)
);

CREATE TABLE "workshop_labs" (
  "wsh_id" INTEGER NOT NULL REFERENCES "workshops"("wsh_id") ON DELETE CASCADE ON UPDATE NO ACTION,
  "l_id"   INTEGER NOT NULL REFERENCES "labs"("l_id") ON DELETE CASCADE ON UPDATE NO ACTION,
  PRIMARY KEY ("wsh_id", "l_id")
);

CREATE TABLE "sections" (
  "s_id" SERIAL PRIMARY KEY,
  "name" VARCHAR(255) NOT NULL,
  "workshop_id" INTEGER NOT NULL REFERENCES "workshops"("wsh_id") ON DELETE CASCADE ON UPDATE NO ACTION
);

CREATE TABLE "grades" (
  "g_id" SERIAL PRIMARY KEY,
  "grade_title" VARCHAR(255) NOT NULL,
  "payment" NUMERIC(10,2) NOT NULL
);

CREATE TABLE "work_types" (
  "t_id" SERIAL PRIMARY KEY,
  "name" VARCHAR(255) NOT NULL
);

CREATE TABLE "worker_types" (
  "tp_id" SERIAL PRIMARY KEY,
  "name" VARCHAR(255) NOT NULL
);

CREATE TABLE "employees" (
  "w_id" BIGSERIAL PRIMARY KEY,
  "full_name" VARCHAR(255) NOT NULL,
  "hire_date" DATE NOT NULL DEFAULT CURRENT_DATE,
  "leave_date" DATE CHECK ("leave_date" IS NULL OR "leave_date" >= "hire_date"),
  "worker_type" INTEGER NOT NULL REFERENCES "worker_types"("tp_id") ON DELETE NO ACTION ON UPDATE NO ACTION,
  "experience" INTEGER NOT NULL CHECK ("experience" >= 0),
  "grade_id" INTEGER NOT NULL REFERENCES "grades"("g_id") ON DELETE NO ACTION ON UPDATE NO ACTION
);

CREATE TABLE "brigade" (
  "b_id" SERIAL PRIMARY KEY,
  "name" VARCHAR(255) NOT NULL
);

CREATE TABLE "workers" (
  "w_id" INTEGER PRIMARY KEY REFERENCES "employees"("w_id") ON DELETE CASCADE ON UPDATE NO ACTION,
  "brigade_id" INTEGER REFERENCES "brigade"("b_id") ON DELETE SET NULL ON UPDATE NO ACTION,
  "specialisation" INTEGER NOT NULL REFERENCES "work_types"("t_id") ON DELETE NO ACTION ON UPDATE NO ACTION,
  "is_brigadier" BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE "ete" (
  "w_id" INTEGER PRIMARY KEY REFERENCES "employees"("w_id") ON DELETE CASCADE ON UPDATE NO ACTION,
  "specialisation" INTEGER NOT NULL REFERENCES "work_types"("t_id") ON DELETE NO ACTION ON UPDATE NO ACTION,
  "education" VARCHAR(255) NOT NULL,
  "is_wsh_super" BOOLEAN NOT NULL DEFAULT FALSE,
  "is_master" BOOLEAN NOT NULL DEFAULT FALSE,
  "section" INTEGER REFERENCES "sections"("s_id") ON DELETE NO ACTION ON UPDATE NO ACTION
);

CREATE TABLE "employee_movements" (
  "entry_id" BIGSERIAL PRIMARY KEY,
  "w_id" INTEGER NOT NULL REFERENCES "employees"("w_id") ON DELETE CASCADE ON UPDATE NO ACTION,
  "move_date" DATE NOT NULL DEFAULT CURRENT_DATE,
  "old_pos" INTEGER REFERENCES "grades"("g_id") ON DELETE SET NULL ON UPDATE NO ACTION,
  "new_pos" INTEGER REFERENCES "grades"("g_id") ON DELETE SET NULL ON UPDATE NO ACTION,
  "comment" TEXT,
  CHECK("old_pos" IS DISTINCT FROM "new_pos") 
);

CREATE TABLE "products" (
  "p_id" BIGSERIAL PRIMARY KEY,
  "name" VARCHAR(255) NOT NULL,
  "category" INTEGER NOT NULL REFERENCES "product_categories"("c_id") ON DELETE NO ACTION ON UPDATE NO ACTION,
  "begin_date" DATE NOT NULL DEFAULT CURRENT_DATE,
  "end_date" DATE CHECK ("end_date" IS NULL OR "end_date" >= "begin_date"),
  "workshop_id" INTEGER NOT NULL REFERENCES "workshops"("wsh_id") ON DELETE NO ACTION ON UPDATE NO ACTION
);

CREATE TABLE "vehicles" (
  "p_id" INTEGER PRIMARY KEY REFERENCES "products"("p_id") ON DELETE CASCADE ON UPDATE NO ACTION,
  "use_type" VARCHAR(50) NOT NULL,
  "vehicle_type" VARCHAR(50) NOT NULL,
  "cargo_cap" INTEGER,
  "pass_count" INTEGER,
  "eng_count" INTEGER,
  "armaments" VARCHAR(255)
);

CREATE TABLE "missiles" (
  "p_id" INTEGER PRIMARY KEY REFERENCES "products"("p_id") ON DELETE CASCADE ON UPDATE NO ACTION,
  "type" VARCHAR(50) NOT NULL,
  "payload" INTEGER,
  "range" INTEGER
);

CREATE TABLE "other" (
  "p_id" INTEGER PRIMARY KEY REFERENCES "products"("p_id") ON DELETE CASCADE ON UPDATE NO ACTION,
  "text_specification" TEXT NOT NULL
);

CREATE TABLE "masters" (
  "unique_id" SERIAL PRIMARY KEY,
  "w_id" INTEGER NOT NULL REFERENCES "employees"("w_id") ON DELETE CASCADE ON UPDATE NO ACTION,
  "s_id" INTEGER NOT NULL REFERENCES "sections"("s_id") ON DELETE CASCADE ON UPDATE NO ACTION
);

CREATE TABLE "assembly" (
  "a_id" BIGSERIAL PRIMARY KEY,
  "brigade_id" INTEGER NOT NULL REFERENCES "brigade"("b_id") ON DELETE NO ACTION ON UPDATE NO ACTION,
  "section_id" INTEGER NOT NULL REFERENCES "sections"("s_id") ON DELETE NO ACTION ON UPDATE NO ACTION,
  "product_id" INTEGER NOT NULL REFERENCES "products"("p_id") ON DELETE NO ACTION ON UPDATE NO ACTION,
  "begin_date" DATE DEFAULT CURRENT_DATE,
  "end_date" DATE CHECK ("end_date" IS NULL OR "end_date" >= "begin_date"),
  "work_type" INTEGER REFERENCES "work_types"("t_id") ON DELETE NO ACTION ON UPDATE NO ACTION,
  "description" TEXT
);

CREATE TABLE "equipment" (
  "e_id" SERIAL PRIMARY KEY,
  "l_id" INTEGER NOT NULL REFERENCES "labs"("l_id") ON DELETE NO ACTION ON UPDATE NO ACTION,
  "name" VARCHAR(255) NOT NULL,
  "type" VARCHAR(255)
);

CREATE TABLE "testers" (
  "w_id" INTEGER PRIMARY KEY REFERENCES "employees"("w_id") ON DELETE CASCADE ON UPDATE NO ACTION,
  "l_id" INTEGER NOT NULL REFERENCES "labs"("l_id") ON DELETE NO ACTION ON UPDATE NO ACTION
);

CREATE TABLE "test" (
  "t_id" SERIAL PRIMARY KEY,
  "product_id" INTEGER NOT NULL REFERENCES "products"("p_id") ON DELETE NO ACTION ON UPDATE NO ACTION,
  "lab_id" INTEGER NOT NULL REFERENCES "labs"("l_id") ON DELETE NO ACTION ON UPDATE NO ACTION,
  "test_date" DATE NOT NULL DEFAULT CURRENT_DATE,
  "result" VARCHAR(255),
  "equipment_id" INTEGER REFERENCES "equipment"("e_id") ON DELETE NO ACTION ON UPDATE NO ACTION
);

CREATE TABLE "test_testers" (
  "test_id" INTEGER NOT NULL REFERENCES "test"("t_id") ON DELETE CASCADE ON UPDATE NO ACTION,
  "tw_id" INTEGER NOT NULL REFERENCES "testers"("w_id") ON DELETE CASCADE ON UPDATE NO ACTION,
  PRIMARY KEY ("test_id", "tw_id")
);

CREATE TABLE "sections_products" (
  "s_id" INTEGER NOT NULL REFERENCES "sections"("s_id") ON DELETE CASCADE ON UPDATE NO ACTION,
  "p_id" INTEGER NOT NULL REFERENCES "products"("p_id") ON DELETE CASCADE ON UPDATE NO ACTION,
  PRIMARY KEY ("s_id", "p_id")
);
