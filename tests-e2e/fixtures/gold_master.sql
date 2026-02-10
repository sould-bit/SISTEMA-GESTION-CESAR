--
-- PostgreSQL database dump
--

\restrict GxcW9yuC1JQVleHj6FoTqLKyb0dhXkD8TndEjgs1lutbgJibWrOlCDXHNsIlZSj

-- Dumped from database version 16.11
-- Dumped by pg_dump version 16.11

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS users_role_id_fkey;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS users_company_id_fkey;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS users_branch_id_fkey;
ALTER TABLE IF EXISTS ONLY public.tables DROP CONSTRAINT IF EXISTS tables_branch_id_fkey;
ALTER TABLE IF EXISTS ONLY public.subscriptions DROP CONSTRAINT IF EXISTS subscriptions_company_id_fkey;
ALTER TABLE IF EXISTS ONLY public.roles DROP CONSTRAINT IF EXISTS roles_company_id_fkey;
ALTER TABLE IF EXISTS ONLY public.role_permissions DROP CONSTRAINT IF EXISTS role_permissions_role_id_fkey;
ALTER TABLE IF EXISTS ONLY public.role_permissions DROP CONSTRAINT IF EXISTS role_permissions_permission_id_fkey;
ALTER TABLE IF EXISTS ONLY public.role_permissions DROP CONSTRAINT IF EXISTS role_permissions_granted_by_fkey;
ALTER TABLE IF EXISTS ONLY public.recipes DROP CONSTRAINT IF EXISTS recipes_product_id_fkey;
ALTER TABLE IF EXISTS ONLY public.recipes DROP CONSTRAINT IF EXISTS recipes_company_id_fkey;
ALTER TABLE IF EXISTS ONLY public.recipe_items DROP CONSTRAINT IF EXISTS recipe_items_recipe_id_fkey;
ALTER TABLE IF EXISTS ONLY public.recipe_items DROP CONSTRAINT IF EXISTS recipe_items_ingredient_id_fkey;
ALTER TABLE IF EXISTS ONLY public.recipe_items DROP CONSTRAINT IF EXISTS recipe_items_company_id_fkey;
ALTER TABLE IF EXISTS ONLY public.products DROP CONSTRAINT IF EXISTS products_company_id_fkey;
ALTER TABLE IF EXISTS ONLY public.products DROP CONSTRAINT IF EXISTS products_category_id_fkey;
ALTER TABLE IF EXISTS ONLY public.products DROP CONSTRAINT IF EXISTS products_active_recipe_id_fkey;
ALTER TABLE IF EXISTS ONLY public.production_events DROP CONSTRAINT IF EXISTS production_events_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.production_events DROP CONSTRAINT IF EXISTS production_events_output_ingredient_id_fkey;
ALTER TABLE IF EXISTS ONLY public.production_events DROP CONSTRAINT IF EXISTS production_events_output_batch_id_fkey;
ALTER TABLE IF EXISTS ONLY public.production_events DROP CONSTRAINT IF EXISTS production_events_input_ingredient_id_fkey;
ALTER TABLE IF EXISTS ONLY public.production_event_inputs DROP CONSTRAINT IF EXISTS production_event_inputs_production_event_id_fkey;
ALTER TABLE IF EXISTS ONLY public.production_event_inputs DROP CONSTRAINT IF EXISTS production_event_inputs_ingredient_id_fkey;
ALTER TABLE IF EXISTS ONLY public.production_event_input_batches DROP CONSTRAINT IF EXISTS production_event_input_batches_source_batch_id_fkey;
ALTER TABLE IF EXISTS ONLY public.production_event_input_batches DROP CONSTRAINT IF EXISTS production_event_input_batches_production_event_input_id_fkey;
ALTER TABLE IF EXISTS ONLY public.product_modifiers DROP CONSTRAINT IF EXISTS product_modifiers_company_id_fkey;
ALTER TABLE IF EXISTS ONLY public.permissions DROP CONSTRAINT IF EXISTS permissions_company_id_fkey;
ALTER TABLE IF EXISTS ONLY public.permissions DROP CONSTRAINT IF EXISTS permissions_category_id_fkey;
ALTER TABLE IF EXISTS ONLY public.permission_categories DROP CONSTRAINT IF EXISTS permission_categories_company_id_fkey;
ALTER TABLE IF EXISTS ONLY public.payments DROP CONSTRAINT IF EXISTS payments_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.payments DROP CONSTRAINT IF EXISTS payments_order_id_fkey;
ALTER TABLE IF EXISTS ONLY public.payments DROP CONSTRAINT IF EXISTS payments_company_id_fkey;
ALTER TABLE IF EXISTS ONLY public.payments DROP CONSTRAINT IF EXISTS payments_branch_id_fkey;
ALTER TABLE IF EXISTS ONLY public.orders DROP CONSTRAINT IF EXISTS orders_table_id_fkey;
ALTER TABLE IF EXISTS ONLY public.orders DROP CONSTRAINT IF EXISTS orders_delivery_person_id_fkey;
ALTER TABLE IF EXISTS ONLY public.orders DROP CONSTRAINT IF EXISTS orders_customer_id_fkey;
ALTER TABLE IF EXISTS ONLY public.orders DROP CONSTRAINT IF EXISTS orders_created_by_id_fkey;
ALTER TABLE IF EXISTS ONLY public.orders DROP CONSTRAINT IF EXISTS orders_company_id_fkey;
ALTER TABLE IF EXISTS ONLY public.orders DROP CONSTRAINT IF EXISTS orders_cancellation_requested_by_id_fkey;
ALTER TABLE IF EXISTS ONLY public.orders DROP CONSTRAINT IF EXISTS orders_branch_id_fkey;
ALTER TABLE IF EXISTS ONLY public.order_items DROP CONSTRAINT IF EXISTS order_items_product_id_fkey;
ALTER TABLE IF EXISTS ONLY public.order_items DROP CONSTRAINT IF EXISTS order_items_order_id_fkey;
ALTER TABLE IF EXISTS ONLY public.order_item_modifiers DROP CONSTRAINT IF EXISTS order_item_modifiers_order_item_id_fkey;
ALTER TABLE IF EXISTS ONLY public.order_item_modifiers DROP CONSTRAINT IF EXISTS order_item_modifiers_modifier_id_fkey;
ALTER TABLE IF EXISTS ONLY public.order_counters DROP CONSTRAINT IF EXISTS order_counters_company_id_fkey;
ALTER TABLE IF EXISTS ONLY public.order_counters DROP CONSTRAINT IF EXISTS order_counters_branch_id_fkey;
ALTER TABLE IF EXISTS ONLY public.order_audits DROP CONSTRAINT IF EXISTS order_audits_order_id_fkey;
ALTER TABLE IF EXISTS ONLY public.order_audits DROP CONSTRAINT IF EXISTS order_audits_changed_by_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.modifier_recipe_items DROP CONSTRAINT IF EXISTS modifier_recipe_items_modifier_id_fkey;
ALTER TABLE IF EXISTS ONLY public.modifier_recipe_items DROP CONSTRAINT IF EXISTS modifier_recipe_items_ingredient_product_id_fkey;
ALTER TABLE IF EXISTS ONLY public.modifier_recipe_items DROP CONSTRAINT IF EXISTS modifier_recipe_items_ingredient_id_fkey;
ALTER TABLE IF EXISTS ONLY public.inventory_transactions DROP CONSTRAINT IF EXISTS inventory_transactions_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.inventory_transactions DROP CONSTRAINT IF EXISTS inventory_transactions_inventory_id_fkey;
ALTER TABLE IF EXISTS ONLY public.inventory DROP CONSTRAINT IF EXISTS inventory_product_id_fkey;
ALTER TABLE IF EXISTS ONLY public.inventory_counts DROP CONSTRAINT IF EXISTS inventory_counts_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.inventory_counts DROP CONSTRAINT IF EXISTS inventory_counts_company_id_fkey;
ALTER TABLE IF EXISTS ONLY public.inventory_counts DROP CONSTRAINT IF EXISTS inventory_counts_branch_id_fkey;
ALTER TABLE IF EXISTS ONLY public.inventory_count_items DROP CONSTRAINT IF EXISTS inventory_count_items_ingredient_id_fkey;
ALTER TABLE IF EXISTS ONLY public.inventory_count_items DROP CONSTRAINT IF EXISTS inventory_count_items_count_id_fkey;
ALTER TABLE IF EXISTS ONLY public.inventory DROP CONSTRAINT IF EXISTS inventory_branch_id_fkey;
ALTER TABLE IF EXISTS ONLY public.ingredients DROP CONSTRAINT IF EXISTS ingredients_company_id_fkey;
ALTER TABLE IF EXISTS ONLY public.ingredients DROP CONSTRAINT IF EXISTS ingredients_category_id_fkey;
ALTER TABLE IF EXISTS ONLY public.ingredient_transactions DROP CONSTRAINT IF EXISTS ingredient_transactions_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.ingredient_transactions DROP CONSTRAINT IF EXISTS ingredient_transactions_inventory_id_fkey;
ALTER TABLE IF EXISTS ONLY public.ingredient_inventory DROP CONSTRAINT IF EXISTS ingredient_inventory_ingredient_id_fkey;
ALTER TABLE IF EXISTS ONLY public.ingredient_inventory DROP CONSTRAINT IF EXISTS ingredient_inventory_branch_id_fkey;
ALTER TABLE IF EXISTS ONLY public.ingredient_cost_history DROP CONSTRAINT IF EXISTS ingredient_cost_history_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.ingredient_cost_history DROP CONSTRAINT IF EXISTS ingredient_cost_history_ingredient_id_fkey;
ALTER TABLE IF EXISTS ONLY public.ingredient_batches DROP CONSTRAINT IF EXISTS ingredient_batches_ingredient_id_fkey;
ALTER TABLE IF EXISTS ONLY public.ingredient_batches DROP CONSTRAINT IF EXISTS ingredient_batches_branch_id_fkey;
ALTER TABLE IF EXISTS ONLY public.delivery_shifts DROP CONSTRAINT IF EXISTS delivery_shifts_delivery_person_id_fkey;
ALTER TABLE IF EXISTS ONLY public.delivery_shifts DROP CONSTRAINT IF EXISTS delivery_shifts_company_id_fkey;
ALTER TABLE IF EXISTS ONLY public.delivery_shifts DROP CONSTRAINT IF EXISTS delivery_shifts_branch_id_fkey;
ALTER TABLE IF EXISTS ONLY public.customers DROP CONSTRAINT IF EXISTS customers_company_id_fkey;
ALTER TABLE IF EXISTS ONLY public.customer_addresses DROP CONSTRAINT IF EXISTS customer_addresses_customer_id_fkey;
ALTER TABLE IF EXISTS ONLY public.categories DROP CONSTRAINT IF EXISTS categories_company_id_fkey;
ALTER TABLE IF EXISTS ONLY public.cash_closures DROP CONSTRAINT IF EXISTS cash_closures_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.cash_closures DROP CONSTRAINT IF EXISTS cash_closures_company_id_fkey;
ALTER TABLE IF EXISTS ONLY public.cash_closures DROP CONSTRAINT IF EXISTS cash_closures_branch_id_fkey;
ALTER TABLE IF EXISTS ONLY public.branches DROP CONSTRAINT IF EXISTS branches_company_id_fkey;
ALTER TABLE IF EXISTS ONLY public.audit_logs DROP CONSTRAINT IF EXISTS audit_logs_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.audit_logs DROP CONSTRAINT IF EXISTS audit_logs_company_id_fkey;
ALTER TABLE IF EXISTS ONLY public.audit_logs DROP CONSTRAINT IF EXISTS audit_logs_branch_id_fkey;
DROP INDEX IF EXISTS public.ix_users_username;
DROP INDEX IF EXISTS public.ix_users_role_id;
DROP INDEX IF EXISTS public.ix_users_company_id;
DROP INDEX IF EXISTS public.ix_users_branch_id;
DROP INDEX IF EXISTS public.ix_unit_conversions_to_unit;
DROP INDEX IF EXISTS public.ix_unit_conversions_from_unit;
DROP INDEX IF EXISTS public.ix_tables_branch_id;
DROP INDEX IF EXISTS public.ix_subscriptions_company_id;
DROP INDEX IF EXISTS public.ix_roles_company_id;
DROP INDEX IF EXISTS public.ix_role_permissions_role_id;
DROP INDEX IF EXISTS public.ix_role_permissions_permission_id;
DROP INDEX IF EXISTS public.ix_recipes_product_id;
DROP INDEX IF EXISTS public.ix_recipes_company_id;
DROP INDEX IF EXISTS public.ix_recipe_items_recipe_id;
DROP INDEX IF EXISTS public.ix_recipe_items_ingredient_id;
DROP INDEX IF EXISTS public.ix_recipe_items_company_id;
DROP INDEX IF EXISTS public.ix_products_company_id;
DROP INDEX IF EXISTS public.ix_products_category_id;
DROP INDEX IF EXISTS public.ix_production_events_output_ingredient_id;
DROP INDEX IF EXISTS public.ix_production_events_input_ingredient_id;
DROP INDEX IF EXISTS public.ix_production_events_company_id;
DROP INDEX IF EXISTS public.ix_production_event_inputs_production_event_id;
DROP INDEX IF EXISTS public.ix_production_event_inputs_ingredient_id;
DROP INDEX IF EXISTS public.ix_production_event_input_batches_source_batch_id;
DROP INDEX IF EXISTS public.ix_production_event_input_batches_production_event_input_id;
DROP INDEX IF EXISTS public.ix_print_jobs_status;
DROP INDEX IF EXISTS public.ix_print_jobs_order_id;
DROP INDEX IF EXISTS public.ix_print_jobs_company_id;
DROP INDEX IF EXISTS public.ix_permissions_company_id;
DROP INDEX IF EXISTS public.ix_permissions_category_id;
DROP INDEX IF EXISTS public.ix_permission_categories_company_id;
DROP INDEX IF EXISTS public.ix_payments_user_id;
DROP INDEX IF EXISTS public.ix_payments_company_id;
DROP INDEX IF EXISTS public.ix_payments_branch_id;
DROP INDEX IF EXISTS public.ix_orders_table_id;
DROP INDEX IF EXISTS public.ix_orders_order_number;
DROP INDEX IF EXISTS public.ix_orders_delivery_person_id;
DROP INDEX IF EXISTS public.ix_orders_customer_id;
DROP INDEX IF EXISTS public.ix_orders_created_by_id;
DROP INDEX IF EXISTS public.ix_orders_company_id;
DROP INDEX IF EXISTS public.ix_orders_branch_id;
DROP INDEX IF EXISTS public.ix_order_counters_company_id;
DROP INDEX IF EXISTS public.ix_order_counters_branch_id;
DROP INDEX IF EXISTS public.ix_order_audits_order_id;
DROP INDEX IF EXISTS public.ix_inventory_counts_company_id;
DROP INDEX IF EXISTS public.ix_inventory_counts_branch_id;
DROP INDEX IF EXISTS public.ix_inventory_count_items_count_id;
DROP INDEX IF EXISTS public.ix_ingredients_sku;
DROP INDEX IF EXISTS public.ix_ingredients_name;
DROP INDEX IF EXISTS public.ix_ingredients_company_id;
DROP INDEX IF EXISTS public.ix_ingredients_category_id;
DROP INDEX IF EXISTS public.ix_ingredient_cost_history_ingredient_id;
DROP INDEX IF EXISTS public.ix_ingredient_batches_is_active;
DROP INDEX IF EXISTS public.ix_ingredient_batches_ingredient_id;
DROP INDEX IF EXISTS public.ix_ingredient_batches_branch_id;
DROP INDEX IF EXISTS public.ix_ingredient_batches_acquired_at;
DROP INDEX IF EXISTS public.ix_delivery_shifts_delivery_person_id;
DROP INDEX IF EXISTS public.ix_delivery_shifts_company_id;
DROP INDEX IF EXISTS public.ix_delivery_shifts_branch_id;
DROP INDEX IF EXISTS public.ix_customers_phone;
DROP INDEX IF EXISTS public.ix_customers_company_id;
DROP INDEX IF EXISTS public.ix_customer_addresses_customer_id;
DROP INDEX IF EXISTS public.ix_companies_slug;
DROP INDEX IF EXISTS public.ix_categories_company_id;
DROP INDEX IF EXISTS public.ix_cash_closures_company_id;
DROP INDEX IF EXISTS public.ix_cash_closures_branch_id;
DROP INDEX IF EXISTS public.ix_branches_company_id;
DROP INDEX IF EXISTS public.ix_audit_logs_user_id;
DROP INDEX IF EXISTS public.ix_audit_logs_created_at;
DROP INDEX IF EXISTS public.ix_audit_logs_company_id;
DROP INDEX IF EXISTS public.ix_audit_logs_action;
DROP INDEX IF EXISTS public.idx_users_role;
DROP INDEX IF EXISTS public.idx_users_login;
DROP INDEX IF EXISTS public.idx_subscriptions_status;
DROP INDEX IF EXISTS public.idx_roles_system;
DROP INDEX IF EXISTS public.idx_roles_hierarchy;
DROP INDEX IF EXISTS public.idx_roles_company_active;
DROP INDEX IF EXISTS public.idx_role_perm_role;
DROP INDEX IF EXISTS public.idx_role_perm_permission;
DROP INDEX IF EXISTS public.idx_role_perm_expires;
DROP INDEX IF EXISTS public.idx_products_company_active;
DROP INDEX IF EXISTS public.idx_products_category;
DROP INDEX IF EXISTS public.idx_perm_resource_action;
DROP INDEX IF EXISTS public.idx_perm_company_category;
DROP INDEX IF EXISTS public.idx_perm_cat_system;
DROP INDEX IF EXISTS public.idx_perm_cat_company_active;
DROP INDEX IF EXISTS public.idx_perm_active;
DROP INDEX IF EXISTS public.idx_payments_order;
DROP INDEX IF EXISTS public.idx_payments_company_date;
DROP INDEX IF EXISTS public.idx_orders_company_status;
DROP INDEX IF EXISTS public.idx_orders_branch_date;
DROP INDEX IF EXISTS public.idx_modifiers_company;
DROP INDEX IF EXISTS public.idx_inventory_branch;
DROP INDEX IF EXISTS public.idx_ingredient_inventory_branch;
DROP INDEX IF EXISTS public.idx_delivery_shifts_driver;
DROP INDEX IF EXISTS public.idx_delivery_shifts_date;
DROP INDEX IF EXISTS public.idx_companies_active;
DROP INDEX IF EXISTS public.idx_categories_company_active;
DROP INDEX IF EXISTS public.idx_branches_active;
DROP INDEX IF EXISTS public.idx_audit_user_action;
DROP INDEX IF EXISTS public.idx_audit_entity;
DROP INDEX IF EXISTS public.idx_audit_company_created;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS users_pkey;
ALTER TABLE IF EXISTS ONLY public.inventory DROP CONSTRAINT IF EXISTS uq_inventory_branch_product;
ALTER TABLE IF EXISTS ONLY public.ingredient_inventory DROP CONSTRAINT IF EXISTS uq_ingredient_inventory_branch;
ALTER TABLE IF EXISTS ONLY public.customers DROP CONSTRAINT IF EXISTS uq_customer_phone_company;
ALTER TABLE IF EXISTS ONLY public.order_counters DROP CONSTRAINT IF EXISTS uq_branch_counter_type;
ALTER TABLE IF EXISTS ONLY public.unit_conversions DROP CONSTRAINT IF EXISTS unit_conversions_pkey;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS unique_username_per_company;
ALTER TABLE IF EXISTS ONLY public.role_permissions DROP CONSTRAINT IF EXISTS unique_role_permission;
ALTER TABLE IF EXISTS ONLY public.roles DROP CONSTRAINT IF EXISTS unique_role_code_per_company;
ALTER TABLE IF EXISTS ONLY public.permissions DROP CONSTRAINT IF EXISTS unique_permission_code_per_company;
ALTER TABLE IF EXISTS ONLY public.categories DROP CONSTRAINT IF EXISTS unique_category_name_per_company;
ALTER TABLE IF EXISTS ONLY public.permission_categories DROP CONSTRAINT IF EXISTS unique_category_code_per_company;
ALTER TABLE IF EXISTS ONLY public.branches DROP CONSTRAINT IF EXISTS unique_branch_code_per_company;
ALTER TABLE IF EXISTS ONLY public.tables DROP CONSTRAINT IF EXISTS tables_pkey;
ALTER TABLE IF EXISTS ONLY public.subscriptions DROP CONSTRAINT IF EXISTS subscriptions_pkey;
ALTER TABLE IF EXISTS ONLY public.roles DROP CONSTRAINT IF EXISTS roles_pkey;
ALTER TABLE IF EXISTS ONLY public.role_permissions DROP CONSTRAINT IF EXISTS role_permissions_pkey;
ALTER TABLE IF EXISTS ONLY public.recipes DROP CONSTRAINT IF EXISTS recipes_pkey;
ALTER TABLE IF EXISTS ONLY public.recipe_items DROP CONSTRAINT IF EXISTS recipe_items_pkey;
ALTER TABLE IF EXISTS ONLY public.products DROP CONSTRAINT IF EXISTS products_pkey;
ALTER TABLE IF EXISTS ONLY public.production_events DROP CONSTRAINT IF EXISTS production_events_pkey;
ALTER TABLE IF EXISTS ONLY public.production_event_inputs DROP CONSTRAINT IF EXISTS production_event_inputs_pkey;
ALTER TABLE IF EXISTS ONLY public.production_event_input_batches DROP CONSTRAINT IF EXISTS production_event_input_batches_pkey;
ALTER TABLE IF EXISTS ONLY public.product_modifiers DROP CONSTRAINT IF EXISTS product_modifiers_pkey;
ALTER TABLE IF EXISTS ONLY public.print_jobs DROP CONSTRAINT IF EXISTS print_jobs_pkey;
ALTER TABLE IF EXISTS ONLY public.permissions DROP CONSTRAINT IF EXISTS permissions_pkey;
ALTER TABLE IF EXISTS ONLY public.permission_categories DROP CONSTRAINT IF EXISTS permission_categories_pkey;
ALTER TABLE IF EXISTS ONLY public.payments DROP CONSTRAINT IF EXISTS payments_pkey;
ALTER TABLE IF EXISTS ONLY public.orders DROP CONSTRAINT IF EXISTS orders_pkey;
ALTER TABLE IF EXISTS ONLY public.order_items DROP CONSTRAINT IF EXISTS order_items_pkey;
ALTER TABLE IF EXISTS ONLY public.order_item_modifiers DROP CONSTRAINT IF EXISTS order_item_modifiers_pkey;
ALTER TABLE IF EXISTS ONLY public.order_counters DROP CONSTRAINT IF EXISTS order_counters_pkey;
ALTER TABLE IF EXISTS ONLY public.order_audits DROP CONSTRAINT IF EXISTS order_audits_pkey;
ALTER TABLE IF EXISTS ONLY public.modifier_recipe_items DROP CONSTRAINT IF EXISTS modifier_recipe_items_pkey;
ALTER TABLE IF EXISTS ONLY public.inventory_transactions DROP CONSTRAINT IF EXISTS inventory_transactions_pkey;
ALTER TABLE IF EXISTS ONLY public.inventory DROP CONSTRAINT IF EXISTS inventory_pkey;
ALTER TABLE IF EXISTS ONLY public.inventory_counts DROP CONSTRAINT IF EXISTS inventory_counts_pkey;
ALTER TABLE IF EXISTS ONLY public.inventory_count_items DROP CONSTRAINT IF EXISTS inventory_count_items_pkey;
ALTER TABLE IF EXISTS ONLY public.ingredients DROP CONSTRAINT IF EXISTS ingredients_pkey;
ALTER TABLE IF EXISTS ONLY public.ingredient_transactions DROP CONSTRAINT IF EXISTS ingredient_transactions_pkey;
ALTER TABLE IF EXISTS ONLY public.ingredient_inventory DROP CONSTRAINT IF EXISTS ingredient_inventory_pkey;
ALTER TABLE IF EXISTS ONLY public.ingredient_cost_history DROP CONSTRAINT IF EXISTS ingredient_cost_history_pkey;
ALTER TABLE IF EXISTS ONLY public.ingredient_batches DROP CONSTRAINT IF EXISTS ingredient_batches_pkey;
ALTER TABLE IF EXISTS ONLY public.delivery_shifts DROP CONSTRAINT IF EXISTS delivery_shifts_pkey;
ALTER TABLE IF EXISTS ONLY public.customers DROP CONSTRAINT IF EXISTS customers_pkey;
ALTER TABLE IF EXISTS ONLY public.customer_addresses DROP CONSTRAINT IF EXISTS customer_addresses_pkey;
ALTER TABLE IF EXISTS ONLY public.companies DROP CONSTRAINT IF EXISTS companies_pkey;
ALTER TABLE IF EXISTS ONLY public.categories DROP CONSTRAINT IF EXISTS categories_pkey;
ALTER TABLE IF EXISTS ONLY public.cash_closures DROP CONSTRAINT IF EXISTS cash_closures_pkey;
ALTER TABLE IF EXISTS ONLY public.branches DROP CONSTRAINT IF EXISTS branches_pkey;
ALTER TABLE IF EXISTS ONLY public.audit_logs DROP CONSTRAINT IF EXISTS audit_logs_pkey;
ALTER TABLE IF EXISTS public.users ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.tables ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.subscriptions ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.products ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.product_modifiers ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.print_jobs ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.payments ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.orders ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.order_items ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.order_item_modifiers ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.order_counters ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.order_audits ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.modifier_recipe_items ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.inventory_transactions ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.inventory ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.delivery_shifts ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.customers ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.customer_addresses ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.companies ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.categories ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.cash_closures ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.branches ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.audit_logs ALTER COLUMN id DROP DEFAULT;
DROP SEQUENCE IF EXISTS public.users_id_seq;
DROP TABLE IF EXISTS public.users;
DROP TABLE IF EXISTS public.unit_conversions;
DROP SEQUENCE IF EXISTS public.tables_id_seq;
DROP TABLE IF EXISTS public.tables;
DROP SEQUENCE IF EXISTS public.subscriptions_id_seq;
DROP TABLE IF EXISTS public.subscriptions;
DROP TABLE IF EXISTS public.roles;
DROP TABLE IF EXISTS public.role_permissions;
DROP TABLE IF EXISTS public.recipes;
DROP TABLE IF EXISTS public.recipe_items;
DROP SEQUENCE IF EXISTS public.products_id_seq;
DROP TABLE IF EXISTS public.products;
DROP TABLE IF EXISTS public.production_events;
DROP TABLE IF EXISTS public.production_event_inputs;
DROP TABLE IF EXISTS public.production_event_input_batches;
DROP SEQUENCE IF EXISTS public.product_modifiers_id_seq;
DROP TABLE IF EXISTS public.product_modifiers;
DROP SEQUENCE IF EXISTS public.print_jobs_id_seq;
DROP TABLE IF EXISTS public.print_jobs;
DROP TABLE IF EXISTS public.permissions;
DROP TABLE IF EXISTS public.permission_categories;
DROP SEQUENCE IF EXISTS public.payments_id_seq;
DROP TABLE IF EXISTS public.payments;
DROP SEQUENCE IF EXISTS public.orders_id_seq;
DROP TABLE IF EXISTS public.orders;
DROP SEQUENCE IF EXISTS public.order_items_id_seq;
DROP TABLE IF EXISTS public.order_items;
DROP SEQUENCE IF EXISTS public.order_item_modifiers_id_seq;
DROP TABLE IF EXISTS public.order_item_modifiers;
DROP SEQUENCE IF EXISTS public.order_counters_id_seq;
DROP TABLE IF EXISTS public.order_counters;
DROP SEQUENCE IF EXISTS public.order_audits_id_seq;
DROP TABLE IF EXISTS public.order_audits;
DROP SEQUENCE IF EXISTS public.modifier_recipe_items_id_seq;
DROP TABLE IF EXISTS public.modifier_recipe_items;
DROP SEQUENCE IF EXISTS public.inventory_transactions_id_seq;
DROP TABLE IF EXISTS public.inventory_transactions;
DROP SEQUENCE IF EXISTS public.inventory_id_seq;
DROP TABLE IF EXISTS public.inventory_counts;
DROP TABLE IF EXISTS public.inventory_count_items;
DROP TABLE IF EXISTS public.inventory;
DROP TABLE IF EXISTS public.ingredients;
DROP TABLE IF EXISTS public.ingredient_transactions;
DROP TABLE IF EXISTS public.ingredient_inventory;
DROP TABLE IF EXISTS public.ingredient_cost_history;
DROP TABLE IF EXISTS public.ingredient_batches;
DROP SEQUENCE IF EXISTS public.delivery_shifts_id_seq;
DROP TABLE IF EXISTS public.delivery_shifts;
DROP SEQUENCE IF EXISTS public.customers_id_seq;
DROP TABLE IF EXISTS public.customers;
DROP SEQUENCE IF EXISTS public.customer_addresses_id_seq;
DROP TABLE IF EXISTS public.customer_addresses;
DROP SEQUENCE IF EXISTS public.companies_id_seq;
DROP TABLE IF EXISTS public.companies;
DROP SEQUENCE IF EXISTS public.categories_id_seq;
DROP TABLE IF EXISTS public.categories;
DROP SEQUENCE IF EXISTS public.cash_closures_id_seq;
DROP TABLE IF EXISTS public.cash_closures;
DROP SEQUENCE IF EXISTS public.branches_id_seq;
DROP TABLE IF EXISTS public.branches;
DROP SEQUENCE IF EXISTS public.audit_logs_id_seq;
DROP TABLE IF EXISTS public.audit_logs;
DROP TYPE IF EXISTS public.tablestatus;
DROP TYPE IF EXISTS public.printjobstatus;
DROP TYPE IF EXISTS public.inventorycountstatus;
DROP TYPE IF EXISTS public.ingredient_type_enum;
DROP TYPE IF EXISTS public.cashclosurestatus;
--
-- Name: cashclosurestatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.cashclosurestatus AS ENUM (
    'OPEN',
    'CLOSED'
);


