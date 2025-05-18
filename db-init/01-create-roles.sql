CREATE ROLE HR;
CREATE ROLE Testers;
CREATE ROLE Workshop_manager;

CREATE USER admin_user WITH PASSWORD 'admin' SUPERUSER ;

CREATE USER HR1 WITH PASSWORD 'HR1';
GRANT HR TO HR1;

CREATE USER tester WITH PASSWORD 'tester';
GRANT Testers TO tester;

CREATE USER wsh_manager WITH PASSWORD 'wsh_manager';
GRANT Workshop_manager TO wsh_manager;
