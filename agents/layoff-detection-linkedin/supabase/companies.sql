-- Company Discovery Engine (Slice A) migration.
-- Run this ONCE in the Supabase SQL editor, in addition to layoff_posts.sql.

-- 1) Two new columns on the posts table: the canonical company key each post
--    rolls up under, and who posted it (employee/recruiter/founder/company/news).
alter table public.layoff_posts
    add column if not exists company_key text,
    add column if not exists poster_role text;

create index if not exists layoff_posts_company_key_idx
    on public.layoff_posts (company_key);

-- 2) The company rollup table — one row per discovered company, with signal
--    counts and an aggregate confidence score (see agent/companies.py).
create table if not exists public.companies (
    company_key        text primary key,   -- normalized dedupe key
    company_name       text,               -- best display name seen
    employee_posts     integer default 0,
    recruiter_posts    integer default 0,
    founder_posts      integer default 0,
    announcement_posts integer default 0,
    news_posts         integer default 0,
    total_posts        integer default 0,
    confidence         numeric default 0,
    locations          text,
    first_seen         timestamptz default now(),
    updated_at         timestamptz default now()
);

create index if not exists companies_confidence_idx
    on public.companies (confidence desc);

-- keep updated_at fresh on upsert (reuses the touch fn from layoff_posts.sql;
-- redefined here so this file can run standalone)
create or replace function public.touch_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end $$;

drop trigger if exists companies_touch on public.companies;
create trigger companies_touch before update on public.companies
for each row execute function public.touch_updated_at();
