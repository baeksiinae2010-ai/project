-- Local stand-in for a Supabase project (Postgres + PostgREST).
-- PostgREST connects as `authenticator`, which switches to `anon` for
-- requests signed with the local dev JWT (see .env.base44-defaults).

create role anon nologin;
create role authenticator login password 'base44-local-authenticator' noinherit;
grant anon to authenticator;

create table public.project (
    id               text primary key,
    grade_class      text,
    study_hours      double precision,
    academic_score   integer,
    sleep_hours      double precision,
    tired_score      integer,
    favorite_subject text,
    created_at       timestamptz default now()
);

grant usage on schema public to anon;
grant select, insert, update, delete on public.project to anon;

-- A few sample responses so the "데이터 분석" charts have something to show.
insert into public.project
    (id, grade_class, study_hours, academic_score, sleep_hours, tired_score, favorite_subject)
values
    ('S_001', '1-3', 2.0, 62, 7.5, 4, '체육'),
    ('S_002', '1-3', 4.5, 81, 6.5, 6, '수학'),
    ('S_003', '2-1', 3.0, 74, 7.0, 5, '음악'),
    ('S_004', '2-1', 6.0, 91, 5.5, 8, '과학'),
    ('S_005', '2-8', 1.5, 55, 8.0, 3, '미술'),
    ('S_006', '3-2', 5.0, 86, 6.0, 7, '영어'),
    ('S_007', '3-2', 3.5, 78, 7.0, 5, '국어'),
    ('S_008', '1-5', 4.0, 83, 6.5, 6, '정보'),
    ('S_009', '2-4', 2.5, 69, 7.5, 4, '사회'),
    ('S_010', '3-7', 7.0, 94, 5.0, 9, '수학');