--
-- Name: ingredient_type_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.ingredient_type_enum AS ENUM (
    'RAW',
    'PROCESSED',
    'MERCHANDISE'
);


--
-- Name: inventorycountstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.inventorycountstatus AS ENUM (
    'OPEN',
    'CLOSED',
    'APPLIED'
);


--
-- Name: printjobstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.printjobstatus AS ENUM (
    'PENDING',
    'PROCESSING',
    'COMPLETED',
    'FAILED'
);


--
-- Name: tablestatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.tablestatus AS ENUM (
    'AVAILABLE',
    'OCCUPIED',
    'RESERVED',
    'ATTENTION'
);


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: audit_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.audit_logs (
    id integer NOT NULL,
    company_id integer NOT NULL,
    user_id integer,
    username character varying(100),
    action character varying NOT NULL,
    entity_type character varying(50),
    entity_id integer,
    old_value json,
    new_value json,
    description character varying(500),
    ip_address character varying(45),
    user_agent character varying(500),
    branch_id integer,
    created_at timestamp without time zone NOT NULL
);


--
-- Name: audit_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.audit_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: audit_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.audit_logs_id_seq OWNED BY public.audit_logs.id;


--
-- Name: branches; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.branches (
    id integer NOT NULL,
    company_id integer NOT NULL,
    name character varying(200) NOT NULL,
    code character varying(20) NOT NULL,
    address character varying,
    phone character varying(50),
    is_active boolean NOT NULL,
    is_main boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone
);


--
-- Name: branches_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.branches_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: branches_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.branches_id_seq OWNED BY public.branches.id;


--
-- Name: cash_closures; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cash_closures (
    id integer NOT NULL,
    company_id integer NOT NULL,
    branch_id integer NOT NULL,
    user_id integer NOT NULL,
    opened_at timestamp without time zone NOT NULL,
    closed_at timestamp without time zone,
    initial_cash numeric(12,2) NOT NULL,
    expected_cash numeric(12,2) NOT NULL,
    expected_card numeric(12,2) NOT NULL,
    expected_transfer numeric(12,2) NOT NULL,
    expected_total numeric(12,2) NOT NULL,
    real_cash numeric(12,2) NOT NULL,
    real_card numeric(12,2) NOT NULL,
    real_transfer numeric(12,2) NOT NULL,
    real_total numeric(12,2) NOT NULL,
    difference numeric(12,2) NOT NULL,
    status public.cashclosurestatus NOT NULL,
    notes character varying(500)
);


--
-- Name: cash_closures_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cash_closures_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: cash_closures_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cash_closures_id_seq OWNED BY public.cash_closures.id;


--
-- Name: categories; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.categories (
    id integer NOT NULL,
    company_id integer NOT NULL,
    name character varying(100) NOT NULL,
    description character varying(255),
    is_active boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone
);


--
-- Name: categories_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.categories_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: categories_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.categories_id_seq OWNED BY public.categories.id;


--
-- Name: companies; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.companies (
    id integer NOT NULL,
    name character varying(200) NOT NULL,
    slug character varying(100) NOT NULL,
    legal_name character varying(200),
    tax_id character varying(50),
    owner_name character varying(200),
    owner_email character varying(200),
    owner_phone character varying(50),
    plan character varying(20) NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone
);


--
-- Name: companies_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.companies_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: companies_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.companies_id_seq OWNED BY public.companies.id;


