CREATE DATABASE aerospace_factory
    WITH OWNER = admin_user
    ENCODING = 'UTF8'
    LC_COLLATE = 'ru_RU.UTF-8'
    LC_CTYPE = 'ru_RU.UTF-8'
    LOCALE_PROVIDER = 'libc'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1
    IS_TEMPLATE = False;

ALTER DATABASE aerospace_factory SET default_text_search_config = 'russian';

\connect aerospace_factory

ALTER DEFAULT PRIVILEGES FOR ROLE admin_user
    IN SCHEMA public
    GRANT USAGE ON SEQUENCES TO HR, Testers, Workshop_manager;
