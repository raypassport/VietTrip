-- VietTrip trip-management MVP
-- Public itinerary, with writes restricted to trip owners and editors.

create extension if not exists pgcrypto;

create table if not exists public.trips (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique,
  name text not null,
  city text,
  starts_on date not null,
  ends_on date not null,
  timezone text not null default 'Asia/Ho_Chi_Minh',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint trips_date_order check (ends_on >= starts_on)
);

create table if not exists public.trip_members (
  trip_id uuid not null references public.trips(id) on delete cascade,
  email text not null,
  role text not null default 'viewer',
  created_at timestamptz not null default now(),
  primary key (trip_id, email),
  constraint trip_members_role check (role in ('owner', 'editor', 'viewer')),
  constraint trip_members_lowercase_email check (email = lower(email))
);

create table if not exists public.events (
  id uuid primary key default gen_random_uuid(),
  trip_id uuid not null references public.trips(id) on delete cascade,
  event_date date not null,
  start_time time,
  end_time time,
  title text not null,
  location text,
  description text,
  map_url text,
  sort_order integer not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint events_time_order check (
    end_time is null or start_time is null or end_time >= start_time
  )
);

create index if not exists events_trip_day_order_idx
  on public.events (trip_id, event_date, start_time, sort_order);

create or replace function public.touch_updated_at()
returns trigger
language plpgsql
set search_path = public
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists trips_touch_updated_at on public.trips;
create trigger trips_touch_updated_at
before update on public.trips
for each row execute function public.touch_updated_at();

drop trigger if exists events_touch_updated_at on public.events;
create trigger events_touch_updated_at
before update on public.events
for each row execute function public.touch_updated_at();

create or replace function public.can_edit_trip(target_trip_id uuid)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1
    from public.trip_members member
    where member.trip_id = target_trip_id
      and member.email = lower(coalesce(auth.jwt() ->> 'email', ''))
      and member.role in ('owner', 'editor')
  );
$$;

create or replace function public.owns_trip(target_trip_id uuid)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1
    from public.trip_members member
    where member.trip_id = target_trip_id
      and member.email = lower(coalesce(auth.jwt() ->> 'email', ''))
      and member.role = 'owner'
  );
$$;

revoke all on function public.can_edit_trip(uuid) from public;
revoke all on function public.owns_trip(uuid) from public;
grant execute on function public.can_edit_trip(uuid) to anon, authenticated;
grant execute on function public.owns_trip(uuid) to authenticated;

alter table public.trips enable row level security;
alter table public.trip_members enable row level security;
alter table public.events enable row level security;

drop policy if exists "Trips are publicly readable" on public.trips;
create policy "Trips are publicly readable"
on public.trips for select
to anon, authenticated
using (true);

drop policy if exists "Editors can update trips" on public.trips;
create policy "Editors can update trips"
on public.trips for update
to authenticated
using (public.can_edit_trip(id))
with check (public.can_edit_trip(id));

drop policy if exists "Members can view their trip membership" on public.trip_members;
create policy "Members can view their trip membership"
on public.trip_members for select
to authenticated
using (public.can_edit_trip(trip_id));

drop policy if exists "Owners can add trip members" on public.trip_members;
create policy "Owners can add trip members"
on public.trip_members for insert
to authenticated
with check (public.owns_trip(trip_id));

drop policy if exists "Owners can update trip members" on public.trip_members;
create policy "Owners can update trip members"
on public.trip_members for update
to authenticated
using (public.owns_trip(trip_id))
with check (public.owns_trip(trip_id));

drop policy if exists "Owners can remove trip members" on public.trip_members;
create policy "Owners can remove trip members"
on public.trip_members for delete
to authenticated
using (public.owns_trip(trip_id));

drop policy if exists "Events are publicly readable" on public.events;
create policy "Events are publicly readable"
on public.events for select
to anon, authenticated
using (true);

drop policy if exists "Editors can add events" on public.events;
create policy "Editors can add events"
on public.events for insert
to authenticated
with check (public.can_edit_trip(trip_id));

drop policy if exists "Editors can update events" on public.events;
create policy "Editors can update events"
on public.events for update
to authenticated
using (public.can_edit_trip(trip_id))
with check (public.can_edit_trip(trip_id));

drop policy if exists "Editors can delete events" on public.events;
create policy "Editors can delete events"
on public.events for delete
to authenticated
using (public.can_edit_trip(trip_id));

insert into public.trips (id, slug, name, city, starts_on, ends_on, timezone)
values (
  'a78f459d-5d44-47d4-8c02-e28d0770eeec',
  'hcmc-2026',
  'Ho Chi Minh City 2026',
  'Ho Chi Minh City',
  '2026-10-21',
  '2026-10-24',
  'Asia/Ho_Chi_Minh'
)
on conflict (slug) do update set
  name = excluded.name,
  city = excluded.city,
  starts_on = excluded.starts_on,
  ends_on = excluded.ends_on,
  timezone = excluded.timezone;

insert into public.trip_members (trip_id, email, role)
select id, 'raypassport@gmail.com', 'owner'
from public.trips
where slug = 'hcmc-2026'
on conflict (trip_id, email) do update set role = excluded.role;

grant select on public.trips, public.events to anon, authenticated;
grant select, insert, update, delete on public.events to authenticated;
grant select, insert, update, delete on public.trip_members to authenticated;
grant update on public.trips to authenticated;