--
-- Name: customer_addresses; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.customer_addresses (
    id integer NOT NULL,
    customer_id integer NOT NULL,
    name character varying(50) NOT NULL,
    address character varying(255) NOT NULL,
    details character varying(100),
    latitude double precision,
    longitude double precision,
    is_default boolean NOT NULL
);


--
-- Name: customer_addresses_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.customer_addresses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: customer_addresses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.customer_addresses_id_seq OWNED BY public.customer_addresses.id;


--
-- Name: customers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.customers (
    id integer NOT NULL,
    company_id integer NOT NULL,
    phone character varying(20) NOT NULL,
    full_name character varying(100) NOT NULL,
    email character varying(100),
    notes character varying,
    is_active boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone
);


--
-- Name: customers_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.customers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: customers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.customers_id_seq OWNED BY public.customers.id;


--
-- Name: delivery_shifts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.delivery_shifts (
    id integer NOT NULL,
    company_id integer NOT NULL,
    branch_id integer NOT NULL,
    delivery_person_id integer NOT NULL,
    started_at timestamp without time zone NOT NULL,
    ended_at timestamp without time zone,
    total_orders integer NOT NULL,
    total_delivered integer NOT NULL,
    total_cancelled integer NOT NULL,
    total_earnings numeric(12,2),
    expected_cash numeric(12,2),
    cash_collected numeric(12,2),
    status character varying,
    closing_notes character varying(500)
);


--
-- Name: delivery_shifts_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.delivery_shifts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: delivery_shifts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.delivery_shifts_id_seq OWNED BY public.delivery_shifts.id;


--
-- Name: ingredient_batches; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ingredient_batches (
    id uuid NOT NULL,
    ingredient_id uuid NOT NULL,
    branch_id integer NOT NULL,
    quantity_initial numeric(18,4) NOT NULL,
    quantity_remaining numeric(18,4) NOT NULL,
    cost_per_unit numeric(18,6) NOT NULL,
    total_cost numeric(18,2) NOT NULL,
    acquired_at timestamp without time zone NOT NULL,
    is_active boolean NOT NULL,
    supplier character varying(100)
);


--
-- Name: ingredient_cost_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ingredient_cost_history (
    id uuid NOT NULL,
    ingredient_id uuid NOT NULL,
    previous_cost numeric(10,2),
    new_cost numeric(10,2),
    reason character varying,
    user_id integer,
    created_at timestamp without time zone NOT NULL
);


--
-- Name: ingredient_inventory; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ingredient_inventory (
    id uuid NOT NULL,
    branch_id integer NOT NULL,
    ingredient_id uuid NOT NULL,
    stock numeric(12,3),
    min_stock numeric(12,3),
    max_stock numeric(12,3),
    updated_at timestamp without time zone NOT NULL
);


--
-- Name: ingredient_transactions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ingredient_transactions (
    id uuid NOT NULL,
    inventory_id uuid NOT NULL,
    transaction_type character varying(20) NOT NULL,
    quantity numeric(12,3),
    balance_after numeric(12,3),
    reference_id character varying(100),
    reason character varying(255),
    user_id integer,
    created_at timestamp without time zone NOT NULL
);


--
-- Name: ingredients; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ingredients (
    name character varying NOT NULL,
    sku character varying(150) NOT NULL,
    base_unit character varying NOT NULL,
    current_cost numeric(18,4),
    last_cost numeric(18,4),
    yield_factor double precision NOT NULL,
    category_id integer,
    company_id integer NOT NULL,
    ingredient_type public.ingredient_type_enum NOT NULL,
    id uuid NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone
);


--
-- Name: inventory; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.inventory (
    id integer NOT NULL,
    branch_id integer NOT NULL,
    product_id integer NOT NULL,
    stock numeric(12,3) NOT NULL,
    min_stock numeric(12,3) NOT NULL,
    max_stock numeric(12,3),
    bin_location character varying(50),
    updated_at timestamp without time zone NOT NULL
);


--
-- Name: inventory_count_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.inventory_count_items (
    ingredient_id uuid NOT NULL,
    expected_quantity numeric(20,4) NOT NULL,
    counted_quantity numeric(20,4),
    id uuid NOT NULL,
    count_id uuid NOT NULL,
    cost_per_unit numeric(20,4) NOT NULL
);


--
-- Name: inventory_counts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.inventory_counts (
    branch_id integer NOT NULL,
    status public.inventorycountstatus NOT NULL,
    notes character varying,
    id uuid NOT NULL,
    company_id integer NOT NULL,
    user_id integer,
    created_at timestamp without time zone NOT NULL,
    closed_at timestamp without time zone,
    applied_at timestamp without time zone
);


--
-- Name: inventory_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.inventory_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: inventory_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.inventory_id_seq OWNED BY public.inventory.id;


--
-- Name: inventory_transactions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.inventory_transactions (
    id integer NOT NULL,
    inventory_id integer NOT NULL,
    transaction_type character varying(20) NOT NULL,
    quantity numeric(12,3) NOT NULL,
    balance_after numeric(12,3) NOT NULL,
    reference_id character varying(100),
    reason character varying(255),
    user_id integer,
    created_at timestamp without time zone NOT NULL
);


--
-- Name: inventory_transactions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.inventory_transactions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: inventory_transactions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.inventory_transactions_id_seq OWNED BY public.inventory_transactions.id;


--
-- Name: modifier_recipe_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.modifier_recipe_items (
    id integer NOT NULL,
    modifier_id integer NOT NULL,
    ingredient_product_id integer,
    ingredient_id uuid,
    quantity numeric(10,3),
    unit character varying(50) NOT NULL
);


--
-- Name: modifier_recipe_items_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.modifier_recipe_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: modifier_recipe_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.modifier_recipe_items_id_seq OWNED BY public.modifier_recipe_items.id;


--
-- Name: order_audits; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.order_audits (
    id integer NOT NULL,
    order_id integer NOT NULL,
    old_status character varying NOT NULL,
    new_status character varying NOT NULL,
    changed_by_user_id integer,
    changed_at timestamp without time zone NOT NULL,
    meta json
);


--
-- Name: order_audits_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.order_audits_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: order_audits_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.order_audits_id_seq OWNED BY public.order_audits.id;


--
-- Name: order_counters; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.order_counters (
    id integer NOT NULL,
    company_id integer NOT NULL,
    branch_id integer NOT NULL,
    counter_type character varying(50) NOT NULL,
    prefix character varying(10),
    last_value integer NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


--
-- Name: order_counters_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.order_counters_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: order_counters_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.order_counters_id_seq OWNED BY public.order_counters.id;


--
-- Name: order_item_modifiers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.order_item_modifiers (
    id integer NOT NULL,
    order_item_id integer NOT NULL,
    modifier_id integer NOT NULL,
    unit_price numeric(10,2),
    quantity integer NOT NULL,
    cost_snapshot numeric(10,2)
);


--
-- Name: order_item_modifiers_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.order_item_modifiers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: order_item_modifiers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.order_item_modifiers_id_seq OWNED BY public.order_item_modifiers.id;


--
-- Name: order_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.order_items (
    id integer NOT NULL,
    order_id integer NOT NULL,
    product_id integer NOT NULL,
    quantity numeric(10,2),
    unit_price numeric(12,2),
    tax_amount numeric(12,2),
    subtotal numeric(12,2),
    notes character varying(255),
    removed_ingredients json
);


--
-- Name: order_items_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.order_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: order_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.order_items_id_seq OWNED BY public.order_items.id;


--
-- Name: orders; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.orders (
    id integer NOT NULL,
    company_id integer NOT NULL,
    branch_id integer NOT NULL,
    order_number character varying(20) NOT NULL,
    status character varying,
    subtotal numeric(12,2),
    tax_total numeric(12,2),
    total numeric(12,2),
    customer_id integer,
    delivery_type character varying,
    table_id integer,
    created_by_id integer,
    delivery_address character varying,
    delivery_notes character varying(500),
    delivery_fee numeric(10,2),
    delivery_customer_name character varying(100),
    delivery_customer_phone character varying(20),
    delivery_person_id integer,
    assigned_at timestamp without time zone,
    picked_up_at timestamp without time zone,
    delivered_at timestamp without time zone,
    customer_notes character varying(500),
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone,
    cancellation_status character varying,
    cancellation_reason character varying(255),
    cancellation_requested_at timestamp without time zone,
    cancellation_processed_at timestamp without time zone,
    cancellation_requested_by_id integer,
    cancellation_denied_reason character varying(255)
);


--
-- Name: orders_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.orders_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: orders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.orders_id_seq OWNED BY public.orders.id;


--
-- Name: payments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.payments (
    id integer NOT NULL,
    company_id integer NOT NULL,
    branch_id integer NOT NULL,
    user_id integer NOT NULL,
    order_id integer NOT NULL,
    amount numeric(12,2),
    method character varying,
    status character varying,
    transaction_id character varying(100),
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone
);


--
-- Name: payments_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.payments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: payments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.payments_id_seq OWNED BY public.payments.id;


--
-- Name: permission_categories; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.permission_categories (
    id uuid NOT NULL,
    company_id integer,
    name character varying(100) NOT NULL,
    code character varying(50) NOT NULL,
    description character varying(255),
    icon character varying(50),
    color character varying(7),
    is_system boolean NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone
);


--
-- Name: permissions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.permissions (
    id uuid NOT NULL,
    company_id integer,
    category_id uuid NOT NULL,
    code character varying(100) NOT NULL,
    name character varying(100) NOT NULL,
    description character varying(255),
    resource character varying(50) NOT NULL,
    action character varying(50) NOT NULL,
    is_system boolean NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone
);


--
-- Name: print_jobs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.print_jobs (
    id integer NOT NULL,
    company_id integer NOT NULL,
    order_id integer NOT NULL,
    status public.printjobstatus NOT NULL,
    attempts integer NOT NULL,
    last_error character varying,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone
);


--
-- Name: print_jobs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.print_jobs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: print_jobs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.print_jobs_id_seq OWNED BY public.print_jobs.id;


--
-- Name: product_modifiers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.product_modifiers (
    id integer NOT NULL,
    company_id integer NOT NULL,
    name character varying(100) NOT NULL,
    description character varying(255),
    extra_price numeric(10,2),
    is_active boolean NOT NULL
);


--
-- Name: product_modifiers_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.product_modifiers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: product_modifiers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.product_modifiers_id_seq OWNED BY public.product_modifiers.id;


--
-- Name: production_event_input_batches; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.production_event_input_batches (
    id uuid NOT NULL,
    production_event_input_id uuid NOT NULL,
    source_batch_id uuid NOT NULL,
    quantity_consumed numeric(18,4),
    cost_attributed numeric(18,4)
);


--
-- Name: production_event_inputs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.production_event_inputs (
    id uuid NOT NULL,
    production_event_id uuid NOT NULL,
    ingredient_id uuid NOT NULL,
    quantity double precision NOT NULL,
    cost_allocated numeric(18,4)
);


--
-- Name: production_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.production_events (
    id uuid NOT NULL,
    company_id integer NOT NULL,
    created_at timestamp without time zone NOT NULL,
    input_ingredient_id uuid,
    input_quantity double precision NOT NULL,
    input_cost_total numeric(18,2),
    notes character varying,
    output_ingredient_id uuid NOT NULL,
    output_batch_id uuid,
    output_quantity double precision NOT NULL,
    calculated_unit_cost numeric(18,6),
    user_id integer
);


--
-- Name: products; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.products (
    id integer NOT NULL,
    company_id integer NOT NULL,
    name character varying(200) NOT NULL,
    description character varying(500),
    price numeric(12,2),
    tax_rate numeric(5,2),
    stock numeric(10,2),
    image_url character varying(500),
    is_active boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone,
    category_id integer,
    active_recipe_id uuid
);


--
-- Name: products_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.products_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: products_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.products_id_seq OWNED BY public.products.id;


--
-- Name: recipe_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.recipe_items (
    id uuid NOT NULL,
    recipe_id uuid NOT NULL,
    ingredient_id uuid NOT NULL,
    company_id integer NOT NULL,
    gross_quantity numeric(10,4) NOT NULL,
    net_quantity numeric(10,4),
    measure_unit character varying(50) NOT NULL,
    calculated_cost numeric(12,2),
    created_at timestamp without time zone NOT NULL
);


--
-- Name: recipes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.recipes (
    id uuid NOT NULL,
    company_id integer NOT NULL,
    product_id integer NOT NULL,
    name character varying(200) NOT NULL,
    version integer NOT NULL,
    is_active boolean NOT NULL,
    recipe_type character varying(20) NOT NULL,
    batch_yield double precision NOT NULL,
    total_cost numeric(10,2),
    preparation_time integer NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone
);


--
-- Name: role_permissions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.role_permissions (
    id uuid NOT NULL,
    role_id uuid NOT NULL,
    permission_id uuid NOT NULL,
    granted_by integer,
    granted_at timestamp without time zone NOT NULL,
    expires_at timestamp without time zone
);


--
-- Name: roles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.roles (
    id uuid NOT NULL,
    company_id integer NOT NULL,
    name character varying(100) NOT NULL,
    code character varying(50) NOT NULL,
    description character varying(255),
    hierarchy_level integer NOT NULL,
    is_system boolean NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone
);


--
-- Name: subscriptions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.subscriptions (
    id integer NOT NULL,
    company_id integer NOT NULL,
    plan character varying(20) NOT NULL,
    status character varying(20) NOT NULL,
    started_at timestamp without time zone NOT NULL,
    current_period_start timestamp without time zone,
    current_period_end timestamp without time zone,
    cancelled_at timestamp without time zone,
    amount double precision NOT NULL,
    currency character varying(3) NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone
);


--
-- Name: subscriptions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.subscriptions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: subscriptions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.subscriptions_id_seq OWNED BY public.subscriptions.id;


--
-- Name: tables; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tables (
    id integer NOT NULL,
    branch_id integer NOT NULL,
    table_number integer NOT NULL,
    seat_count integer NOT NULL,
    status public.tablestatus NOT NULL,
    pos_x integer,
    pos_y integer,
    is_active boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone
);


--
-- Name: tables_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tables_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tables_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.tables_id_seq OWNED BY public.tables.id;


--
-- Name: unit_conversions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.unit_conversions (
    id uuid NOT NULL,
    from_unit character varying NOT NULL,
    to_unit character varying NOT NULL,
    factor double precision NOT NULL
);


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id integer NOT NULL,
    company_id integer NOT NULL,
    branch_id integer,
    role_id uuid,
    username character varying(50) NOT NULL,
    email character varying(100) NOT NULL,
    hashed_password character varying(255) NOT NULL,
    full_name character varying(100),
    role character varying(20) NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone,
    last_login timestamp without time zone
);


--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: audit_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs ALTER COLUMN id SET DEFAULT nextval('public.audit_logs_id_seq'::regclass);


--
-- Name: branches id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.branches ALTER COLUMN id SET DEFAULT nextval('public.branches_id_seq'::regclass);


--
-- Name: cash_closures id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cash_closures ALTER COLUMN id SET DEFAULT nextval('public.cash_closures_id_seq'::regclass);


--
-- Name: categories id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categories ALTER COLUMN id SET DEFAULT nextval('public.categories_id_seq'::regclass);


--
-- Name: companies id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.companies ALTER COLUMN id SET DEFAULT nextval('public.companies_id_seq'::regclass);


--
-- Name: customer_addresses id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_addresses ALTER COLUMN id SET DEFAULT nextval('public.customer_addresses_id_seq'::regclass);


--
-- Name: customers id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customers ALTER COLUMN id SET DEFAULT nextval('public.customers_id_seq'::regclass);


--
-- Name: delivery_shifts id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.delivery_shifts ALTER COLUMN id SET DEFAULT nextval('public.delivery_shifts_id_seq'::regclass);


--
-- Name: inventory id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory ALTER COLUMN id SET DEFAULT nextval('public.inventory_id_seq'::regclass);


--
-- Name: inventory_transactions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_transactions ALTER COLUMN id SET DEFAULT nextval('public.inventory_transactions_id_seq'::regclass);


--
-- Name: modifier_recipe_items id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.modifier_recipe_items ALTER COLUMN id SET DEFAULT nextval('public.modifier_recipe_items_id_seq'::regclass);


--
-- Name: order_audits id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_audits ALTER COLUMN id SET DEFAULT nextval('public.order_audits_id_seq'::regclass);


--
-- Name: order_counters id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_counters ALTER COLUMN id SET DEFAULT nextval('public.order_counters_id_seq'::regclass);


--
-- Name: order_item_modifiers id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_item_modifiers ALTER COLUMN id SET DEFAULT nextval('public.order_item_modifiers_id_seq'::regclass);


--
-- Name: order_items id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_items ALTER COLUMN id SET DEFAULT nextval('public.order_items_id_seq'::regclass);


--
-- Name: orders id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders ALTER COLUMN id SET DEFAULT nextval('public.orders_id_seq'::regclass);


