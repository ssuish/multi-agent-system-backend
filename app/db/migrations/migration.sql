-- SQL script generated within Supabase for migration

-- public.profiles
CREATE TABLE IF NOT EXISTS public."profiles" (
  "id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  "clerk_user_id" text UNIQUE,
  "display_name" text,
  "created_at" timestamptz DEFAULT now(),
  "updated_at" timestamptz DEFAULT now()
);

-- public.conversations
CREATE TABLE IF NOT EXISTS public."conversations" (
  "id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  "user_id" uuid NOT NULL,
  "title" text,
  "created_at" timestamptz DEFAULT now(),
  "updated_at" timestamptz DEFAULT now(),
  "status" text DEFAULT 'active',
  "jd_text" text,
  "cv_reference" text,
  "cv_markdown" text
);

-- public.messages
CREATE TABLE IF NOT EXISTS public."messages" (
  "id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  "conversation_id" uuid NOT NULL,
  "role" text,
  "content" text,
  "created_at" timestamptz DEFAULT now()
);

-- Foreign keys
DO $$
BEGIN
  -- conversations.user_id -> profiles.id
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'conversations_user_id_fkey'
  ) THEN
    ALTER TABLE public."conversations"
    ADD CONSTRAINT "conversations_user_id_fkey"
    FOREIGN KEY ("user_id") REFERENCES public."profiles" ("id");
  END IF;

  -- messages.conversation_id -> conversations.id
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'messages_conversation_id_fkey'
  ) THEN
    ALTER TABLE public."messages"
    ADD CONSTRAINT "messages_conversation_id_fkey"
    FOREIGN KEY ("conversation_id") REFERENCES public."conversations" ("id") ON DELETE CASCADE;
  END IF;   
END $$;

-- Helpful indexes (only if they don't already exist)
DO $$
BEGIN
  -- conversations.user_id index
  IF NOT EXISTS (   
    SELECT 1 FROM pg_indexes WHERE schemaname='public' AND indexname='conversations_user_id_idx'
  ) THEN
    CREATE INDEX "conversations_user_id_idx" ON public."conversations" ("user_id");
  END IF;

  -- messages.conversation_id index
  IF NOT EXISTS (
    SELECT 1 FROM pg_indexes WHERE schemaname='public' AND indexname='messages_conversation_id_idx'
  ) THEN
    CREATE INDEX "messages_conversation_id_idx" ON public."messages" ("conversation_id");
  END IF;
END $$;