--
-- PostgreSQL database dump
--

-- Dumped from database version 17.2
-- Dumped by pg_dump version 17.2

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: -
--

-- *not* creating schema, since initdb creates it


--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON SCHEMA public IS '';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: ai_usage; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ai_usage (
    id integer NOT NULL,
    user_id integer NOT NULL,
    day date NOT NULL,
    count integer NOT NULL
);


--
-- Name: ai_usage_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.ai_usage_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: ai_usage_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.ai_usage_id_seq OWNED BY public.ai_usage.id;


--
-- Name: app_settings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.app_settings (
    key character varying(80) NOT NULL,
    value text NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


--
-- Name: applications; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.applications (
    id integer NOT NULL,
    user_id integer NOT NULL,
    job_id integer NOT NULL,
    status character varying(50) NOT NULL,
    cover_letter text,
    notes text,
    match_score double precision,
    applied_at timestamp without time zone,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


--
-- Name: applications_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.applications_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: applications_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.applications_id_seq OWNED BY public.applications.id;


--
-- Name: audit_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.audit_logs (
    id integer NOT NULL,
    user_id integer,
    action character varying(60) NOT NULL,
    target_type character varying(40),
    target_id character varying(64),
    detail json,
    ip character varying(64),
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
-- Name: employees; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.employees (
    emp_id integer NOT NULL,
    user_id integer NOT NULL,
    resume_text text,
    skills text,
    experience_years double precision,
    education text,
    phone character varying(50),
    linkedin_url character varying(500),
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


--
-- Name: employees_emp_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.employees_emp_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: employees_emp_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.employees_emp_id_seq OWNED BY public.employees.emp_id;


--
-- Name: jobs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.jobs (
    id integer NOT NULL,
    title character varying(255) NOT NULL,
    company character varying(255) NOT NULL,
    location character varying(255),
    description text,
    requirements text,
    salary_min double precision,
    salary_max double precision,
    job_type character varying(50),
    remote boolean NOT NULL,
    url character varying(500),
    source character varying(100),
    is_active boolean NOT NULL,
    posted_at timestamp without time zone,
    created_at timestamp without time zone NOT NULL
);


--
-- Name: jobs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.jobs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: jobs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.jobs_id_seq OWNED BY public.jobs.id;


--
-- Name: otp_codes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.otp_codes (
    id integer NOT NULL,
    email character varying(255) NOT NULL,
    purpose character varying(30) NOT NULL,
    code_hash character varying(128) NOT NULL,
    attempts integer NOT NULL,
    consumed boolean NOT NULL,
    expires_at timestamp without time zone NOT NULL,
    created_at timestamp without time zone NOT NULL
);


--
-- Name: otp_codes_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.otp_codes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: otp_codes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.otp_codes_id_seq OWNED BY public.otp_codes.id;


--
-- Name: payment_orders; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.payment_orders (
    id integer NOT NULL,
    user_id integer NOT NULL,
    razorpay_order_id character varying(64) NOT NULL,
    razorpay_payment_id character varying(64),
    amount_paise integer NOT NULL,
    currency character varying(8) NOT NULL,
    status character varying(20) NOT NULL,
    item_type character varying(30) NOT NULL,
    item_id integer,
    description character varying(255),
    meta json,
    created_at timestamp without time zone NOT NULL,
    paid_at timestamp without time zone
);


--
-- Name: payment_orders_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.payment_orders_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: payment_orders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.payment_orders_id_seq OWNED BY public.payment_orders.id;


--
-- Name: resume_downloads; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.resume_downloads (
    id integer NOT NULL,
    user_id integer NOT NULL,
    resume_id integer,
    template_id integer,
    created_at timestamp without time zone NOT NULL
);


--
-- Name: resume_downloads_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.resume_downloads_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: resume_downloads_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.resume_downloads_id_seq OWNED BY public.resume_downloads.id;


--
-- Name: resume_templates; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.resume_templates (
    id integer NOT NULL,
    slug character varying(80) NOT NULL,
    name character varying(120) NOT NULL,
    description text,
    category character varying(40) NOT NULL,
    style character varying(40) NOT NULL,
    layout json NOT NULL,
    is_premium boolean NOT NULL,
    price_paise integer NOT NULL,
    is_active boolean NOT NULL,
    sort_order integer NOT NULL,
    created_at timestamp without time zone NOT NULL
);


--
-- Name: resume_templates_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.resume_templates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: resume_templates_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.resume_templates_id_seq OWNED BY public.resume_templates.id;


--
-- Name: resumes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.resumes (
    id integer NOT NULL,
    user_id integer NOT NULL,
    title character varying(150) NOT NULL,
    template_id integer,
    country character varying(10) NOT NULL,
    job_category character varying(40) NOT NULL,
    target_job_title character varying(200),
    target_job_description text,
    data json NOT NULL,
    ats_score double precision,
    is_primary boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


--
-- Name: resumes_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.resumes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: resumes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.resumes_id_seq OWNED BY public.resumes.id;


--
-- Name: template_purchases; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.template_purchases (
    id integer NOT NULL,
    user_id integer NOT NULL,
    template_id integer NOT NULL,
    order_id integer,
    granted_by_admin boolean NOT NULL,
    created_at timestamp without time zone NOT NULL
);


--
-- Name: template_purchases_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.template_purchases_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: template_purchases_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.template_purchases_id_seq OWNED BY public.template_purchases.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id integer NOT NULL,
    email character varying(255) NOT NULL,
    hashed_password character varying(255) NOT NULL,
    full_name character varying(255),
    role character varying(20) NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    is_verified boolean DEFAULT true NOT NULL,
    auth_provider character varying(20) DEFAULT 'local'::character varying NOT NULL,
    google_id character varying(64),
    avatar_url character varying(500),
    token_version integer DEFAULT 0 NOT NULL,
    failed_login_attempts integer DEFAULT 0 NOT NULL,
    locked_until timestamp without time zone,
    last_login_at timestamp without time zone,
    plan character varying(20) DEFAULT 'free'::character varying NOT NULL,
    plan_expires_at timestamp without time zone
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
-- Name: ai_usage id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_usage ALTER COLUMN id SET DEFAULT nextval('public.ai_usage_id_seq'::regclass);


--
-- Name: applications id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.applications ALTER COLUMN id SET DEFAULT nextval('public.applications_id_seq'::regclass);


--
-- Name: audit_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs ALTER COLUMN id SET DEFAULT nextval('public.audit_logs_id_seq'::regclass);


--
-- Name: employees emp_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employees ALTER COLUMN emp_id SET DEFAULT nextval('public.employees_emp_id_seq'::regclass);


--
-- Name: jobs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.jobs ALTER COLUMN id SET DEFAULT nextval('public.jobs_id_seq'::regclass);


--
-- Name: otp_codes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.otp_codes ALTER COLUMN id SET DEFAULT nextval('public.otp_codes_id_seq'::regclass);


--
-- Name: payment_orders id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_orders ALTER COLUMN id SET DEFAULT nextval('public.payment_orders_id_seq'::regclass);


--
-- Name: resume_downloads id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resume_downloads ALTER COLUMN id SET DEFAULT nextval('public.resume_downloads_id_seq'::regclass);


--
-- Name: resume_templates id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resume_templates ALTER COLUMN id SET DEFAULT nextval('public.resume_templates_id_seq'::regclass);


--
-- Name: resumes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resumes ALTER COLUMN id SET DEFAULT nextval('public.resumes_id_seq'::regclass);


--
-- Name: template_purchases id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.template_purchases ALTER COLUMN id SET DEFAULT nextval('public.template_purchases_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: ai_usage; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.ai_usage (id, user_id, day, count) FROM stdin;
1	3	2026-10-11	2
2	4	2026-10-11	15
3	3	2026-10-21	1
\.


--
-- Data for Name: app_settings; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.app_settings (key, value, updated_at) FROM stdin;
free_daily_ai_limit	15	2026-10-11 12:40:03.936628
\.


--
-- Data for Name: applications; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.applications (id, user_id, job_id, status, cover_letter, notes, match_score, applied_at, created_at, updated_at) FROM stdin;
2	5	2	offered	\N	Offer received	80	2026-06-06 17:19:01.19327	2026-06-06 17:19:01.19327	2026-06-06 17:30:07.541651
1	4	1	applied	\N	Great match	92	2026-06-06 17:19:01.189272	2026-06-06 17:19:01.189272	2026-10-11 14:50:05.640368
3	4	3	saved	Dear Hiring Manager at AI Ventures,\n\nI'm thrilled to apply for the Machine Learning Engineer position at AI Ventures, where I can leverage my passion for machine learning and MLOps to drive innovation and impact. With a strong foundation in Python and experience deploying ML models to production, I'm confident that I can make a significant contribution to your team.\n\nThroughout my career as a Senior Backend Engineer at TechCorp, I've developed expertise in building and deploying scalable REST APIs. Notably, I successfully deployed ML models to production using Docker and Kubernetes, showcasing my ability to bridge the gap between model development and deployment. Additionally, I've honed my skills in Python, PyTorch, and TensorFlow, which I believe will serve me well in this role. My experience with FastAPI and PostgreSQL has also given me a solid understanding of data storage and retrieval, essential for building reliable ML pipelines.\n\nWhat draws me to AI Ventures is the company's commitment to advancing AI research and innovation. I'm impressed by the organization's cutting-edge approach to machine learning and its dedication to pushing the boundaries of what's possible. I'm excited about the prospect of collaborating with a talented team of engineers and researchers to develop and deploy innovative ML models that drive real-world impact.\n\nI would welcome the opportunity to discuss how my skills and experience align with the requirements of this role. Thank you for considering my application. I look forward to the chance to contribute to AI Ventures' mission to shape the future of AI.\n\nSincerely,\nAlice Johnson	Review later	80	2026-10-11 14:44:06.590568	2026-06-06 17:19:01.19527	2026-10-11 14:53:21.502406
\.


--
-- Data for Name: audit_logs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.audit_logs (id, user_id, action, target_type, target_id, detail, ip, created_at) FROM stdin;
6	3	user.login	\N	\N	null	127.0.0.1	2026-10-11 12:40:03.791612
7	3	admin.grant_template	user	6	{"template_id": 11}	127.0.0.1	2026-10-11 12:40:03.889966
8	3	admin.settings_update	\N	\N	{"free_daily_ai_limit": "15"}	127.0.0.1	2026-10-11 12:40:03.93961
10	4	user.login	\N	\N	null	127.0.0.1	2026-10-11 12:40:53.593736
11	4	user.login	\N	\N	null	127.0.0.1	2026-10-11 12:42:19.08044
12	4	user.login	\N	\N	null	127.0.0.1	2026-10-11 12:45:53.135764
13	4	user.login	\N	\N	null	127.0.0.1	2026-10-11 13:07:58.124871
14	4	user.login	\N	\N	null	127.0.0.1	2026-10-11 13:08:46.015219
15	3	user.login	\N	\N	null	127.0.0.1	2026-10-11 13:08:48.380153
16	4	user.login	\N	\N	null	127.0.0.1	2026-10-11 13:09:09.439772
17	4	user.login	\N	\N	null	127.0.0.1	2026-10-11 13:09:57.280662
18	3	user.login	\N	\N	null	127.0.0.1	2026-10-11 13:09:59.634754
19	3	user.login	\N	\N	null	127.0.0.1	2026-10-11 13:11:11.519154
20	3	user.login	\N	\N	null	127.0.0.1	2026-10-11 13:11:40.560147
26	3	user.login	\N	\N	null	127.0.0.1	2026-10-11 13:13:30.214754
27	3	admin.grant_template	user	7	{"template_id": 11}	127.0.0.1	2026-10-11 13:13:30.272538
28	3	admin.settings_update	\N	\N	{"free_daily_ai_limit": "15"}	127.0.0.1	2026-10-11 13:13:30.309753
1	\N	user.register	\N	\N	null	127.0.0.1	2026-10-11 12:39:55.940205
2	\N	user.verify_email	\N	\N	null	127.0.0.1	2026-10-11 12:39:56.305745
3	\N	user.reset_password	\N	\N	null	127.0.0.1	2026-10-11 12:39:59.555231
4	\N	user.login	\N	\N	null	127.0.0.1	2026-10-11 12:39:59.871085
5	\N	user.change_password	\N	\N	null	127.0.0.1	2026-10-11 12:40:01.106182
9	\N	user.locked	\N	\N	null	127.0.0.1	2026-10-11 12:40:07.848605
21	\N	user.register	\N	\N	null	127.0.0.1	2026-10-11 13:13:22.581788
22	\N	user.verify_email	\N	\N	null	127.0.0.1	2026-10-11 13:13:22.935084
23	\N	user.reset_password	\N	\N	null	127.0.0.1	2026-10-11 13:13:26.016176
24	\N	user.login	\N	\N	null	127.0.0.1	2026-10-11 13:13:26.329194
25	\N	user.change_password	\N	\N	null	127.0.0.1	2026-10-11 13:13:27.538949
29	\N	user.locked	\N	\N	null	127.0.0.1	2026-10-11 13:13:34.184287
30	3	user.login	\N	\N	null	127.0.0.1	2026-10-11 14:28:02.823635
31	4	user.login	\N	\N	null	127.0.0.1	2026-10-11 14:34:45.183464
32	4	user.login	\N	\N	null	127.0.0.1	2026-10-11 14:47:57.103965
33	3	user.login	\N	\N	null	127.0.0.1	2026-10-21 05:50:13.744944
\.


--
-- Data for Name: employees; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.employees (emp_id, user_id, resume_text, skills, experience_years, education, phone, linkedin_url, created_at, updated_at) FROM stdin;
3	4	Alice Johnson | alice@example.com\n\nEXPERIENCE\nSenior Backend Engineer - TechCorp (2021-Present)\n  - Built REST APIs with FastAPI and PostgreSQL\n  - Deployed ML models to production using Docker and Kubernetes\n\nSKILLS\nPython, FastAPI, PostgreSQL, React, Docker, Machine Learning\n	python,fastapi,postgresql,react,machine learning	5	\N	\N	\N	2026-06-06 17:19:00.844797	2026-06-06 17:19:00.844797
4	5	Bob Smith | bob@example.com\n\nEXPERIENCE\nFrontend Developer - WebAgency (2020-Present)\n  - Built SPAs with React and TypeScript\n  - Integrated REST APIs\n\nSKILLS\nJavaScript, TypeScript, React, Node.js\n	javascript,react,node.js,typescript	4	\N	\N	\N	2026-06-06 17:19:01.173282	2026-06-06 17:19:01.173282
\.


--
-- Data for Name: jobs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.jobs (id, title, company, location, description, requirements, salary_min, salary_max, job_type, remote, url, source, is_active, posted_at, created_at) FROM stdin;
1	Senior Python Developer	DataFlow Inc.	San Francisco, CA	Build scalable APIs and data pipelines.	Python, FastAPI, PostgreSQL, Docker	120000	160000	full-time	t	https://example.com/jobs/1	linkedin	t	2026-06-06 17:19:01.178278	2026-06-06 17:19:01.178278
2	React Frontend Engineer	CloudSoft	Austin, TX	Build UI with React and TypeScript.	React, TypeScript, REST APIs	100000	140000	full-time	t	https://example.com/jobs/2	indeed	t	2026-06-06 17:19:01.182276	2026-06-06 17:19:01.183276
3	Machine Learning Engineer	AI Ventures	New York, NY	Train and deploy ML models.	Python, PyTorch or TensorFlow, MLOps	140000	190000	full-time	f	https://example.com/jobs/3	manual	t	2026-06-06 17:19:01.184275	2026-06-06 17:19:01.184275
4	QA Engineer	Test Corp	Remote	Test apps	Testing, API	\N	\N	full-time	t	\N	\N	t	\N	2026-06-06 17:26:55.076644
\.


--
-- Data for Name: otp_codes; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.otp_codes (id, email, purpose, code_hash, attempts, consumed, expires_at, created_at) FROM stdin;
1	qa_585bc2@example.com	verify_email	bc06d7d59c1d38f4c89a0b8cb0fae7fbeb9a803df0ab8821507a3c8c5f7dc520	1	t	2026-10-11 12:44:55.924807	2026-10-11 12:39:55.935208
2	qa_585bc2@example.com	reset_password	8f2897ea06934ae3154d337ccd8a924eaccd599250db5a0b2e3e3f13ff689a9a	0	t	2026-10-11 12:44:59.15851	2026-10-11 12:39:59.165517
3	qa_0e2bf9@example.com	verify_email	82e7b5aa74eb458e0a02d85d55b1b16c04b9b993c04d7afed4495e3b8714ee3c	1	t	2026-10-11 13:18:22.573788	2026-10-11 13:13:22.579789
4	qa_0e2bf9@example.com	reset_password	281bc45e44a44607fadb0b963193ac5c21195eee5d9cd236bc1864c9d8808ba6	0	t	2026-10-11 13:18:25.653338	2026-10-11 13:13:25.660322
\.


--
-- Data for Name: payment_orders; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.payment_orders (id, user_id, razorpay_order_id, razorpay_payment_id, amount_paise, currency, status, item_type, item_id, description, meta, created_at, paid_at) FROM stdin;
\.


--
-- Data for Name: resume_downloads; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.resume_downloads (id, user_id, resume_id, template_id, created_at) FROM stdin;
3	3	\N	12	2026-10-11 13:11:13.431069
4	3	\N	12	2026-10-11 13:11:42.413213
7	3	9	3	2026-10-11 14:32:50.904304
8	3	8	5	2026-10-11 14:33:02.645662
9	3	8	5	2026-10-11 14:33:11.281729
\.


--
-- Data for Name: resume_templates; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.resume_templates (id, slug, name, description, category, style, layout, is_premium, price_paise, is_active, sort_order, created_at) FROM stdin;
1	ats-classic	ATS Classic	Single-column, parser-friendly layout that works for any industry.	general	classic	{"layout": "classic", "primary": "#111827", "accent": "#374151", "font": "serif", "photo": false, "heading": "underline"}	f	0	t	0	2026-10-11 12:38:57.23755
2	clean-minimal	Clean Minimal	Lots of whitespace and crisp typography.	general	minimal	{"layout": "minimal", "primary": "#0f172a", "accent": "#64748b", "font": "sans", "photo": false, "heading": "caps"}	f	0	t	1	2026-10-11 12:38:57.23755
3	modern-blue	Modern Blue	Bold colour header — popular for tech roles.	it	modern	{"layout": "band", "primary": "#1d4ed8", "accent": "#3b82f6", "font": "sans", "photo": false, "heading": "bar"}	f	0	t	2	2026-10-11 12:38:57.23755
4	professional-navy	Professional Navy	Conservative and polished for corporate roles.	finance	professional	{"layout": "executive", "primary": "#1e3a5f", "accent": "#c9a227", "font": "sans", "photo": false, "heading": "underline"}	f	0	t	3	2026-10-11 12:38:57.23755
5	tech-sidebar	Tech Sidebar	Skills sidebar to surface your tech stack.	it	modern	{"layout": "sidebar", "primary": "#0f766e", "accent": "#14b8a6", "font": "sans", "photo": false, "heading": "caps"}	f	0	t	4	2026-10-11 12:38:57.23755
6	medical-cv	Medical CV	Structured CV for doctors, nurses and clinicians.	healthcare	academic	{"layout": "academic", "primary": "#0e7490", "accent": "#0891b2", "font": "serif", "photo": false, "heading": "underline"}	f	0	t	5	2026-10-11 12:38:57.23755
7	engineer-pro	Engineer Pro	Two-column layout highlighting projects and tools.	engineering	professional	{"layout": "split", "primary": "#334155", "accent": "#f59e0b", "font": "sans", "photo": false, "heading": "bar"}	f	0	t	6	2026-10-11 12:38:57.23755
8	fresher-start	Fresher Start	Education-first layout for students and graduates.	general	modern	{"layout": "compact", "primary": "#7c3aed", "accent": "#a78bfa", "font": "sans", "photo": false, "heading": "pill"}	f	0	t	7	2026-10-11 12:38:57.23755
9	educator	Educator	Clean classic layout for teachers and trainers.	education	classic	{"layout": "classic", "primary": "#14532d", "accent": "#16a34a", "font": "serif", "photo": false, "heading": "caps"}	f	0	t	8	2026-10-11 12:38:57.23755
10	sales-impact	Sales Impact	Make your numbers pop for sales & marketing.	sales	modern	{"layout": "band", "primary": "#b91c1c", "accent": "#ef4444", "font": "sans", "photo": false, "heading": "bar"}	f	0	t	9	2026-10-11 12:38:57.23755
11	executive-gold	Executive Gold	Boardroom-ready design for senior leaders.	finance	executive	{"layout": "executive", "primary": "#111827", "accent": "#b8860b", "font": "serif", "photo": false, "heading": "caps"}	t	14900	t	10	2026-10-11 12:38:57.23755
12	doctor-elite	Doctor Elite	Photo sidebar with licences & registrations up front.	healthcare	professional	{"layout": "sidebar", "primary": "#075985", "accent": "#38bdf8", "font": "sans", "photo": true, "heading": "caps"}	t	9900	t	11	2026-10-11 12:38:57.23755
13	senior-consultant	Senior Consultant	Detailed CV for consultants with publications & research.	healthcare	academic	{"layout": "academic", "primary": "#4c1d95", "accent": "#7c3aed", "font": "serif", "photo": false, "heading": "underline"}	t	9900	t	12	2026-10-11 12:38:57.23755
14	dev-timeline	Developer Timeline	Career timeline with tech-stack chips.	it	modern	{"layout": "timeline", "primary": "#0f172a", "accent": "#22d3ee", "font": "sans", "photo": false, "heading": "bar"}	t	7900	t	13	2026-10-11 12:38:57.23755
15	cloud-architect	Cloud Architect	Dark-accent two-column for senior engineers.	it	professional	{"layout": "split", "primary": "#1e293b", "accent": "#6366f1", "font": "sans", "photo": false, "heading": "pill"}	t	9900	t	14	2026-10-11 12:38:57.23755
16	creative-studio	Creative Studio	Expressive layout for designers.	creative	creative	{"layout": "creative", "primary": "#be185d", "accent": "#f472b6", "font": "sans", "photo": true, "heading": "pill"}	t	12900	t	15	2026-10-11 12:38:57.23755
17	designer-portfolio	Designer Portfolio	Portfolio links and projects first.	creative	modern	{"layout": "sidebar", "primary": "#18181b", "accent": "#f97316", "font": "sans", "photo": true, "heading": "caps"}	t	9900	t	16	2026-10-11 12:38:57.23755
18	structural	Structural	Timeline layout for civil & mechanical engineers.	engineering	modern	{"layout": "timeline", "primary": "#78350f", "accent": "#f59e0b", "font": "sans", "photo": false, "heading": "bar"}	t	7900	t	17	2026-10-11 12:38:57.23755
19	legal-counsel	Legal Counsel	Refined serif design for lawyers.	legal	executive	{"layout": "executive", "primary": "#1c1917", "accent": "#78716c", "font": "serif", "photo": false, "heading": "underline"}	t	9900	t	18	2026-10-11 12:38:57.23755
20	gulf-pro	Gulf Pro	Photo + nationality/visa fields for GCC applications.	general	professional	{"layout": "sidebar", "primary": "#14532d", "accent": "#ca8a04", "font": "sans", "photo": true, "heading": "caps"}	t	7900	t	19	2026-10-11 12:38:57.23755
21	euro-modern	Euro Modern	Europe-style CV with photo header.	general	modern	{"layout": "band", "primary": "#1e40af", "accent": "#facc15", "font": "sans", "photo": true, "heading": "bar"}	t	7900	t	20	2026-10-11 12:38:57.23755
22	hospitality-star	Hospitality Star	Warm, friendly layout for service roles.	hospitality	creative	{"layout": "creative", "primary": "#9a3412", "accent": "#fb923c", "font": "sans", "photo": true, "heading": "pill"}	t	4900	t	21	2026-10-11 12:38:57.23755
23	professor-cv	Professor CV	Academic CV with publications, grants and teaching.	education	academic	{"layout": "academic", "primary": "#312e81", "accent": "#6366f1", "font": "serif", "photo": false, "heading": "caps"}	t	7900	t	22	2026-10-11 12:38:57.23755
24	marketing-bold	Marketing Bold	High-contrast layout for growth marketers.	sales	creative	{"layout": "creative", "primary": "#5b21b6", "accent": "#22c55e", "font": "sans", "photo": false, "heading": "pill"}	t	9900	t	23	2026-10-11 12:38:57.23755
\.


--
-- Data for Name: resumes; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.resumes (id, user_id, title, template_id, country, job_category, target_job_title, target_job_description, data, ats_score, is_primary, created_at, updated_at) FROM stdin;
8	3	Nandhakumarm_Resume1	5	AU	it	\N	\N	{"personal": {"full_name": "NANDHAKUMAR M", "headline": "Senior Power Platform & AI Solution Engineer", "email": "nandhu29696@gmail.com", "phone": "+91 (638) 569-2143", "location": "", "website": "", "linkedin": "https://www.linkedin.com/in/nandhakumar-m-85344a178", "github": "", "photo": "", "date_of_birth": "", "nationality": "", "marital_status": "", "gender": "", "visa_status": ""}, "summary": "Power Platform Developer with 4+ years of experience delivering 15+ Canvas Apps and enterprise automation solutions. Skilled in integrating AI services (Azure OpenAI, AI tools) with PowerApps and Power Automate, building API-driven workflows and scalable data solutions using Dataverse and Azure Data Lake. Experienced in Python-based integrations, REST APIs, and process automation, with a strong focus on building intelligent, secure, and production-ready solutions.", "experience": [{"id": "a3b9c4ec", "title": "Senior Software Engineer", "company": "Firstsource Solutions Limited", "location": "", "start": "04/2025", "end": "", "current": true, "bullets": ["Designed and implemented AI-integrated Power Platform solutions, embedding AI capabilities into PowerApps and Power Automate workflows", "Integrated AI services (Azure OpenAI / AI tools) using REST APIs and automated workflows for intelligent decision-making", "Built and consumed REST APIs for AI and enterprise systems, enabling scalable and secure integrations", "Worked with Python-based services / scripting (if even basic) for API orchestration and data processing", "Implemented Dataverse-based scalable solutions with governance and structured data modelling", "Designed solutions considering performance, security, and cost optimization"]}, {"id": "117047ba", "title": "Junior Software Engineer", "company": "Firstsource Solutions Limited", "location": "", "start": "10/2021", "end": "03/2025", "current": false, "bullets": ["Developed and delivered 15+ PowerApps Canvas applications, streamlining workflows and reducing manual effort across multiple business units", "Designed and managed SharePoint Online and Dataverse data models, ensuring secure, scalable, and structured data management", "Built automated workflows using Power Automate, including approval systems, notifications, and scheduled integrations, improving process efficiency by 40%", "Developed and deployed scalable apps with Spring Boot (Microservices Architecture) and React.js, improving system efficiency by 35%", "Led full-cycle development of ILM, BCM, and a Healthcare (NGO) project", "Streamlined CI/CD pipelines, resulting in a 50% faster release cycle", "Created technical documentation for APIs and system architecture, reducing onboarding time by 40% and improving developer efficiency by 25%"]}, {"id": "0dd087e1", "title": "Full Stack Developer", "company": "Invicious Technologies llb", "location": "", "start": "03/2021", "end": "09/2021", "current": false, "bullets": ["Led development of mobile and web applications using Spring Boot, React.js, REST APIs, MySQL, MongoDB, AWS, and Android", "Developed and optimized the Hyper App project, improving system performance by 30%", "Built REST APIs using Spring Boot, ensuring seamless frontend-backend communication and reducing API response time by 25%", "Managed AWS cloud deployments, optimizing resource usage and cutting infrastructure", "Led a cross-functional team, boosting project delivery speed by 35% through clear task planning and coordination", "Integrated MySQL and MongoDB, improving data retrieval speed by 40%"]}, {"id": "4cd29dca", "title": "Java Web Developer (Internship)", "company": "Smartway Industrial Automation", "location": "", "start": "12/2019", "end": "05/2020", "current": false, "bullets": ["Developed a real-time dashboard using Java & JSP, improving user accessibility by 20%", "Led development of the final year project, applying full-stack development principles to deliver a functional web solution"]}], "education": [{"id": "851a1636", "degree": "Master of Computer Applications", "institution": "Hindusthan college of Engineering and Technology", "location": "", "start": "05/2017", "end": "05/2020", "grade": "Coimbatore, India", "details": ""}, {"id": "a72ed12e", "degree": "Bachelor of Computer Applications", "institution": "Hindusthan college of Arts and Science", "location": "", "start": "05/2013", "end": "05/2016", "grade": "Coimbatore, India", "details": ""}], "skills": [{"id": "6d5bf9cc", "name": "Skills", "items": ["Microsoft Power Platform", "PowerApps (Canvas Apps)", "Power Automate", "Dataverse", "SharePoint Online", "Power Pages", "(POC)", "Copilot Studio (POC)", "Custom", "Connectors", "API Integration", "Solution Design", "Governance", "Frontend", "React.js", "Redux", "JavaScript (ES6+)", "TypeScript", "HTML5", "CSS3", "Webpack", "Backend", "Python (API Integration", "Automation)", "Java", "(Spring Boot)", "Node.js", "Database", "PostgreSQL", "MySQL (Schema Design", "Query", "Optimization)", "MongoDB (NoSQL Data", "Modeling)", "Cloud & DevOps", "AWS", "Docker", "Azure DevOps", "CI/CD", "Git"]}], "projects": [], "certifications": [], "licenses": [], "publications": [], "awards": [], "volunteer": [], "languages": [], "interests": [], "references": [], "declaration": "", "custom_sections": [], "section_order": ["summary", "skills", "experience", "education", "certifications", "references", "projects"], "hidden_sections": []}	\N	f	2026-10-11 14:29:58.287113	2026-10-11 14:30:59.462009
9	3	My Resume	2	US	it	\N	\N	{"personal": {"full_name": "Admin User", "headline": "", "email": "admin@example.com", "phone": "", "location": "", "website": "", "linkedin": "", "github": "", "photo": "", "date_of_birth": "", "nationality": "", "marital_status": "", "gender": "", "visa_status": ""}, "summary": "", "experience": [], "education": [], "skills": [], "projects": [], "certifications": [], "licenses": [], "publications": [], "awards": [], "volunteer": [], "languages": [], "interests": [], "references": [], "declaration": "", "custom_sections": [], "section_order": ["summary", "experience", "skills", "education", "projects", "certifications"], "hidden_sections": []}	\N	f	2026-10-11 14:30:39.52311	2026-10-21 05:51:02.052066
\.


--
-- Data for Name: template_purchases; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.template_purchases (id, user_id, template_id, order_id, granted_by_admin, created_at) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.users (id, email, hashed_password, full_name, role, is_active, created_at, updated_at, is_verified, auth_provider, google_id, avatar_url, token_version, failed_login_attempts, locked_until, last_login_at, plan, plan_expires_at) FROM stdin;
5	bob@example.com	$2b$12$ZBOKNIbRM.Pvz5MWYLGe6Ok/9T3jcZKYVnObHLGhbuebWMDCekmj6	Bob Smith	employee	t	2026-06-06 17:19:01.171282	2026-06-06 17:19:01.171282	t	local	\N	\N	0	0	\N	\N	free	\N
4	alice@example.com	$2b$12$gwL0Lt0iv/SEO8xfQIN1Xed9OhPzsyb3KYqxSa/rSRE6j9QaTwAx.	Alice Johnson	employee	t	2026-06-06 17:19:00.839801	2026-10-11 14:47:57.106964	t	local	\N	\N	0	0	\N	2026-10-11 14:47:57.101966	free	\N
3	admin@example.com	$2b$12$LHCi31MNP/ZAqP6q4OuaC.ct36Q79NAPN26679VRPcWq7CNZ0NN0.	Admin User	super_admin	t	2026-06-06 17:19:00.473219	2026-10-21 05:50:13.892561	t	local	\N	\N	1	0	\N	2026-10-21 05:50:13.742944	free	\N
\.


--
-- Name: ai_usage_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.ai_usage_id_seq', 3, true);


--
-- Name: applications_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.applications_id_seq', 5, true);


--
-- Name: audit_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.audit_logs_id_seq', 33, true);


--
-- Name: employees_emp_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.employees_emp_id_seq', 6, true);


--
-- Name: jobs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.jobs_id_seq', 4, true);


--
-- Name: otp_codes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.otp_codes_id_seq', 4, true);


--
-- Name: payment_orders_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.payment_orders_id_seq', 1, false);


--
-- Name: resume_downloads_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.resume_downloads_id_seq', 9, true);


--
-- Name: resume_templates_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.resume_templates_id_seq', 24, true);


--
-- Name: resumes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.resumes_id_seq', 9, true);


--
-- Name: template_purchases_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.template_purchases_id_seq', 2, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.users_id_seq', 7, true);


--
-- Name: ai_usage ai_usage_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_usage
    ADD CONSTRAINT ai_usage_pkey PRIMARY KEY (id);


--
-- Name: app_settings app_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app_settings
    ADD CONSTRAINT app_settings_pkey PRIMARY KEY (key);


--
-- Name: applications applications_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.applications
    ADD CONSTRAINT applications_pkey PRIMARY KEY (id);


--
-- Name: audit_logs audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_pkey PRIMARY KEY (id);


--
-- Name: employees employees_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employees
    ADD CONSTRAINT employees_pkey PRIMARY KEY (emp_id);


--
-- Name: jobs jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.jobs
    ADD CONSTRAINT jobs_pkey PRIMARY KEY (id);


--
-- Name: otp_codes otp_codes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.otp_codes
    ADD CONSTRAINT otp_codes_pkey PRIMARY KEY (id);


--
-- Name: payment_orders payment_orders_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_orders
    ADD CONSTRAINT payment_orders_pkey PRIMARY KEY (id);


--
-- Name: resume_downloads resume_downloads_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resume_downloads
    ADD CONSTRAINT resume_downloads_pkey PRIMARY KEY (id);


--
-- Name: resume_templates resume_templates_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resume_templates
    ADD CONSTRAINT resume_templates_pkey PRIMARY KEY (id);


--
-- Name: resumes resumes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resumes
    ADD CONSTRAINT resumes_pkey PRIMARY KEY (id);


--
-- Name: template_purchases template_purchases_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.template_purchases
    ADD CONSTRAINT template_purchases_pkey PRIMARY KEY (id);


--
-- Name: ai_usage uq_ai_usage_user_day; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_usage
    ADD CONSTRAINT uq_ai_usage_user_day UNIQUE (user_id, day);


--
-- Name: template_purchases uq_user_template; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.template_purchases
    ADD CONSTRAINT uq_user_template UNIQUE (user_id, template_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_ai_usage_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ai_usage_user_id ON public.ai_usage USING btree (user_id);


--
-- Name: ix_applications_job_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_applications_job_id ON public.applications USING btree (job_id);


--
-- Name: ix_applications_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_applications_user_id ON public.applications USING btree (user_id);


--
-- Name: ix_audit_logs_action; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_logs_action ON public.audit_logs USING btree (action);


--
-- Name: ix_audit_logs_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_logs_created_at ON public.audit_logs USING btree (created_at);


--
-- Name: ix_audit_logs_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_logs_user_id ON public.audit_logs USING btree (user_id);


--
-- Name: ix_employees_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_employees_user_id ON public.employees USING btree (user_id);


--
-- Name: ix_jobs_company; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_jobs_company ON public.jobs USING btree (company);


--
-- Name: ix_jobs_title; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_jobs_title ON public.jobs USING btree (title);


--
-- Name: ix_otp_codes_email; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_otp_codes_email ON public.otp_codes USING btree (email);


--
-- Name: ix_payment_orders_razorpay_order_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_payment_orders_razorpay_order_id ON public.payment_orders USING btree (razorpay_order_id);


--
-- Name: ix_payment_orders_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_payment_orders_status ON public.payment_orders USING btree (status);


--
-- Name: ix_payment_orders_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_payment_orders_user_id ON public.payment_orders USING btree (user_id);


--
-- Name: ix_resume_downloads_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_resume_downloads_user_id ON public.resume_downloads USING btree (user_id);


--
-- Name: ix_resume_templates_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_resume_templates_category ON public.resume_templates USING btree (category);


--
-- Name: ix_resume_templates_slug; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_resume_templates_slug ON public.resume_templates USING btree (slug);


--
-- Name: ix_resumes_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_resumes_user_id ON public.resumes USING btree (user_id);


--
-- Name: ix_template_purchases_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_template_purchases_user_id ON public.template_purchases USING btree (user_id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ai_usage ai_usage_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_usage
    ADD CONSTRAINT ai_usage_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: applications applications_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.applications
    ADD CONSTRAINT applications_job_id_fkey FOREIGN KEY (job_id) REFERENCES public.jobs(id);


--
-- Name: applications applications_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.applications
    ADD CONSTRAINT applications_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: audit_logs audit_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: employees employees_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employees
    ADD CONSTRAINT employees_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: payment_orders payment_orders_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_orders
    ADD CONSTRAINT payment_orders_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: resume_downloads resume_downloads_resume_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resume_downloads
    ADD CONSTRAINT resume_downloads_resume_id_fkey FOREIGN KEY (resume_id) REFERENCES public.resumes(id) ON DELETE SET NULL;


--
-- Name: resume_downloads resume_downloads_template_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resume_downloads
    ADD CONSTRAINT resume_downloads_template_id_fkey FOREIGN KEY (template_id) REFERENCES public.resume_templates(id) ON DELETE SET NULL;


--
-- Name: resume_downloads resume_downloads_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resume_downloads
    ADD CONSTRAINT resume_downloads_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: resumes resumes_template_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resumes
    ADD CONSTRAINT resumes_template_id_fkey FOREIGN KEY (template_id) REFERENCES public.resume_templates(id) ON DELETE SET NULL;


--
-- Name: resumes resumes_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resumes
    ADD CONSTRAINT resumes_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: template_purchases template_purchases_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.template_purchases
    ADD CONSTRAINT template_purchases_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.payment_orders(id) ON DELETE SET NULL;


--
-- Name: template_purchases template_purchases_template_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.template_purchases
    ADD CONSTRAINT template_purchases_template_id_fkey FOREIGN KEY (template_id) REFERENCES public.resume_templates(id) ON DELETE CASCADE;


--
-- Name: template_purchases template_purchases_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.template_purchases
    ADD CONSTRAINT template_purchases_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