--
-- Name: payments id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payments ALTER COLUMN id SET DEFAULT nextval('public.payments_id_seq'::regclass);


--
-- Name: print_jobs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.print_jobs ALTER COLUMN id SET DEFAULT nextval('public.print_jobs_id_seq'::regclass);


--
-- Name: product_modifiers id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_modifiers ALTER COLUMN id SET DEFAULT nextval('public.product_modifiers_id_seq'::regclass);


--
-- Name: products id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.products ALTER COLUMN id SET DEFAULT nextval('public.products_id_seq'::regclass);


--
-- Name: subscriptions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subscriptions ALTER COLUMN id SET DEFAULT nextval('public.subscriptions_id_seq'::regclass);


--
-- Name: tables id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tables ALTER COLUMN id SET DEFAULT nextval('public.tables_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: audit_logs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.audit_logs (id, company_id, user_id, username, action, entity_type, entity_id, old_value, new_value, description, ip_address, user_agent, branch_id, created_at) FROM stdin;
1	1	1	Kate	login_success	\N	\N	null	null	Login Smart Auth: Kate	\N	\N	\N	2026-02-09 22:15:52.150735
\.


--
-- Data for Name: branches; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.branches (id, company_id, name, code, address, phone, is_active, is_main, created_at, updated_at) FROM stdin;
1	1	Sede Principal	MAIN	Calle 70 	\N	t	t	2026-02-09 22:02:54.443177	\N
\.


--
-- Data for Name: cash_closures; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.cash_closures (id, company_id, branch_id, user_id, opened_at, closed_at, initial_cash, expected_cash, expected_card, expected_transfer, expected_total, real_cash, real_card, real_transfer, real_total, difference, status, notes) FROM stdin;
\.


--
-- Data for Name: categories; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.categories (id, company_id, name, description, is_active, created_at, updated_at) FROM stdin;
1	1	Hamburguesa		t	2026-02-09 22:13:12.258031	\N
\.


--
-- Data for Name: companies; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.companies (id, name, slug, legal_name, tax_id, owner_name, owner_email, owner_phone, plan, is_active, created_at, updated_at) FROM stdin;
1	Kate	kate	Kate	90080010080	Katerine toribamo larrs	kate@gmail.com	3053074359	free	t	2026-02-09 22:02:54.430144	\N
\.


--
-- Data for Name: customer_addresses; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.customer_addresses (id, customer_id, name, address, details, latitude, longitude, is_default) FROM stdin;
\.


--
-- Data for Name: customers; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.customers (id, company_id, phone, full_name, email, notes, is_active, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: delivery_shifts; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.delivery_shifts (id, company_id, branch_id, delivery_person_id, started_at, ended_at, total_orders, total_delivered, total_cancelled, total_earnings, expected_cash, cash_collected, status, closing_notes) FROM stdin;
\.


--
-- Data for Name: ingredient_batches; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.ingredient_batches (id, ingredient_id, branch_id, quantity_initial, quantity_remaining, cost_per_unit, total_cost, acquired_at, is_active, supplier) FROM stdin;
a19390b3-f05a-48b1-a9c8-380e90d0a79e	703abbdb-6788-4da1-922f-a361762e289b	1	100.0000	100.0000	1000.000000	100000.00	2026-02-09 22:07:25.587242	t	\N
3306a310-a287-461d-a177-d6d705812fa3	89c1e3b3-4f94-460f-8e41-baf5ca29a35d	1	1000.0000	1000.0000	5.000000	5000.00	2026-02-09 22:10:16.035349	t	\N
6c7d2fc6-4d04-4459-b412-a2acaa22d80b	4cc75c4e-0b0c-434c-8bb6-9e33480d6439	1	3000.0000	3000.0000	20.000000	60000.00	2026-02-09 22:10:44.169072	t	\N
bb520f3b-d4c4-4cbb-a5c8-4ac7ae078567	3b353150-d34e-444d-8b40-fa9f5dfb29e0	1	100.0000	100.0000	300.000000	30000.00	2026-02-09 22:11:11.317322	t	\N
1d5a2ac6-6738-4c6e-b875-76587899942e	291168f8-f422-4f28-acd9-accf52fc213f	1	10000.0000	0.0000	40.000000	400000.00	2026-02-09 22:07:57.542492	f	\N
003aa6e9-df01-4dd9-aa20-33bb74e0f068	27261432-f349-4b99-ad57-89f6787b9271	1	60.0000	50.0000	400.000000	24000.00	2026-02-09 22:09:06.219858	t	\N
d232f39f-f631-4670-a4fb-92d1550003d9	7d802d27-a0c0-4d4c-bd24-6651b5aaaefb	1	1000.0000	930.0000	70.000000	70000.00	2026-02-09 22:09:26.030795	t	\N
10b6b43b-3f50-4712-8781-600fa94e6c51	9a243d35-95b4-4ac6-9cac-c6866652d1de	1	10000.0000	10000.0000	40.890000	408900.00	2026-02-09 22:12:10.494435	t	Internal Production
00943645-b9e8-4a8e-be29-691b0576dcb3	399224a8-7cbc-4a97-b89e-361de03079c2	1	20.0000	20.0000	2500.000000	50000.00	2026-02-09 22:17:12.486598	t	Compra Inicial
\.


--
-- Data for Name: ingredient_cost_history; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.ingredient_cost_history (id, ingredient_id, previous_cost, new_cost, reason, user_id, created_at) FROM stdin;
\.


--
-- Data for Name: ingredient_inventory; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.ingredient_inventory (id, branch_id, ingredient_id, stock, min_stock, max_stock, updated_at) FROM stdin;
135f39f9-1aeb-428b-8bfd-bb63e5cc8918	1	703abbdb-6788-4da1-922f-a361762e289b	100.000	0.000	\N	2026-02-09 22:07:25.578536
1c6e2983-4501-4202-a269-770a02cc055d	1	89c1e3b3-4f94-460f-8e41-baf5ca29a35d	1000.000	0.000	\N	2026-02-09 22:10:16.01601
f7f19afb-c013-4ab2-a9e1-1eedba5323f9	1	4cc75c4e-0b0c-434c-8bb6-9e33480d6439	3000.000	0.000	\N	2026-02-09 22:10:44.162343
4e84b07b-6e33-4d04-a890-caa3bb8db00d	1	3b353150-d34e-444d-8b40-fa9f5dfb29e0	100.000	0.000	\N	2026-02-09 22:11:11.31172
cb171fca-ac66-4c0f-adb4-74451ec19ce1	1	291168f8-f422-4f28-acd9-accf52fc213f	0.000	0.000	\N	2026-02-09 22:07:57.5363
9f797c81-b902-4f66-820d-c288b0471423	1	27261432-f349-4b99-ad57-89f6787b9271	50.000	0.000	\N	2026-02-09 22:09:06.213225
a1ca8378-d861-4f58-9fc6-2b5eb67fa615	1	7d802d27-a0c0-4d4c-bd24-6651b5aaaefb	930.000	0.000	\N	2026-02-09 22:09:26.026761
9e6f7f76-3be4-4c11-a534-b90b8857bb10	1	9a243d35-95b4-4ac6-9cac-c6866652d1de	10000.000	0.000	\N	2026-02-09 22:12:10.489542
025feee9-3f61-410a-9d22-b47f9bfed121	1	399224a8-7cbc-4a97-b89e-361de03079c2	20.000	0.000	\N	2026-02-09 22:17:12.460191
\.


--
-- Data for Name: ingredient_transactions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.ingredient_transactions (id, inventory_id, transaction_type, quantity, balance_after, reference_id, reason, user_id, created_at) FROM stdin;
2eb9f7f6-7090-4f6d-b862-cffbef19d064	135f39f9-1aeb-428b-8bfd-bb63e5cc8918	IN	100.000	100.000	\N	Stock inicial al crear insumo	1	2026-02-09 22:07:25.594304
6457b434-43e4-4a6a-af7f-cd37fc524456	cb171fca-ac66-4c0f-adb4-74451ec19ce1	IN	10000.000	10000.000	\N	Stock inicial al crear insumo	1	2026-02-09 22:07:57.546183
ba0d10ee-5cd1-4e3c-96eb-49fe8ad5b096	9f797c81-b902-4f66-820d-c288b0471423	IN	60.000	60.000	\N	Stock inicial al crear insumo	1	2026-02-09 22:09:06.223291
494c6bd2-152e-4414-bb20-1adcdbf64f57	a1ca8378-d861-4f58-9fc6-2b5eb67fa615	IN	1000.000	1000.000	\N	Stock inicial al crear insumo	1	2026-02-09 22:09:26.033689
4ea79c34-9918-4036-a6d0-06a00706e75b	1c6e2983-4501-4202-a269-770a02cc055d	IN	1000.000	1000.000	\N	Stock inicial al crear insumo	1	2026-02-09 22:10:16.041617
d095762b-118e-48d8-85b6-43a52fe35a63	f7f19afb-c013-4ab2-a9e1-1eedba5323f9	IN	3000.000	3000.000	\N	Stock inicial al crear insumo	1	2026-02-09 22:10:44.173769
9fe0511e-f1f6-4842-8eba-d1ca401243e2	4e84b07b-6e33-4d04-a890-caa3bb8db00d	IN	100.000	100.000	\N	Stock inicial al crear insumo	1	2026-02-09 22:11:11.321429
330cd6d5-8c02-4158-bd2b-cae9353fbddc	cb171fca-ac66-4c0f-adb4-74451ec19ce1	PRODUCTION_OUT	-10000.000	0.000	\N	Producci├│n de Carne hamburguesa 	1	2026-02-09 22:12:10.457692
22fe124d-4cf7-402a-b3c0-6788d5f3d58e	9f797c81-b902-4f66-820d-c288b0471423	PRODUCTION_OUT	-10.000	50.000	\N	Producci├│n de Carne hamburguesa 	1	2026-02-09 22:12:10.469857
1c3a8357-c288-4972-8540-f2a167898dcc	a1ca8378-d861-4f58-9fc6-2b5eb67fa615	PRODUCTION_OUT	-70.000	930.000	\N	Producci├│n de Carne hamburguesa 	1	2026-02-09 22:12:10.481256
eb43ae8c-250f-4a34-8603-19c8b82306f0	9e6f7f76-3be4-4c11-a534-b90b8857bb10	PRODUCTION_IN	10000.000	10000.000	\N	Producci├│n Interna	1	2026-02-09 22:12:10.497815
f5f6ea57-00a7-43a3-bf90-14b9dff0e555	025feee9-3f61-410a-9d22-b47f9bfed121	IN	20.000	20.000	\N	Stock inicial de coca cola zero	1	2026-02-09 22:17:12.499559
\.


--
-- Data for Name: ingredients; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.ingredients (name, sku, base_unit, current_cost, last_cost, yield_factor, category_id, company_id, ingredient_type, id, is_active, created_at, updated_at) FROM stdin;
Pan hamburguesa 	ING-8LN573	und	1000.0000	1000.0000	1	\N	1	RAW	703abbdb-6788-4da1-922f-a361762e289b	t	2026-02-09 22:07:25.520906	\N
Carne	ING-M0SO64	g	40.0000	40.0000	1	\N	1	RAW	291168f8-f422-4f28-acd9-accf52fc213f	t	2026-02-09 22:07:57.464053	\N
Huevos 	ING-SSFLUF	und	400.0000	400.0000	1	\N	1	RAW	27261432-f349-4b99-ad57-89f6787b9271	t	2026-02-09 22:09:06.127936	\N
Pimienta 	ING-S1URT8	g	70.0000	70.0000	1	\N	1	RAW	7d802d27-a0c0-4d4c-bd24-6651b5aaaefb	t	2026-02-09 22:09:25.989834	\N
Tomate 	ING-MOCV6A	g	5.0000	5.0000	1	\N	1	RAW	89c1e3b3-4f94-460f-8e41-baf5ca29a35d	t	2026-02-09 22:10:15.877238	\N
Tocineta 	ING-C81PK0	g	20.0000	20.0000	1	\N	1	RAW	4cc75c4e-0b0c-434c-8bb6-9e33480d6439	t	2026-02-09 22:10:44.032126	\N
Queso	ING-YZQSH3	und	300.0000	300.0000	1	\N	1	RAW	3b353150-d34e-444d-8b40-fa9f5dfb29e0	t	2026-02-09 22:11:11.260986	\N
Carne hamburguesa 	ING-AK6KPU	g	40.8900	0.0000	1	\N	1	PROCESSED	9a243d35-95b4-4ac6-9cac-c6866652d1de	t	2026-02-09 22:12:10.430003	\N
coca cola zero	BEV-COCA-33CB0A	UNIDAD	2500.0000	2500.0000	1	\N	1	MERCHANDISE	399224a8-7cbc-4a97-b89e-361de03079c2	t	2026-02-09 22:17:12.455688	\N
\.


--
-- Data for Name: inventory; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.inventory (id, branch_id, product_id, stock, min_stock, max_stock, bin_location, updated_at) FROM stdin;
\.


--
-- Data for Name: inventory_count_items; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.inventory_count_items (ingredient_id, expected_quantity, counted_quantity, id, count_id, cost_per_unit) FROM stdin;
\.


--
-- Data for Name: inventory_counts; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.inventory_counts (branch_id, status, notes, id, company_id, user_id, created_at, closed_at, applied_at) FROM stdin;
\.


--
-- Data for Name: inventory_transactions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.inventory_transactions (id, inventory_id, transaction_type, quantity, balance_after, reference_id, reason, user_id, created_at) FROM stdin;
\.


--
-- Data for Name: modifier_recipe_items; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.modifier_recipe_items (id, modifier_id, ingredient_product_id, ingredient_id, quantity, unit) FROM stdin;
1	1	\N	3b353150-d34e-444d-8b40-fa9f5dfb29e0	10.000	und
\.


--
-- Data for Name: order_audits; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.order_audits (id, order_id, old_status, new_status, changed_by_user_id, changed_at, meta) FROM stdin;
\.


--
-- Data for Name: order_counters; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.order_counters (id, company_id, branch_id, counter_type, prefix, last_value, updated_at) FROM stdin;
\.


--
-- Data for Name: order_item_modifiers; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.order_item_modifiers (id, order_item_id, modifier_id, unit_price, quantity, cost_snapshot) FROM stdin;
\.


--
-- Data for Name: order_items; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.order_items (id, order_id, product_id, quantity, unit_price, tax_amount, subtotal, notes, removed_ingredients) FROM stdin;
\.


--
-- Data for Name: orders; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.orders (id, company_id, branch_id, order_number, status, subtotal, tax_total, total, customer_id, delivery_type, table_id, created_by_id, delivery_address, delivery_notes, delivery_fee, delivery_customer_name, delivery_customer_phone, delivery_person_id, assigned_at, picked_up_at, delivered_at, customer_notes, created_at, updated_at, cancellation_status, cancellation_reason, cancellation_requested_at, cancellation_processed_at, cancellation_requested_by_id, cancellation_denied_reason) FROM stdin;
\.


--
-- Data for Name: payments; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.payments (id, company_id, branch_id, user_id, order_id, amount, method, status, transaction_id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: permission_categories; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.permission_categories (id, company_id, name, code, description, icon, color, is_system, is_active, created_at, updated_at) FROM stdin;
4a2887af-eef8-43f4-a8cc-f2d350aa9a06	\N	Productos	products	\N	inventory_2	#4CAF50	t	t	2026-02-09 21:59:35.215767	\N
ceb3f26b-4704-4fbd-9f86-f71e5e668e4c	\N	Pedidos	orders	\N	receipt_long	#2196F3	t	t	2026-02-09 21:59:35.227068	\N
1c13b39b-bf09-47bc-a63f-ca0da50cbd73	\N	Inventario	inventory	\N	warehouse	#FF9800	t	t	2026-02-09 21:59:35.23149	\N
0f67c228-e642-4619-86ce-ce5a0ec35cab	\N	Caja	cash	\N	point_of_sale	#9C27B0	t	t	2026-02-09 21:59:35.235827	\N
c7a01cd8-d197-4fa8-b52d-42183fc68f52	\N	Reportes	reports	\N	analytics	#607D8B	t	t	2026-02-09 21:59:35.239142	\N
f352a664-5662-453e-aac7-b3817e6db125	\N	Usuarios	users	\N	people	#F44336	t	t	2026-02-09 21:59:35.241788	\N
a94ead7b-20f6-4883-b7c5-155d95fb7266	\N	Sucursales	branches	\N	store	#00BCD4	t	t	2026-02-09 21:59:35.2445	\N
ff04579b-b72b-4719-964b-0f5d9185ce01	\N	Configuraci├│n	settings	\N	settings	#795548	t	t	2026-02-09 21:59:35.247542	\N
6f60939d-2e9e-47b4-9313-96680444b173	\N	Administraci├│n	admin	\N	admin_panel_settings	#673AB7	t	t	2026-02-09 21:59:35.25006	\N
\.


--
-- Data for Name: permissions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.permissions (id, company_id, category_id, code, name, description, resource, action, is_system, is_active, created_at, updated_at) FROM stdin;
8f117173-4239-4ea0-a533-0a9e71678c05	\N	4a2887af-eef8-43f4-a8cc-f2d350aa9a06	products.create	Crear productos	\N	products	create	t	t	2026-02-09 21:59:35.259332	\N
7f9a8ede-33f2-47e8-8a61-3a0d80eb7a55	\N	4a2887af-eef8-43f4-a8cc-f2d350aa9a06	products.read	Ver productos	\N	products	read	t	t	2026-02-09 21:59:35.259802	\N
b9576b8f-0dea-4a68-8396-f3c2aad2eab3	\N	4a2887af-eef8-43f4-a8cc-f2d350aa9a06	products.update	Editar productos	\N	products	update	t	t	2026-02-09 21:59:35.260343	\N
6b3d33a4-3825-4d70-a0b0-3294acd8fde5	\N	4a2887af-eef8-43f4-a8cc-f2d350aa9a06	products.delete	Eliminar productos	\N	products	delete	t	t	2026-02-09 21:59:35.260791	\N
d1c7d837-21f6-46d5-985f-f692a33bdb1c	\N	ceb3f26b-4704-4fbd-9f86-f71e5e668e4c	orders.create	Crear pedidos	\N	orders	create	t	t	2026-02-09 21:59:35.261168	\N
f0b49401-cf3e-431a-8323-1899d7a896bf	\N	ceb3f26b-4704-4fbd-9f86-f71e5e668e4c	orders.read	Ver pedidos	\N	orders	read	t	t	2026-02-09 21:59:35.261507	\N
dc29e23c-b356-4036-a92e-2a1af948965b	\N	ceb3f26b-4704-4fbd-9f86-f71e5e668e4c	orders.update	Actualizar pedidos	\N	orders	update	t	t	2026-02-09 21:59:35.261819	\N
dcc21cd0-1a73-4a91-bc4f-f18267db396e	\N	ceb3f26b-4704-4fbd-9f86-f71e5e668e4c	orders.cancel	Cancelar pedidos	\N	orders	cancel	t	t	2026-02-09 21:59:35.262222	\N
ecde2a02-99da-48fa-b4ce-c203fdbf8713	\N	1c13b39b-bf09-47bc-a63f-ca0da50cbd73	inventory.read	Ver inventario	\N	inventory	read	t	t	2026-02-09 21:59:35.262465	\N
633d14fa-8f41-43e4-b298-c9bebcc090da	\N	1c13b39b-bf09-47bc-a63f-ca0da50cbd73	inventory.adjust	Ajustar inventario	\N	inventory	adjust	t	t	2026-02-09 21:59:35.262864	\N
33d18ec2-71d9-49c1-a1db-4485639ced0b	\N	0f67c228-e642-4619-86ce-ce5a0ec35cab	cash.open	Abrir caja	\N	cash	open	t	t	2026-02-09 21:59:35.263267	\N
a58264b8-7323-493d-a4fc-b31faa15a889	\N	0f67c228-e642-4619-86ce-ce5a0ec35cab	cash.close	Cerrar caja	\N	cash	close	t	t	2026-02-09 21:59:35.26371	\N
c486aadf-e5d2-4d8d-8562-7f7f8be7da65	\N	0f67c228-e642-4619-86ce-ce5a0ec35cab	cash.read	Ver movimientos	\N	cash	read	t	t	2026-02-09 21:59:35.264179	\N
71dd944f-458e-45b8-9eb9-37a283abe7b8	\N	c7a01cd8-d197-4fa8-b52d-42183fc68f52	reports.sales	Ver reportes de ventas	\N	reports	sales	t	t	2026-02-09 21:59:35.264767	\N
ea41f39b-26f9-490a-88f6-73d2adb9c077	\N	c7a01cd8-d197-4fa8-b52d-42183fc68f52	reports.financial	Ver reportes financieros	\N	reports	financial	t	t	2026-02-09 21:59:35.265556	\N
82af820c-2bea-47dd-a7c6-04ecade15c28	\N	f352a664-5662-453e-aac7-b3817e6db125	users.create	Crear usuarios	\N	users	create	t	t	2026-02-09 21:59:35.266018	\N
a8de728b-8741-4d2a-acc5-76a74fe26643	\N	f352a664-5662-453e-aac7-b3817e6db125	users.read	Ver usuarios	\N	users	read	t	t	2026-02-09 21:59:35.266448	\N
0aff922f-56ca-43ed-8b40-d02064843932	\N	f352a664-5662-453e-aac7-b3817e6db125	users.update	Editar usuarios	\N	users	update	t	t	2026-02-09 21:59:35.266843	\N
0ab5d08c-fd2d-4789-8ed9-37a70fad27d9	\N	f352a664-5662-453e-aac7-b3817e6db125	users.delete	Eliminar usuarios	\N	users	delete	t	t	2026-02-09 21:59:35.267245	\N
8d534ca1-12cd-44e5-ac17-5cb9b5b9d3f1	\N	ff04579b-b72b-4719-964b-0f5d9185ce01	settings.read	Ver configuraci├│n	\N	settings	read	t	t	2026-02-09 21:59:35.267632	\N
52d6fee7-733d-435c-a91e-043db2012180	\N	ff04579b-b72b-4719-964b-0f5d9185ce01	settings.update	Modificar configuraci├│n	\N	settings	update	t	t	2026-02-09 21:59:35.268123	\N
0897e7e4-f24d-4baf-bbad-831d883a9b12	\N	6f60939d-2e9e-47b4-9313-96680444b173	roles.create	Crear roles	\N	roles	create	t	t	2026-02-09 21:59:35.268505	\N
1ab24f92-edd3-4d6b-a5c4-412eee5886df	\N	6f60939d-2e9e-47b4-9313-96680444b173	roles.read	Ver roles	\N	roles	read	t	t	2026-02-09 21:59:35.268881	\N
2f1a8bea-5d90-45c3-ae44-6b38bee69786	\N	6f60939d-2e9e-47b4-9313-96680444b173	roles.update	Editar roles	\N	roles	update	t	t	2026-02-09 21:59:35.26927	\N
79bcea13-ae53-499a-b0cb-8e8a2caeab99	\N	6f60939d-2e9e-47b4-9313-96680444b173	roles.delete	Eliminar roles	\N	roles	delete	t	t	2026-02-09 21:59:35.269699	\N
d38fe066-ade1-4f42-9148-7d246dc7630d	\N	6f60939d-2e9e-47b4-9313-96680444b173	permissions.read	Ver permisos	\N	permissions	read	t	t	2026-02-09 21:59:35.270122	\N
3ad6d9e3-0562-4fcf-8d44-07abea052e3e	\N	6f60939d-2e9e-47b4-9313-96680444b173	permissions.update	Asignar permisos	\N	permissions	update	t	t	2026-02-09 21:59:35.270508	\N
317387ea-47c7-42ee-9b15-a4ffdb43f020	\N	6f60939d-2e9e-47b4-9313-96680444b173	categories.read	Ver categor├¡as	\N	categories	read	t	t	2026-02-09 21:59:35.270883	\N
d4571f05-7878-4433-85f2-7f6c493a79ab	\N	6f60939d-2e9e-47b4-9313-96680444b173	categories.create	Crear categor├¡as	\N	categories	create	t	t	2026-02-09 21:59:35.271272	\N
5c8ed432-bcdc-4d04-974e-76cb5c3a0547	\N	a94ead7b-20f6-4883-b7c5-155d95fb7266	branches.read	Ver sucursales	\N	branches	read	t	t	2026-02-09 21:59:35.27171	\N
b8708661-9623-4ac5-9b82-8555bf982311	\N	a94ead7b-20f6-4883-b7c5-155d95fb7266	branches.create	Crear sucursales	\N	branches	create	t	t	2026-02-09 21:59:35.27216	\N
b405c771-43f7-4ed7-9c58-d845a971eff2	\N	a94ead7b-20f6-4883-b7c5-155d95fb7266	branches.update	Editar sucursales	\N	branches	update	t	t	2026-02-09 21:59:35.272542	\N
d2db46a4-3848-466e-85f9-cd2d653a5c5e	\N	a94ead7b-20f6-4883-b7c5-155d95fb7266	branches.delete	Eliminar sucursales	\N	branches	delete	t	t	2026-02-09 21:59:35.27279	\N
\.


--
-- Data for Name: print_jobs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.print_jobs (id, company_id, order_id, status, attempts, last_error, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: product_modifiers; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.product_modifiers (id, company_id, name, description, extra_price, is_active) FROM stdin;
1	1	queso		7000.00	t
\.


--
-- Data for Name: production_event_input_batches; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.production_event_input_batches (id, production_event_input_id, source_batch_id, quantity_consumed, cost_attributed) FROM stdin;
94030350-3bad-4edc-85dc-55c9478c3f5a	1e0bf8f3-71a5-4f09-9022-2935aa28f05c	1d5a2ac6-6738-4c6e-b875-76587899942e	10000.0000	400000.0000
ada83ce6-83e7-4f7f-83f5-e4190b391420	c99edff3-cfff-408c-9928-60e1423c3e5f	003aa6e9-df01-4dd9-aa20-33bb74e0f068	10.0000	4000.0000
89d4cc41-2127-44fc-8921-b165a0ea60a5	13266281-d089-421c-b578-dc24150654d8	d232f39f-f631-4670-a4fb-92d1550003d9	70.0000	4900.0000
\.


--
-- Data for Name: production_event_inputs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.production_event_inputs (id, production_event_id, ingredient_id, quantity, cost_allocated) FROM stdin;
1e0bf8f3-71a5-4f09-9022-2935aa28f05c	5234238c-1ef7-4de4-ac8b-e6b25c914741	291168f8-f422-4f28-acd9-accf52fc213f	10000	400000.0000
c99edff3-cfff-408c-9928-60e1423c3e5f	5234238c-1ef7-4de4-ac8b-e6b25c914741	27261432-f349-4b99-ad57-89f6787b9271	10	4000.0000
13266281-d089-421c-b578-dc24150654d8	5234238c-1ef7-4de4-ac8b-e6b25c914741	7d802d27-a0c0-4d4c-bd24-6651b5aaaefb	70	4900.0000
\.


--
-- Data for Name: production_events; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.production_events (id, company_id, created_at, input_ingredient_id, input_quantity, input_cost_total, notes, output_ingredient_id, output_batch_id, output_quantity, calculated_unit_cost, user_id) FROM stdin;
5234238c-1ef7-4de4-ac8b-e6b25c914741	1	2026-02-09 22:12:10.517724	291168f8-f422-4f28-acd9-accf52fc213f	10000	408900.00	\N	9a243d35-95b4-4ac6-9cac-c6866652d1de	10b6b43b-3f50-4712-8781-600fa94e6c51	10000	40.890000	1
\.


--
-- Data for Name: products; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.products (id, company_id, name, description, price, tax_rate, stock, image_url, is_active, created_at, updated_at, category_id, active_recipe_id) FROM stdin;
1	1	Bueger bacon 	\N	20000.00	0.00	0.00	/uploads/eaa37f49-6862-4965-9dd0-e442d590427c.jpg	t	2026-02-09 22:14:22.824425	\N	1	\N
2	1	coca cola zero	Bebida Venta Directa	3999.00	0.00	0.00		t	2026-02-09 22:17:12.509357	\N	\N	\N
\.


--
-- Data for Name: recipe_items; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.recipe_items (id, recipe_id, ingredient_id, company_id, gross_quantity, net_quantity, measure_unit, calculated_cost, created_at) FROM stdin;
49deb220-c8fc-4daa-964b-86a45ea022c1	e57cc8a7-8fd8-4440-aaf7-a743d0cbffa9	9a243d35-95b4-4ac6-9cac-c6866652d1de	1	140.0000	\N	g	5724.60	2026-02-09 22:14:22.933758
65797dbf-bade-420d-9db5-aabd4fda050d	e57cc8a7-8fd8-4440-aaf7-a743d0cbffa9	703abbdb-6788-4da1-922f-a361762e289b	1	1.0000	\N	und	1000.00	2026-02-09 22:14:22.944243
72f4698a-69b1-4f71-a847-2c7fc93dd932	e57cc8a7-8fd8-4440-aaf7-a743d0cbffa9	89c1e3b3-4f94-460f-8e41-baf5ca29a35d	1	2.0000	\N	g	10.00	2026-02-09 22:14:22.946983
8d4466d9-cb72-40a6-80d0-d608ce12c0e8	e57cc8a7-8fd8-4440-aaf7-a743d0cbffa9	4cc75c4e-0b0c-434c-8bb6-9e33480d6439	1	3.0000	\N	g	60.00	2026-02-09 22:14:22.949124
67bed26c-290c-4991-af12-62d582527d39	287fb249-2bac-49e1-8d48-031fd53ce371	399224a8-7cbc-4a97-b89e-361de03079c2	1	1.0000	1.0000	UNIDAD	2500.00	2026-02-09 22:17:12.517438
\.


--
-- Data for Name: recipes; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.recipes (id, company_id, product_id, name, version, is_active, recipe_type, batch_yield, total_cost, preparation_time, created_at, updated_at) FROM stdin;
e57cc8a7-8fd8-4440-aaf7-a743d0cbffa9	1	1	Bueger bacon 	1	t	REAL	1	6794.60	0	2026-02-09 22:14:22.920091	\N
287fb249-2bac-49e1-8d48-031fd53ce371	1	2	Receta Auto: coca cola zero	1	t	AUTO	1	0.00	0	2026-02-09 22:17:12.513147	\N
\.


--
-- Data for Name: role_permissions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.role_permissions (id, role_id, permission_id, granted_by, granted_at, expires_at) FROM stdin;
5409ebea-2235-40c0-a3bc-bb631b704d7a	74fd8c58-32e7-49d9-b9c5-87b8b75575a5	5c8ed432-bcdc-4d04-974e-76cb5c3a0547	\N	2026-02-09 22:02:54.46865	\N
e833ab07-645c-4fda-bb2a-28bd9df0b8ee	74fd8c58-32e7-49d9-b9c5-87b8b75575a5	c486aadf-e5d2-4d8d-8562-7f7f8be7da65	\N	2026-02-09 22:02:54.468825	\N
27768fff-4e8e-42df-8e5f-8646be708d44	74fd8c58-32e7-49d9-b9c5-87b8b75575a5	6b3d33a4-3825-4d70-a0b0-3294acd8fde5	\N	2026-02-09 22:02:54.468947	\N
a34bb8b8-ffb5-4b08-8d9f-e47cc8015520	74fd8c58-32e7-49d9-b9c5-87b8b75575a5	ea41f39b-26f9-490a-88f6-73d2adb9c077	\N	2026-02-09 22:02:54.469059	\N
353559b0-8a28-4bd9-9bf4-7f59b77e9029	74fd8c58-32e7-49d9-b9c5-87b8b75575a5	d2db46a4-3848-466e-85f9-cd2d653a5c5e	\N	2026-02-09 22:02:54.46917	\N
8035d949-ee60-4d1e-99aa-693b91cd4fa8	74fd8c58-32e7-49d9-b9c5-87b8b75575a5	79bcea13-ae53-499a-b0cb-8e8a2caeab99	\N	2026-02-09 22:02:54.46928	\N
bcb2b240-f70b-4f53-8d9e-4616bc2e0e21	74fd8c58-32e7-49d9-b9c5-87b8b75575a5	0897e7e4-f24d-4baf-bbad-831d883a9b12	\N	2026-02-09 22:02:54.469398	\N
be68b188-2925-4ea3-883b-48c05a91aaf5	74fd8c58-32e7-49d9-b9c5-87b8b75575a5	633d14fa-8f41-43e4-b298-c9bebcc090da	\N	2026-02-09 22:02:54.469509	\N
314f064f-5a6b-48e9-9c4b-2a839867f654	74fd8c58-32e7-49d9-b9c5-87b8b75575a5	71dd944f-458e-45b8-9eb9-37a283abe7b8	\N	2026-02-09 22:02:54.469618	\N
6b522ae7-31eb-4749-8f70-2229ef1af733	74fd8c58-32e7-49d9-b9c5-87b8b75575a5	a58264b8-7323-493d-a4fc-b31faa15a889	\N	2026-02-09 22:02:54.469759	\N
66329d56-7c03-4586-b76e-c4fba387a80a	74fd8c58-32e7-49d9-b9c5-87b8b75575a5	317387ea-47c7-42ee-9b15-a4ffdb43f020	\N	2026-02-09 22:02:54.46988	\N
d72549a7-c64c-4d23-9962-e4c418dde04b	74fd8c58-32e7-49d9-b9c5-87b8b75575a5	0aff922f-56ca-43ed-8b40-d02064843932	\N	2026-02-09 22:02:54.469999	\N
686755a4-f2c0-4af1-97fc-5adff6b09040	74fd8c58-32e7-49d9-b9c5-87b8b75575a5	ecde2a02-99da-48fa-b4ce-c203fdbf8713	\N	2026-02-09 22:02:54.470116	\N
f61d516d-6c11-41dc-b85c-682a4f3977cc	74fd8c58-32e7-49d9-b9c5-87b8b75575a5	33d18ec2-71d9-49c1-a1db-4485639ced0b	\N	2026-02-09 22:02:54.470222	\N
939d2b2c-23bf-4265-9bbe-5f0ffb466beb	74fd8c58-32e7-49d9-b9c5-87b8b75575a5	b9576b8f-0dea-4a68-8396-f3c2aad2eab3	\N	2026-02-09 22:02:54.470323	\N
ee9ae842-64aa-4245-aaff-1e82a56a21b4	74fd8c58-32e7-49d9-b9c5-87b8b75575a5	0ab5d08c-fd2d-4789-8ed9-37a70fad27d9	\N	2026-02-09 22:02:54.47046	\N
2afddbf3-ad6c-496e-b2ff-051c6842e168	74fd8c58-32e7-49d9-b9c5-87b8b75575a5	8f117173-4239-4ea0-a533-0a9e71678c05	\N	2026-02-09 22:02:54.470569	\N
f2c1fa94-a37d-4ad0-ac17-c23007c879a6	74fd8c58-32e7-49d9-b9c5-87b8b75575a5	2f1a8bea-5d90-45c3-ae44-6b38bee69786	\N	2026-02-09 22:02:54.470673	\N
22fb4174-b734-4184-bdfc-d3ccb5d5ac4e	74fd8c58-32e7-49d9-b9c5-87b8b75575a5	dcc21cd0-1a73-4a91-bc4f-f18267db396e	\N	2026-02-09 22:02:54.470774	\N
f8da27c7-7190-4792-a7f6-cb9343436184	74fd8c58-32e7-49d9-b9c5-87b8b75575a5	82af820c-2bea-47dd-a7c6-04ecade15c28	\N	2026-02-09 22:02:54.47088	\N
efe82fe1-29bc-4677-a0c3-0a5f030bdea0	74fd8c58-32e7-49d9-b9c5-87b8b75575a5	7f9a8ede-33f2-47e8-8a61-3a0d80eb7a55	\N	2026-02-09 22:02:54.470981	\N
34b73cc1-739f-491f-bc54-0abc7de84a3d	74fd8c58-32e7-49d9-b9c5-87b8b75575a5	8d534ca1-12cd-44e5-ac17-5cb9b5b9d3f1	\N	2026-02-09 22:02:54.471081	\N
3e82a3f9-34a1-45e9-847b-7e89354e1d78	74fd8c58-32e7-49d9-b9c5-87b8b75575a5	1ab24f92-edd3-4d6b-a5c4-412eee5886df	\N	2026-02-09 22:02:54.47118	\N
cf556959-3846-4028-95b5-2e7d35c01e2f	74fd8c58-32e7-49d9-b9c5-87b8b75575a5	a8de728b-8741-4d2a-acc5-76a74fe26643	\N	2026-02-09 22:02:54.471284	\N
79126d0e-6e29-4b3b-913b-227af53cc628	74fd8c58-32e7-49d9-b9c5-87b8b75575a5	dc29e23c-b356-4036-a92e-2a1af948965b	\N	2026-02-09 22:02:54.471392	\N
6314b036-2d04-4931-8223-2aea8c4adc09	74fd8c58-32e7-49d9-b9c5-87b8b75575a5	3ad6d9e3-0562-4fcf-8d44-07abea052e3e	\N	2026-02-09 22:02:54.471502	\N
1e9d4881-e1ff-4eeb-a78f-2771370b8a9a	74fd8c58-32e7-49d9-b9c5-87b8b75575a5	f0b49401-cf3e-431a-8323-1899d7a896bf	\N	2026-02-09 22:02:54.471607	\N
9fc09925-c689-4647-967f-2fff205e35e4	74fd8c58-32e7-49d9-b9c5-87b8b75575a5	d38fe066-ade1-4f42-9148-7d246dc7630d	\N	2026-02-09 22:02:54.47171	\N
3a1b94d6-fba6-4cd8-81f2-1ace41d7c778	74fd8c58-32e7-49d9-b9c5-87b8b75575a5	b405c771-43f7-4ed7-9c58-d845a971eff2	\N	2026-02-09 22:02:54.471838	\N
d541f5c0-4fea-4709-a5ee-c7ac9ad40696	74fd8c58-32e7-49d9-b9c5-87b8b75575a5	b8708661-9623-4ac5-9b82-8555bf982311	\N	2026-02-09 22:02:54.471952	\N
7bf04f56-c881-41da-a999-4c1ac71ffce6	74fd8c58-32e7-49d9-b9c5-87b8b75575a5	52d6fee7-733d-435c-a91e-043db2012180	\N	2026-02-09 22:02:54.472063	\N
b1ec04db-9fa7-41e1-95e7-4ed401ce1736	74fd8c58-32e7-49d9-b9c5-87b8b75575a5	d4571f05-7878-4433-85f2-7f6c493a79ab	\N	2026-02-09 22:02:54.472168	\N
39f803c8-0420-4959-bbae-5927c6f25c9d	74fd8c58-32e7-49d9-b9c5-87b8b75575a5	d1c7d837-21f6-46d5-985f-f692a33bdb1c	\N	2026-02-09 22:02:54.472362	\N
8b41f9d9-009f-4027-b8fd-bbae607e1bdb	f55fa7d7-8758-414e-b8aa-b280664bdb69	c486aadf-e5d2-4d8d-8562-7f7f8be7da65	\N	2026-02-09 22:02:54.484483	\N
72812922-d545-4517-9d23-997e01d67033	f55fa7d7-8758-414e-b8aa-b280664bdb69	ecde2a02-99da-48fa-b4ce-c203fdbf8713	\N	2026-02-09 22:02:54.484638	\N
ce1a7c8d-bc6c-44a5-87a4-f5b1ac60ab8b	f55fa7d7-8758-414e-b8aa-b280664bdb69	6b3d33a4-3825-4d70-a0b0-3294acd8fde5	\N	2026-02-09 22:02:54.484754	\N
156d2a38-bd2d-4018-807c-4c9b7a0c6b05	f55fa7d7-8758-414e-b8aa-b280664bdb69	b9576b8f-0dea-4a68-8396-f3c2aad2eab3	\N	2026-02-09 22:02:54.484862	\N
c4b53f90-9e34-4e64-9eb7-a058756aed9e	f55fa7d7-8758-414e-b8aa-b280664bdb69	33d18ec2-71d9-49c1-a1db-4485639ced0b	\N	2026-02-09 22:02:54.484984	\N
0a6a8d2d-7872-4a9b-a73b-231e834f9c81	f55fa7d7-8758-414e-b8aa-b280664bdb69	dc29e23c-b356-4036-a92e-2a1af948965b	\N	2026-02-09 22:02:54.485088	\N
2213eb82-4a3d-4dc7-86ae-78149f1cf493	f55fa7d7-8758-414e-b8aa-b280664bdb69	ea41f39b-26f9-490a-88f6-73d2adb9c077	\N	2026-02-09 22:02:54.485193	\N
23ad9cf3-0293-4312-b929-85e3b660087a	f55fa7d7-8758-414e-b8aa-b280664bdb69	a8de728b-8741-4d2a-acc5-76a74fe26643	\N	2026-02-09 22:02:54.485297	\N
436a3b1c-ea40-426c-b447-18a52b360f76	f55fa7d7-8758-414e-b8aa-b280664bdb69	71dd944f-458e-45b8-9eb9-37a283abe7b8	\N	2026-02-09 22:02:54.4854	\N
c8eca462-f418-4a30-a22b-d972f23943b9	f55fa7d7-8758-414e-b8aa-b280664bdb69	5c8ed432-bcdc-4d04-974e-76cb5c3a0547	\N	2026-02-09 22:02:54.485503	\N
78a85818-c8aa-409f-bb10-a1e14d2c738e	f55fa7d7-8758-414e-b8aa-b280664bdb69	8f117173-4239-4ea0-a533-0a9e71678c05	\N	2026-02-09 22:02:54.485607	\N
015b48c6-1922-40c7-93d2-012805706d94	f55fa7d7-8758-414e-b8aa-b280664bdb69	f0b49401-cf3e-431a-8323-1899d7a896bf	\N	2026-02-09 22:02:54.485741	\N
6afe4847-4daf-4417-91f6-da9275074bc6	f55fa7d7-8758-414e-b8aa-b280664bdb69	dcc21cd0-1a73-4a91-bc4f-f18267db396e	\N	2026-02-09 22:02:54.485847	\N
0d0bce16-54c7-468b-afe2-a20356773087	f55fa7d7-8758-414e-b8aa-b280664bdb69	633d14fa-8f41-43e4-b298-c9bebcc090da	\N	2026-02-09 22:02:54.485951	\N
a3fcdea4-c69f-452a-a9cc-1d10948fa60c	f55fa7d7-8758-414e-b8aa-b280664bdb69	7f9a8ede-33f2-47e8-8a61-3a0d80eb7a55	\N	2026-02-09 22:02:54.486053	\N
d3c3a513-a80a-4582-82ae-135d89fd638d	f55fa7d7-8758-414e-b8aa-b280664bdb69	d1c7d837-21f6-46d5-985f-f692a33bdb1c	\N	2026-02-09 22:02:54.486156	\N
8e95c2a4-c4e8-484d-a53f-46ea3cdd6402	f55fa7d7-8758-414e-b8aa-b280664bdb69	a58264b8-7323-493d-a4fc-b31faa15a889	\N	2026-02-09 22:02:54.48626	\N
2d72e09b-af5b-4c72-a829-ec480043ee72	8011da3e-e193-45c8-ac46-4250db01d59e	c486aadf-e5d2-4d8d-8562-7f7f8be7da65	\N	2026-02-09 22:02:54.493801	\N
2ece47a6-dcd4-4fa2-8a69-9bef9f8b213e	8011da3e-e193-45c8-ac46-4250db01d59e	33d18ec2-71d9-49c1-a1db-4485639ced0b	\N	2026-02-09 22:02:54.494128	\N
6cbf2fe8-2502-46aa-b812-54207884dc6c	8011da3e-e193-45c8-ac46-4250db01d59e	dc29e23c-b356-4036-a92e-2a1af948965b	\N	2026-02-09 22:02:54.494345	\N
d4ac9062-48ec-4ee4-876d-175c1176ef0d	8011da3e-e193-45c8-ac46-4250db01d59e	71dd944f-458e-45b8-9eb9-37a283abe7b8	\N	2026-02-09 22:02:54.49454	\N
9d3cc60e-adc9-4918-a989-c33a9b1e680d	8011da3e-e193-45c8-ac46-4250db01d59e	f0b49401-cf3e-431a-8323-1899d7a896bf	\N	2026-02-09 22:02:54.494725	\N
3c277437-ffc7-4139-9beb-16696bb830ce	8011da3e-e193-45c8-ac46-4250db01d59e	7f9a8ede-33f2-47e8-8a61-3a0d80eb7a55	\N	2026-02-09 22:02:54.494908	\N
09b6b2df-4ec7-49d8-8d70-8c5ac740afd0	8011da3e-e193-45c8-ac46-4250db01d59e	d1c7d837-21f6-46d5-985f-f692a33bdb1c	\N	2026-02-09 22:02:54.495087	\N
4085ff41-5a2e-4fca-bd9b-e77ba404c416	8011da3e-e193-45c8-ac46-4250db01d59e	a58264b8-7323-493d-a4fc-b31faa15a889	\N	2026-02-09 22:02:54.495253	\N
7afe4847-4daf-4417-91f6-da9275074bc8	8011da3e-e193-45c8-ac46-4250db01d59e	dcc21cd0-1a73-4a91-bc4f-f18267db396e	\N	2026-02-09 22:02:54.4953	\N
71847f4d-c900-445c-a152-1298bbb35b8c	b196853c-1197-4b42-8eca-60c25e82ad10	633d14fa-8f41-43e4-b298-c9bebcc090da	\N	2026-02-09 22:02:54.502357	\N
98737271-0c05-4106-ac33-6efa0f51bc86	b196853c-1197-4b42-8eca-60c25e82ad10	ecde2a02-99da-48fa-b4ce-c203fdbf8713	\N	2026-02-09 22:02:54.502495	\N
18fe200a-7d65-4590-8295-d929fcaaa466	b196853c-1197-4b42-8eca-60c25e82ad10	dc29e23c-b356-4036-a92e-2a1af948965b	\N	2026-02-09 22:02:54.502634	\N
ca038a41-6579-4271-83db-4692ba43343c	b196853c-1197-4b42-8eca-60c25e82ad10	f0b49401-cf3e-431a-8323-1899d7a896bf	\N	2026-02-09 22:02:54.502737	\N
8b4a3f7c-e21e-41d9-917d-668b6080435d	3d150ecb-411e-4483-a308-6308bbe24b7a	7f9a8ede-33f2-47e8-8a61-3a0d80eb7a55	\N	2026-02-09 22:02:54.506376	\N
acbd9627-6b28-49e5-a669-abb3171090ec	3d150ecb-411e-4483-a308-6308bbe24b7a	d1c7d837-21f6-46d5-985f-f692a33bdb1c	\N	2026-02-09 22:02:54.506608	\N
6055f6f8-65e8-419b-8cc2-4cc9f2609485	3d150ecb-411e-4483-a308-6308bbe24b7a	dc29e23c-b356-4036-a92e-2a1af948965b	\N	2026-02-09 22:02:54.506805	\N
0ae3625d-f49d-4c53-b481-4cc18f49cabc	3d150ecb-411e-4483-a308-6308bbe24b7a	f0b49401-cf3e-431a-8323-1899d7a896bf	\N	2026-02-09 22:02:54.506996	\N
672ea2ca-973a-48bb-9470-2bd74fb3779f	58599bfb-7e6e-4966-b306-4550c68594d0	dc29e23c-b356-4036-a92e-2a1af948965b	\N	2026-02-09 22:02:54.511322	\N
eba710e1-b840-4ad5-a699-15c477413ecb	58599bfb-7e6e-4966-b306-4550c68594d0	f0b49401-cf3e-431a-8323-1899d7a896bf	\N	2026-02-09 22:02:54.511465	\N
\.


--
-- Data for Name: roles; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.roles (id, company_id, name, code, description, hierarchy_level, is_system, is_active, created_at, updated_at) FROM stdin;
74fd8c58-32e7-49d9-b9c5-87b8b75575a5	1	Administrador	admin	Acceso total al sistema	100	t	t	2026-02-09 22:02:54.465288	\N
f55fa7d7-8758-414e-b8aa-b280664bdb69	1	Gerente	manager	Gesti├│n operativa del negocio	90	t	t	2026-02-09 22:02:54.483049	\N
8011da3e-e193-45c8-ac46-4250db01d59e	1	Cajero	cashier	Manejo de caja y cobros	50	t	t	2026-02-09 22:02:54.490653	\N
b196853c-1197-4b42-8eca-60c25e82ad10	1	Cocinero	cook	Pantalla de cocina e inventario	40	t	t	2026-02-09 22:02:54.500914	\N
3d150ecb-411e-4483-a308-6308bbe24b7a	1	Mesero	server	Toma de pedidos y atenci├│n	30	t	t	2026-02-09 22:02:54.50496	\N
58599bfb-7e6e-4966-b306-4550c68594d0	1	Repartidor	delivery	Entrega de pedidos	20	t	t	2026-02-09 22:02:54.509979	\N
\.


--
-- Data for Name: subscriptions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.subscriptions (id, company_id, plan, status, started_at, current_period_start, current_period_end, cancelled_at, amount, currency, created_at, updated_at) FROM stdin;
1	1	free	active	2026-02-09 22:02:54.435844	\N	\N	\N	0	COP	2026-02-09 22:02:54.436083	\N
\.


--
-- Data for Name: tables; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tables (id, branch_id, table_number, seat_count, status, pos_x, pos_y, is_active, created_at, updated_at) FROM stdin;
1	1	1	4	AVAILABLE	\N	\N	t	2026-02-09 22:18:00.377113	\N
2	1	2	4	AVAILABLE	\N	\N	t	2026-02-09 22:18:00.377536	\N
3	1	3	4	AVAILABLE	\N	\N	t	2026-02-09 22:18:00.377717	\N
4	1	4	4	AVAILABLE	\N	\N	t	2026-02-09 22:18:00.377878	\N
5	1	5	4	AVAILABLE	\N	\N	t	2026-02-09 22:18:00.3781	\N
6	1	6	4	AVAILABLE	\N	\N	t	2026-02-09 22:18:00.378293	\N
7	1	7	4	AVAILABLE	\N	\N	t	2026-02-09 22:18:00.378825	\N
8	1	8	4	AVAILABLE	\N	\N	t	2026-02-09 22:18:00.379061	\N
9	1	9	4	AVAILABLE	\N	\N	t	2026-02-09 22:18:00.379279	\N
10	1	10	4	AVAILABLE	\N	\N	t	2026-02-09 22:18:00.379435	\N
\.


--
-- Data for Name: unit_conversions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.unit_conversions (id, from_unit, to_unit, factor) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.users (id, company_id, branch_id, role_id, username, email, hashed_password, full_name, role, is_active, created_at, updated_at, last_login) FROM stdin;
1	1	1	74fd8c58-32e7-49d9-b9c5-87b8b75575a5	Kate	kate@gmail.com	$2b$12$e15aDWRo5KYOHDPrcIfB7.wRPu6kQTiWwMovL7sTpb4ohnwDLlLzW	Katerine toribamo larrs	admin	t	2026-02-09 22:02:54.892478	\N	\N
2	1	1	3d150ecb-411e-4483-a308-6308bbe24b7a	Mess	mesero@gmail.com	$2b$12$F4Y8vn5fNxQSXWnx8nZmSO5Ksh3Uub/OSfGI1Razyy1tEFY0lL4EW	Mesero	server	t	2026-02-09 22:04:12.486359	\N	\N
3	1	1	8011da3e-e193-45c8-ac46-4250db01d59e	Cajerouser	caja@gmail.com	$2b$12$7A4moGs1Avqw2IjCxYzyR.OzkNhEoOWBqs6RKQ2xmbDtU909EZusK	Cajero	cashier	t	2026-02-09 22:04:41.524965	\N	\N
4	1	1	b196853c-1197-4b42-8eca-60c25e82ad10	Cocinerouser	cocinero@gmail.com	$2b$12$N/5.kIBiMT8MFL6Kcqd1subbOUSE6Bpkf4Ohw4nzcgHEvUojMss3m	Cocinero	cook	t	2026-02-09 22:05:25.5004	\N	\N
\.


--
-- Name: audit_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.audit_logs_id_seq', 1, true);


--
-- Name: branches_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.branches_id_seq', 1, true);


--
-- Name: cash_closures_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.cash_closures_id_seq', 1, false);


--
-- Name: categories_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.categories_id_seq', 1, true);


--
-- Name: companies_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.companies_id_seq', 1, true);


--
-- Name: customer_addresses_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.customer_addresses_id_seq', 1, false);


--
-- Name: customers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.customers_id_seq', 1, false);


--
-- Name: delivery_shifts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.delivery_shifts_id_seq', 1, false);


--
-- Name: inventory_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.inventory_id_seq', 1, false);


--
-- Name: inventory_transactions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.inventory_transactions_id_seq', 1, false);


--
-- Name: modifier_recipe_items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.modifier_recipe_items_id_seq', 1, true);


--
-- Name: order_audits_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.order_audits_id_seq', 1, false);


--
-- Name: order_counters_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.order_counters_id_seq', 1, false);


--
-- Name: order_item_modifiers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.order_item_modifiers_id_seq', 1, false);


--
-- Name: order_items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.order_items_id_seq', 1, false);


--
-- Name: orders_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.orders_id_seq', 1, false);


--
-- Name: payments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.payments_id_seq', 1, false);


--
-- Name: print_jobs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.print_jobs_id_seq', 1, false);


--
-- Name: product_modifiers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.product_modifiers_id_seq', 1, true);


--
-- Name: products_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.products_id_seq', 2, true);


--
-- Name: subscriptions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.subscriptions_id_seq', 1, true);


--
-- Name: tables_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tables_id_seq', 10, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.users_id_seq', 4, true);


--
-- Name: audit_logs audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_pkey PRIMARY KEY (id);


--
-- Name: branches branches_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.branches
    ADD CONSTRAINT branches_pkey PRIMARY KEY (id);


--
-- Name: cash_closures cash_closures_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cash_closures
    ADD CONSTRAINT cash_closures_pkey PRIMARY KEY (id);


--
-- Name: categories categories_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT categories_pkey PRIMARY KEY (id);


--
-- Name: companies companies_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.companies
    ADD CONSTRAINT companies_pkey PRIMARY KEY (id);


--
-- Name: customer_addresses customer_addresses_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_addresses
    ADD CONSTRAINT customer_addresses_pkey PRIMARY KEY (id);


--
-- Name: customers customers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT customers_pkey PRIMARY KEY (id);


--
-- Name: delivery_shifts delivery_shifts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.delivery_shifts
    ADD CONSTRAINT delivery_shifts_pkey PRIMARY KEY (id);


--
-- Name: ingredient_batches ingredient_batches_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ingredient_batches
    ADD CONSTRAINT ingredient_batches_pkey PRIMARY KEY (id);


--
-- Name: ingredient_cost_history ingredient_cost_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ingredient_cost_history
    ADD CONSTRAINT ingredient_cost_history_pkey PRIMARY KEY (id);


--
-- Name: ingredient_inventory ingredient_inventory_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ingredient_inventory
    ADD CONSTRAINT ingredient_inventory_pkey PRIMARY KEY (id);


--
-- Name: ingredient_transactions ingredient_transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ingredient_transactions
    ADD CONSTRAINT ingredient_transactions_pkey PRIMARY KEY (id);


--
-- Name: ingredients ingredients_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ingredients
    ADD CONSTRAINT ingredients_pkey PRIMARY KEY (id);


--
-- Name: inventory_count_items inventory_count_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_count_items
    ADD CONSTRAINT inventory_count_items_pkey PRIMARY KEY (id);


--
-- Name: inventory_counts inventory_counts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_counts
    ADD CONSTRAINT inventory_counts_pkey PRIMARY KEY (id);


--
-- Name: inventory inventory_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory
    ADD CONSTRAINT inventory_pkey PRIMARY KEY (id);


--
-- Name: inventory_transactions inventory_transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_transactions
    ADD CONSTRAINT inventory_transactions_pkey PRIMARY KEY (id);


--
-- Name: modifier_recipe_items modifier_recipe_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.modifier_recipe_items
    ADD CONSTRAINT modifier_recipe_items_pkey PRIMARY KEY (id);


--
-- Name: order_audits order_audits_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_audits
    ADD CONSTRAINT order_audits_pkey PRIMARY KEY (id);


--
-- Name: order_counters order_counters_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_counters
    ADD CONSTRAINT order_counters_pkey PRIMARY KEY (id);


--
-- Name: order_item_modifiers order_item_modifiers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_item_modifiers
    ADD CONSTRAINT order_item_modifiers_pkey PRIMARY KEY (id);


--
-- Name: order_items order_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT order_items_pkey PRIMARY KEY (id);


--
-- Name: orders orders_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_pkey PRIMARY KEY (id);


--
-- Name: payments payments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_pkey PRIMARY KEY (id);


--
-- Name: permission_categories permission_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permission_categories
    ADD CONSTRAINT permission_categories_pkey PRIMARY KEY (id);


--
-- Name: permissions permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permissions
    ADD CONSTRAINT permissions_pkey PRIMARY KEY (id);


--
-- Name: print_jobs print_jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.print_jobs
    ADD CONSTRAINT print_jobs_pkey PRIMARY KEY (id);


--
-- Name: product_modifiers product_modifiers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_modifiers
    ADD CONSTRAINT product_modifiers_pkey PRIMARY KEY (id);


--
-- Name: production_event_input_batches production_event_input_batches_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.production_event_input_batches
    ADD CONSTRAINT production_event_input_batches_pkey PRIMARY KEY (id);


--
-- Name: production_event_inputs production_event_inputs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.production_event_inputs
    ADD CONSTRAINT production_event_inputs_pkey PRIMARY KEY (id);


--
-- Name: production_events production_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.production_events
    ADD CONSTRAINT production_events_pkey PRIMARY KEY (id);


--
-- Name: products products_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_pkey PRIMARY KEY (id);


--
-- Name: recipe_items recipe_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recipe_items
    ADD CONSTRAINT recipe_items_pkey PRIMARY KEY (id);


--
-- Name: recipes recipes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recipes
    ADD CONSTRAINT recipes_pkey PRIMARY KEY (id);


--
-- Name: role_permissions role_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT role_permissions_pkey PRIMARY KEY (id);


--
-- Name: roles roles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);


--
-- Name: subscriptions subscriptions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subscriptions
    ADD CONSTRAINT subscriptions_pkey PRIMARY KEY (id);


--
-- Name: tables tables_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tables
    ADD CONSTRAINT tables_pkey PRIMARY KEY (id);


--
-- Name: branches unique_branch_code_per_company; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.branches
    ADD CONSTRAINT unique_branch_code_per_company UNIQUE (company_id, code);


--
-- Name: permission_categories unique_category_code_per_company; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permission_categories
    ADD CONSTRAINT unique_category_code_per_company UNIQUE (company_id, code);


--
-- Name: categories unique_category_name_per_company; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT unique_category_name_per_company UNIQUE (company_id, name);


--
-- Name: permissions unique_permission_code_per_company; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permissions
    ADD CONSTRAINT unique_permission_code_per_company UNIQUE (company_id, code);


--
-- Name: roles unique_role_code_per_company; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT unique_role_code_per_company UNIQUE (company_id, code);


--
-- Name: role_permissions unique_role_permission; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT unique_role_permission UNIQUE (role_id, permission_id);


--
-- Name: users unique_username_per_company; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT unique_username_per_company UNIQUE (company_id, username);


--
-- Name: unit_conversions unit_conversions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.unit_conversions
    ADD CONSTRAINT unit_conversions_pkey PRIMARY KEY (id);


--
-- Name: order_counters uq_branch_counter_type; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_counters
    ADD CONSTRAINT uq_branch_counter_type UNIQUE (branch_id, counter_type);


--
-- Name: customers uq_customer_phone_company; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT uq_customer_phone_company UNIQUE (company_id, phone);


--
-- Name: ingredient_inventory uq_ingredient_inventory_branch; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ingredient_inventory
    ADD CONSTRAINT uq_ingredient_inventory_branch UNIQUE (branch_id, ingredient_id);


--
-- Name: inventory uq_inventory_branch_product; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory
    ADD CONSTRAINT uq_inventory_branch_product UNIQUE (branch_id, product_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: idx_audit_company_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_company_created ON public.audit_logs USING btree (company_id, created_at);


--
-- Name: idx_audit_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_entity ON public.audit_logs USING btree (entity_type, entity_id);


--
-- Name: idx_audit_user_action; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_user_action ON public.audit_logs USING btree (user_id, action);


--
-- Name: idx_branches_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_branches_active ON public.branches USING btree (company_id, is_active);


--
-- Name: idx_categories_company_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_categories_company_active ON public.categories USING btree (company_id, is_active);


--
-- Name: idx_companies_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_companies_active ON public.companies USING btree (is_active);


--
-- Name: idx_delivery_shifts_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_delivery_shifts_date ON public.delivery_shifts USING btree (company_id, started_at);


--
-- Name: idx_delivery_shifts_driver; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_delivery_shifts_driver ON public.delivery_shifts USING btree (company_id, delivery_person_id);


--
-- Name: idx_ingredient_inventory_branch; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ingredient_inventory_branch ON public.ingredient_inventory USING btree (branch_id);


--
-- Name: idx_inventory_branch; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_inventory_branch ON public.inventory USING btree (branch_id);


--
-- Name: idx_modifiers_company; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_modifiers_company ON public.product_modifiers USING btree (company_id);


--
-- Name: idx_orders_branch_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_orders_branch_date ON public.orders USING btree (branch_id, created_at);


--
-- Name: idx_orders_company_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_orders_company_status ON public.orders USING btree (company_id, status);


--
-- Name: idx_payments_company_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_payments_company_date ON public.payments USING btree (company_id, created_at);


--
-- Name: idx_payments_order; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_payments_order ON public.payments USING btree (order_id);


--
-- Name: idx_perm_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_perm_active ON public.permissions USING btree (company_id, is_active);


--
-- Name: idx_perm_cat_company_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_perm_cat_company_active ON public.permission_categories USING btree (company_id, is_active);


--
-- Name: idx_perm_cat_system; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_perm_cat_system ON public.permission_categories USING btree (is_system, is_active);


--
-- Name: idx_perm_company_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_perm_company_category ON public.permissions USING btree (company_id, category_id);


--
-- Name: idx_perm_resource_action; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_perm_resource_action ON public.permissions USING btree (company_id, resource, action);


--
-- Name: idx_products_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_products_category ON public.products USING btree (company_id, category_id);


--
-- Name: idx_products_company_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_products_company_active ON public.products USING btree (company_id, is_active);


--
-- Name: idx_role_perm_expires; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_role_perm_expires ON public.role_permissions USING btree (expires_at);


--
-- Name: idx_role_perm_permission; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_role_perm_permission ON public.role_permissions USING btree (permission_id);


--
-- Name: idx_role_perm_role; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_role_perm_role ON public.role_permissions USING btree (role_id);


--
-- Name: idx_roles_company_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_roles_company_active ON public.roles USING btree (company_id, is_active);


--
-- Name: idx_roles_hierarchy; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_roles_hierarchy ON public.roles USING btree (company_id, hierarchy_level);


--
-- Name: idx_roles_system; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_roles_system ON public.roles USING btree (is_system, is_active);


--
-- Name: idx_subscriptions_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_subscriptions_status ON public.subscriptions USING btree (status, current_period_end);


--
-- Name: idx_users_login; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_users_login ON public.users USING btree (company_id, username, is_active);


--
-- Name: idx_users_role; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_users_role ON public.users USING btree (company_id, role_id, is_active);


--
-- Name: ix_audit_logs_action; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_logs_action ON public.audit_logs USING btree (action);


--
-- Name: ix_audit_logs_company_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_logs_company_id ON public.audit_logs USING btree (company_id);


--
-- Name: ix_audit_logs_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_logs_created_at ON public.audit_logs USING btree (created_at);


--
-- Name: ix_audit_logs_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_logs_user_id ON public.audit_logs USING btree (user_id);


--
-- Name: ix_branches_company_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_branches_company_id ON public.branches USING btree (company_id);


--
-- Name: ix_cash_closures_branch_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_cash_closures_branch_id ON public.cash_closures USING btree (branch_id);


--
-- Name: ix_cash_closures_company_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_cash_closures_company_id ON public.cash_closures USING btree (company_id);


--
-- Name: ix_categories_company_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_categories_company_id ON public.categories USING btree (company_id);


--
-- Name: ix_companies_slug; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_companies_slug ON public.companies USING btree (slug);


--
-- Name: ix_customer_addresses_customer_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_customer_addresses_customer_id ON public.customer_addresses USING btree (customer_id);


--
-- Name: ix_customers_company_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_customers_company_id ON public.customers USING btree (company_id);


--
-- Name: ix_customers_phone; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_customers_phone ON public.customers USING btree (phone);


--
-- Name: ix_delivery_shifts_branch_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_delivery_shifts_branch_id ON public.delivery_shifts USING btree (branch_id);


--
-- Name: ix_delivery_shifts_company_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_delivery_shifts_company_id ON public.delivery_shifts USING btree (company_id);


--
-- Name: ix_delivery_shifts_delivery_person_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_delivery_shifts_delivery_person_id ON public.delivery_shifts USING btree (delivery_person_id);


--
-- Name: ix_ingredient_batches_acquired_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ingredient_batches_acquired_at ON public.ingredient_batches USING btree (acquired_at);


--
-- Name: ix_ingredient_batches_branch_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ingredient_batches_branch_id ON public.ingredient_batches USING btree (branch_id);


--
-- Name: ix_ingredient_batches_ingredient_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ingredient_batches_ingredient_id ON public.ingredient_batches USING btree (ingredient_id);


--
-- Name: ix_ingredient_batches_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ingredient_batches_is_active ON public.ingredient_batches USING btree (is_active);


--
-- Name: ix_ingredient_cost_history_ingredient_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ingredient_cost_history_ingredient_id ON public.ingredient_cost_history USING btree (ingredient_id);


--
-- Name: ix_ingredients_category_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ingredients_category_id ON public.ingredients USING btree (category_id);


--
-- Name: ix_ingredients_company_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ingredients_company_id ON public.ingredients USING btree (company_id);


--
-- Name: ix_ingredients_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ingredients_name ON public.ingredients USING btree (name);


--
-- Name: ix_ingredients_sku; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ingredients_sku ON public.ingredients USING btree (sku);


--
-- Name: ix_inventory_count_items_count_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_inventory_count_items_count_id ON public.inventory_count_items USING btree (count_id);


--
-- Name: ix_inventory_counts_branch_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_inventory_counts_branch_id ON public.inventory_counts USING btree (branch_id);


--
-- Name: ix_inventory_counts_company_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_inventory_counts_company_id ON public.inventory_counts USING btree (company_id);


--
-- Name: ix_order_audits_order_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_order_audits_order_id ON public.order_audits USING btree (order_id);


--
-- Name: ix_order_counters_branch_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_order_counters_branch_id ON public.order_counters USING btree (branch_id);


--
-- Name: ix_order_counters_company_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_order_counters_company_id ON public.order_counters USING btree (company_id);


--
-- Name: ix_orders_branch_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_orders_branch_id ON public.orders USING btree (branch_id);


--
-- Name: ix_orders_company_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_orders_company_id ON public.orders USING btree (company_id);


--
-- Name: ix_orders_created_by_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_orders_created_by_id ON public.orders USING btree (created_by_id);


--
-- Name: ix_orders_customer_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_orders_customer_id ON public.orders USING btree (customer_id);


--
-- Name: ix_orders_delivery_person_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_orders_delivery_person_id ON public.orders USING btree (delivery_person_id);


--
-- Name: ix_orders_order_number; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_orders_order_number ON public.orders USING btree (order_number);


--
-- Name: ix_orders_table_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_orders_table_id ON public.orders USING btree (table_id);


--
-- Name: ix_payments_branch_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_payments_branch_id ON public.payments USING btree (branch_id);


--
-- Name: ix_payments_company_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_payments_company_id ON public.payments USING btree (company_id);


--
-- Name: ix_payments_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_payments_user_id ON public.payments USING btree (user_id);


--
-- Name: ix_permission_categories_company_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_permission_categories_company_id ON public.permission_categories USING btree (company_id);


--
-- Name: ix_permissions_category_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_permissions_category_id ON public.permissions USING btree (category_id);


--
-- Name: ix_permissions_company_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_permissions_company_id ON public.permissions USING btree (company_id);


--
-- Name: ix_print_jobs_company_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_print_jobs_company_id ON public.print_jobs USING btree (company_id);


--
-- Name: ix_print_jobs_order_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_print_jobs_order_id ON public.print_jobs USING btree (order_id);


--
-- Name: ix_print_jobs_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_print_jobs_status ON public.print_jobs USING btree (status);


--
-- Name: ix_production_event_input_batches_production_event_input_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_production_event_input_batches_production_event_input_id ON public.production_event_input_batches USING btree (production_event_input_id);


--
-- Name: ix_production_event_input_batches_source_batch_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_production_event_input_batches_source_batch_id ON public.production_event_input_batches USING btree (source_batch_id);


--
-- Name: ix_production_event_inputs_ingredient_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_production_event_inputs_ingredient_id ON public.production_event_inputs USING btree (ingredient_id);


--
-- Name: ix_production_event_inputs_production_event_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_production_event_inputs_production_event_id ON public.production_event_inputs USING btree (production_event_id);


--
-- Name: ix_production_events_company_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_production_events_company_id ON public.production_events USING btree (company_id);


--
-- Name: ix_production_events_input_ingredient_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_production_events_input_ingredient_id ON public.production_events USING btree (input_ingredient_id);


--
-- Name: ix_production_events_output_ingredient_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_production_events_output_ingredient_id ON public.production_events USING btree (output_ingredient_id);


--
-- Name: ix_products_category_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_products_category_id ON public.products USING btree (category_id);


--
-- Name: ix_products_company_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_products_company_id ON public.products USING btree (company_id);


--
-- Name: ix_recipe_items_company_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_recipe_items_company_id ON public.recipe_items USING btree (company_id);


--
-- Name: ix_recipe_items_ingredient_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_recipe_items_ingredient_id ON public.recipe_items USING btree (ingredient_id);


--
-- Name: ix_recipe_items_recipe_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_recipe_items_recipe_id ON public.recipe_items USING btree (recipe_id);


--
-- Name: ix_recipes_company_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_recipes_company_id ON public.recipes USING btree (company_id);


--
-- Name: ix_recipes_product_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_recipes_product_id ON public.recipes USING btree (product_id);


--
-- Name: ix_role_permissions_permission_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_role_permissions_permission_id ON public.role_permissions USING btree (permission_id);


--
-- Name: ix_role_permissions_role_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_role_permissions_role_id ON public.role_permissions USING btree (role_id);


--
-- Name: ix_roles_company_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_roles_company_id ON public.roles USING btree (company_id);


--
-- Name: ix_subscriptions_company_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_subscriptions_company_id ON public.subscriptions USING btree (company_id);


--
-- Name: ix_tables_branch_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_tables_branch_id ON public.tables USING btree (branch_id);


--
-- Name: ix_unit_conversions_from_unit; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_unit_conversions_from_unit ON public.unit_conversions USING btree (from_unit);


--
-- Name: ix_unit_conversions_to_unit; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_unit_conversions_to_unit ON public.unit_conversions USING btree (to_unit);


--
-- Name: ix_users_branch_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_users_branch_id ON public.users USING btree (branch_id);


--
-- Name: ix_users_company_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_users_company_id ON public.users USING btree (company_id);


--
-- Name: ix_users_role_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_users_role_id ON public.users USING btree (role_id);


--
-- Name: ix_users_username; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_users_username ON public.users USING btree (username);


--
-- Name: audit_logs audit_logs_branch_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_branch_id_fkey FOREIGN KEY (branch_id) REFERENCES public.branches(id);


--
-- Name: audit_logs audit_logs_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- Name: audit_logs audit_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: branches branches_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.branches
    ADD CONSTRAINT branches_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- Name: cash_closures cash_closures_branch_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cash_closures
    ADD CONSTRAINT cash_closures_branch_id_fkey FOREIGN KEY (branch_id) REFERENCES public.branches(id);


--
-- Name: cash_closures cash_closures_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cash_closures
    ADD CONSTRAINT cash_closures_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- Name: cash_closures cash_closures_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cash_closures
    ADD CONSTRAINT cash_closures_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: categories categories_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT categories_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- Name: customer_addresses customer_addresses_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_addresses
    ADD CONSTRAINT customer_addresses_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customers(id);


--
-- Name: customers customers_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT customers_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- Name: delivery_shifts delivery_shifts_branch_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.delivery_shifts
    ADD CONSTRAINT delivery_shifts_branch_id_fkey FOREIGN KEY (branch_id) REFERENCES public.branches(id);


--
-- Name: delivery_shifts delivery_shifts_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.delivery_shifts
    ADD CONSTRAINT delivery_shifts_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- Name: delivery_shifts delivery_shifts_delivery_person_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.delivery_shifts
    ADD CONSTRAINT delivery_shifts_delivery_person_id_fkey FOREIGN KEY (delivery_person_id) REFERENCES public.users(id);


--
-- Name: ingredient_batches ingredient_batches_branch_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ingredient_batches
    ADD CONSTRAINT ingredient_batches_branch_id_fkey FOREIGN KEY (branch_id) REFERENCES public.branches(id);


--
-- Name: ingredient_batches ingredient_batches_ingredient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ingredient_batches
    ADD CONSTRAINT ingredient_batches_ingredient_id_fkey FOREIGN KEY (ingredient_id) REFERENCES public.ingredients(id);


--
-- Name: ingredient_cost_history ingredient_cost_history_ingredient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ingredient_cost_history
    ADD CONSTRAINT ingredient_cost_history_ingredient_id_fkey FOREIGN KEY (ingredient_id) REFERENCES public.ingredients(id);


--
-- Name: ingredient_cost_history ingredient_cost_history_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ingredient_cost_history
    ADD CONSTRAINT ingredient_cost_history_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: ingredient_inventory ingredient_inventory_branch_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ingredient_inventory
    ADD CONSTRAINT ingredient_inventory_branch_id_fkey FOREIGN KEY (branch_id) REFERENCES public.branches(id);


--
-- Name: ingredient_inventory ingredient_inventory_ingredient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ingredient_inventory
    ADD CONSTRAINT ingredient_inventory_ingredient_id_fkey FOREIGN KEY (ingredient_id) REFERENCES public.ingredients(id);


--
-- Name: ingredient_transactions ingredient_transactions_inventory_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ingredient_transactions
    ADD CONSTRAINT ingredient_transactions_inventory_id_fkey FOREIGN KEY (inventory_id) REFERENCES public.ingredient_inventory(id);


--
-- Name: ingredient_transactions ingredient_transactions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ingredient_transactions
    ADD CONSTRAINT ingredient_transactions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: ingredients ingredients_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ingredients
    ADD CONSTRAINT ingredients_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.categories(id);


--
-- Name: ingredients ingredients_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ingredients
    ADD CONSTRAINT ingredients_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- Name: inventory inventory_branch_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory
    ADD CONSTRAINT inventory_branch_id_fkey FOREIGN KEY (branch_id) REFERENCES public.branches(id);


--
-- Name: inventory_count_items inventory_count_items_count_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_count_items
    ADD CONSTRAINT inventory_count_items_count_id_fkey FOREIGN KEY (count_id) REFERENCES public.inventory_counts(id);


--
-- Name: inventory_count_items inventory_count_items_ingredient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_count_items
    ADD CONSTRAINT inventory_count_items_ingredient_id_fkey FOREIGN KEY (ingredient_id) REFERENCES public.ingredients(id);


--
-- Name: inventory_counts inventory_counts_branch_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_counts
    ADD CONSTRAINT inventory_counts_branch_id_fkey FOREIGN KEY (branch_id) REFERENCES public.branches(id);


--
-- Name: inventory_counts inventory_counts_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_counts
    ADD CONSTRAINT inventory_counts_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- Name: inventory_counts inventory_counts_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_counts
    ADD CONSTRAINT inventory_counts_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: inventory inventory_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory
    ADD CONSTRAINT inventory_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- Name: inventory_transactions inventory_transactions_inventory_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_transactions
    ADD CONSTRAINT inventory_transactions_inventory_id_fkey FOREIGN KEY (inventory_id) REFERENCES public.inventory(id);


--
-- Name: inventory_transactions inventory_transactions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_transactions
    ADD CONSTRAINT inventory_transactions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: modifier_recipe_items modifier_recipe_items_ingredient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.modifier_recipe_items
    ADD CONSTRAINT modifier_recipe_items_ingredient_id_fkey FOREIGN KEY (ingredient_id) REFERENCES public.ingredients(id);


--
-- Name: modifier_recipe_items modifier_recipe_items_ingredient_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.modifier_recipe_items
    ADD CONSTRAINT modifier_recipe_items_ingredient_product_id_fkey FOREIGN KEY (ingredient_product_id) REFERENCES public.products(id);


--
-- Name: modifier_recipe_items modifier_recipe_items_modifier_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.modifier_recipe_items
    ADD CONSTRAINT modifier_recipe_items_modifier_id_fkey FOREIGN KEY (modifier_id) REFERENCES public.product_modifiers(id);


--
-- Name: order_audits order_audits_changed_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_audits
    ADD CONSTRAINT order_audits_changed_by_user_id_fkey FOREIGN KEY (changed_by_user_id) REFERENCES public.users(id);


--
-- Name: order_audits order_audits_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_audits
    ADD CONSTRAINT order_audits_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(id);


--
-- Name: order_counters order_counters_branch_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_counters
    ADD CONSTRAINT order_counters_branch_id_fkey FOREIGN KEY (branch_id) REFERENCES public.branches(id);


--
-- Name: order_counters order_counters_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_counters
    ADD CONSTRAINT order_counters_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- Name: order_item_modifiers order_item_modifiers_modifier_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_item_modifiers
    ADD CONSTRAINT order_item_modifiers_modifier_id_fkey FOREIGN KEY (modifier_id) REFERENCES public.product_modifiers(id);


--
-- Name: order_item_modifiers order_item_modifiers_order_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_item_modifiers
    ADD CONSTRAINT order_item_modifiers_order_item_id_fkey FOREIGN KEY (order_item_id) REFERENCES public.order_items(id);


--
-- Name: order_items order_items_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT order_items_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(id);


--
-- Name: order_items order_items_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT order_items_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- Name: orders orders_branch_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_branch_id_fkey FOREIGN KEY (branch_id) REFERENCES public.branches(id);


--
-- Name: orders orders_cancellation_requested_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_cancellation_requested_by_id_fkey FOREIGN KEY (cancellation_requested_by_id) REFERENCES public.users(id);


--
-- Name: orders orders_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- Name: orders orders_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(id);


--
-- Name: orders orders_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customers(id);


--
-- Name: orders orders_delivery_person_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_delivery_person_id_fkey FOREIGN KEY (delivery_person_id) REFERENCES public.users(id);


--
-- Name: orders orders_table_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_table_id_fkey FOREIGN KEY (table_id) REFERENCES public.tables(id);


--
-- Name: payments payments_branch_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_branch_id_fkey FOREIGN KEY (branch_id) REFERENCES public.branches(id);


--
-- Name: payments payments_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- Name: payments payments_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(id);


--
-- Name: payments payments_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: permission_categories permission_categories_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permission_categories
    ADD CONSTRAINT permission_categories_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- Name: permissions permissions_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permissions
    ADD CONSTRAINT permissions_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.permission_categories(id);


--
-- Name: permissions permissions_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permissions
    ADD CONSTRAINT permissions_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- Name: product_modifiers product_modifiers_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_modifiers
    ADD CONSTRAINT product_modifiers_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- Name: production_event_input_batches production_event_input_batches_production_event_input_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.production_event_input_batches
    ADD CONSTRAINT production_event_input_batches_production_event_input_id_fkey FOREIGN KEY (production_event_input_id) REFERENCES public.production_event_inputs(id);


--
-- Name: production_event_input_batches production_event_input_batches_source_batch_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.production_event_input_batches
    ADD CONSTRAINT production_event_input_batches_source_batch_id_fkey FOREIGN KEY (source_batch_id) REFERENCES public.ingredient_batches(id);


--
-- Name: production_event_inputs production_event_inputs_ingredient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.production_event_inputs
    ADD CONSTRAINT production_event_inputs_ingredient_id_fkey FOREIGN KEY (ingredient_id) REFERENCES public.ingredients(id);


--
-- Name: production_event_inputs production_event_inputs_production_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.production_event_inputs
    ADD CONSTRAINT production_event_inputs_production_event_id_fkey FOREIGN KEY (production_event_id) REFERENCES public.production_events(id);


--
-- Name: production_events production_events_input_ingredient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.production_events
    ADD CONSTRAINT production_events_input_ingredient_id_fkey FOREIGN KEY (input_ingredient_id) REFERENCES public.ingredients(id);


--
-- Name: production_events production_events_output_batch_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.production_events
    ADD CONSTRAINT production_events_output_batch_id_fkey FOREIGN KEY (output_batch_id) REFERENCES public.ingredient_batches(id);


--
-- Name: production_events production_events_output_ingredient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.production_events
    ADD CONSTRAINT production_events_output_ingredient_id_fkey FOREIGN KEY (output_ingredient_id) REFERENCES public.ingredients(id);


--
-- Name: production_events production_events_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.production_events
    ADD CONSTRAINT production_events_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: products products_active_recipe_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_active_recipe_id_fkey FOREIGN KEY (active_recipe_id) REFERENCES public.recipes(id);


--
-- Name: products products_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.categories(id);


--
-- Name: products products_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- Name: recipe_items recipe_items_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recipe_items
    ADD CONSTRAINT recipe_items_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- Name: recipe_items recipe_items_ingredient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recipe_items
    ADD CONSTRAINT recipe_items_ingredient_id_fkey FOREIGN KEY (ingredient_id) REFERENCES public.ingredients(id);


--
-- Name: recipe_items recipe_items_recipe_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recipe_items
    ADD CONSTRAINT recipe_items_recipe_id_fkey FOREIGN KEY (recipe_id) REFERENCES public.recipes(id);


--
-- Name: recipes recipes_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recipes
    ADD CONSTRAINT recipes_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- Name: recipes recipes_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recipes
    ADD CONSTRAINT recipes_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- Name: role_permissions role_permissions_granted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT role_permissions_granted_by_fkey FOREIGN KEY (granted_by) REFERENCES public.users(id);


--
-- Name: role_permissions role_permissions_permission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT role_permissions_permission_id_fkey FOREIGN KEY (permission_id) REFERENCES public.permissions(id);


--
-- Name: role_permissions role_permissions_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT role_permissions_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id);


--
-- Name: roles roles_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- Name: subscriptions subscriptions_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subscriptions
    ADD CONSTRAINT subscriptions_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- Name: tables tables_branch_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tables
    ADD CONSTRAINT tables_branch_id_fkey FOREIGN KEY (branch_id) REFERENCES public.branches(id);


--
-- Name: users users_branch_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_branch_id_fkey FOREIGN KEY (branch_id) REFERENCES public.branches(id);


--
-- Name: users users_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- Name: users users_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id);

--
-- PostgreSQL database dump complete
--
