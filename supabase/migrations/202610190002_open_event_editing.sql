-- Open event editing for the shared friends-only trip site.
-- Anyone with the public site can create, update, or delete itinerary events.

grant select, insert, update, delete on public.events to anon, authenticated;

drop policy if exists "Anyone can add events" on public.events;
create policy "Anyone can add events"
on public.events for insert
to anon, authenticated
with check (trip_id = 'a78f459d-5d44-47d4-8c02-e28d0770eeec');

drop policy if exists "Anyone can update events" on public.events;
create policy "Anyone can update events"
on public.events for update
to anon, authenticated
using (trip_id = 'a78f459d-5d44-47d4-8c02-e28d0770eeec')
with check (trip_id = 'a78f459d-5d44-47d4-8c02-e28d0770eeec');

drop policy if exists "Anyone can delete events" on public.events;
create policy "Anyone can delete events"
on public.events for delete
to anon, authenticated
using (trip_id = 'a78f459d-5d44-47d4-8c02-e28d0770eeec');
