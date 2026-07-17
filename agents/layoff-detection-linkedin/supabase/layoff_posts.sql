-- Run this in the Supabase SQL editor to create the table the agent writes to.
create table if not exists public.layoff_posts (
    id           bigint generated always as identity primary key,
    source_url   text unique not null,          -- dedupe key
    source       text,                           -- 'linkedin' | 'news'
    company      text,
    person_name  text,
    role_hint    text,
    role_category text,
    country      text,
    is_us        boolean default false,
    headcount    integer,
    location     text,
    event_date   date,
    open_to_work boolean default false,
    is_qualified boolean default false,           -- validated: matches target job role (+ location)
    summary      text,
    confidence   numeric,
    created_at   timestamptz default now(),
    updated_at   timestamptz default now()
);

-- If your table already exists (created before is_qualified was added), run this
-- ONCE to add the new column without dropping data:
--   alter table public.layoff_posts add column if not exists is_qualified boolean default false;

create index if not exists layoff_posts_company_idx on public.layoff_posts (company);
create index if not exists layoff_posts_open_to_work_idx on public.layoff_posts (open_to_work);
create index if not exists layoff_posts_is_qualified_idx on public.layoff_posts (is_qualified);
create index if not exists layoff_posts_created_at_idx on public.layoff_posts (created_at desc);

-- keep updated_at fresh on upsert
create or replace function public.touch_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end $$;

drop trigger if exists layoff_posts_touch on public.layoff_posts;
create trigger layoff_posts_touch before update on public.layoff_posts
for each row execute function public.touch_updated_at();
