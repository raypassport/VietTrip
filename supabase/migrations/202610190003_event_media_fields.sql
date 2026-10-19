-- Fields used by the itinerary cards in the mobile UI.

alter table public.events
  add column if not exists tiktok_url text,
  add column if not exists thumbnail_url text;
