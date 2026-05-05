import { createBrowserClient } from "@supabase/ssr"

export function createSupabaseBrowserClient() {
  return createBrowserClient(
    "https://kuehgabfpgvfcwyrjcji.supabase.co",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt1ZWhnYWJmcGd2ZmN3eXJqY2ppIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzUxOTg3NDQsImV4cCI6MjA5MDc3NDc0NH0.E9OwbP7N1ffER_c4PvAiqf5XIjAGFshLkqwuuqn7ZGs"
  )
}