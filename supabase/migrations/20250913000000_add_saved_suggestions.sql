/*
  # Add Saved Suggestions Table

  1. New Table
    - `saved_suggestions` - User-saved AI suggestions
    - References profiles table for user_id
    - Includes all suggestion data
    - Timestamps for tracking

  2. Security
    - Enable RLS for data protection
    - Add policies for user access
*/

-- Create saved_suggestions table
CREATE TABLE IF NOT EXISTS saved_suggestions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
  title text NOT NULL,
  description text NOT NULL,
  difficulty text DEFAULT 'Easy' CHECK (difficulty IN ('Easy', 'Medium', 'Hard')),
  time_required text,
  tools text[] DEFAULT '{}',
  materials text[] DEFAULT '{}',
  estimated_cost text,
  steps text[] DEFAULT '{}',
  safety_tips text[] DEFAULT '{}',
  eco_impact jsonb DEFAULT '{}',
  video_search_query text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Enable Row Level Security
ALTER TABLE saved_suggestions ENABLE ROW LEVEL SECURITY;

-- Create policy for users to view their own saved suggestions
CREATE POLICY "Users can view own saved suggestions"
  ON saved_suggestions
  FOR SELECT
  USING (auth.uid() = user_id);

-- Create policy for users to insert their own saved suggestions
CREATE POLICY "Users can insert own saved suggestions"
  ON saved_suggestions
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Create policy for users to update their own saved suggestions
CREATE POLICY "Users can update own saved suggestions"
  ON saved_suggestions
  FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- Create policy for users to delete their own saved suggestions
CREATE POLICY "Users can delete own saved suggestions"
  ON saved_suggestions
  FOR DELETE
  USING (auth.uid() = user_id);