/*
  # Initial Schema for Waste2Wonder Platform

  1. New Tables
    - `profiles` - User profile information
    - `waste_items` - Uploaded waste items
    - `suggestions` - AI-generated suggestions
    - `products` - Marketplace products
    - `community_posts` - Community posts
    - `post_likes` - Post likes tracking
    - `post_comments` - Post comments
    - `post_bookmarks` - Post bookmarks

  2. Security
    - Enable RLS on all tables
    - Add policies for authenticated users
    - Secure data access based on user ownership
*/

-- Create profiles table
CREATE TABLE IF NOT EXISTS profiles (
  id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email text UNIQUE NOT NULL,
  name text NOT NULL,
  role text DEFAULT 'user' CHECK (role IN ('user', 'creator', 'admin')),
  avatar text,
  join_date timestamptz DEFAULT now(),
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Create waste_items table
CREATE TABLE IF NOT EXISTS waste_items (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
  type text NOT NULL,
  description text NOT NULL,
  image text,
  category text NOT NULL,
  condition text DEFAULT 'Good',
  quantity integer DEFAULT 1,
  location text,
  dimensions text,
  weight text,
  color text,
  material text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Create suggestions table
CREATE TABLE IF NOT EXISTS suggestions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  waste_id uuid REFERENCES waste_items(id) ON DELETE CASCADE NOT NULL,
  title text NOT NULL,
  description text NOT NULL,
  tools text[] DEFAULT '{}',
  materials text[] DEFAULT '{}',
  steps text[] DEFAULT '{}',
  difficulty text DEFAULT 'Easy' CHECK (difficulty IN ('Easy', 'Medium', 'Hard')),
  time_required text,
  estimated_cost text,
  safety_tips text[] DEFAULT '{}',
  video_search_query text,
  eco_impact jsonb DEFAULT '{}',
  created_at timestamptz DEFAULT now()
);

-- Create products table
CREATE TABLE IF NOT EXISTS products (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
  title text NOT NULL,
  description text NOT NULL,
  price decimal(10,2) DEFAULT 0,
  image text,
  category text NOT NULL,
  condition text DEFAULT 'New' CHECK (condition IN ('New', 'Like New', 'Good', 'Fair')),
  type text DEFAULT 'Sale' CHECK (type IN ('Sale', 'Donation')),
  dimensions text,
  weight text,
  color text,
  material text,
  location text,
  tags text,
  shipping_info text,
  return_policy text,
  seller_info jsonb DEFAULT '{}',
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Create community_posts table
CREATE TABLE IF NOT EXISTS community_posts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
  title text NOT NULL,
  description text NOT NULL,
  image text,
  category text NOT NULL,
  materials text,
  time_spent text,
  difficulty text DEFAULT 'Easy' CHECK (difficulty IN ('Easy', 'Medium', 'Hard')),
  tags text[] DEFAULT '{}',
  tips text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Create post_likes table
CREATE TABLE IF NOT EXISTS post_likes (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  post_id uuid REFERENCES community_posts(id) ON DELETE CASCADE NOT NULL,
  user_id uuid REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
  created_at timestamptz DEFAULT now(),
  UNIQUE(post_id, user_id)
);

-- Create post_comments table
CREATE TABLE IF NOT EXISTS post_comments (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  post_id uuid REFERENCES community_posts(id) ON DELETE CASCADE NOT NULL,
  user_id uuid REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
  content text NOT NULL,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Create post_bookmarks table
CREATE TABLE IF NOT EXISTS post_bookmarks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  post_id uuid REFERENCES community_posts(id) ON DELETE CASCADE NOT NULL,
  user_id uuid REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
  created_at timestamptz DEFAULT now(),
  UNIQUE(post_id, user_id)
);

-- Enable Row Level Security
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE waste_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE suggestions ENABLE ROW LEVEL SECURITY;
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE community_posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE post_likes ENABLE ROW LEVEL SECURITY;
ALTER TABLE post_comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE post_bookmarks ENABLE ROW LEVEL SECURITY;

-- Profiles policies
CREATE POLICY "Users can read all profiles"
  ON profiles
  FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Users can update own profile"
  ON profiles
  FOR UPDATE
  TO authenticated
  USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile"
  ON profiles
  FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = id);

-- Waste items policies
CREATE POLICY "Users can read all waste items"
  ON waste_items
  FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Users can insert own waste items"
  ON waste_items
  FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own waste items"
  ON waste_items
  FOR UPDATE
  TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own waste items"
  ON waste_items
  FOR DELETE
  TO authenticated
  USING (auth.uid() = user_id);

-- Suggestions policies
CREATE POLICY "Users can read all suggestions"
  ON suggestions
  FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Users can insert suggestions for own waste items"
  ON suggestions
  FOR INSERT
  TO authenticated
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM waste_items 
      WHERE id = waste_id AND user_id = auth.uid()
    )
  );

-- Products policies
CREATE POLICY "Users can read all products"
  ON products
  FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Users can insert own products"
  ON products
  FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own products"
  ON products
  FOR UPDATE
  TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own products"
  ON products
  FOR DELETE
  TO authenticated
  USING (auth.uid() = user_id);

-- Community posts policies
CREATE POLICY "Users can read all community posts"
  ON community_posts
  FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Users can insert own community posts"
  ON community_posts
  FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own community posts"
  ON community_posts
  FOR UPDATE
  TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own community posts"
  ON community_posts
  FOR DELETE
  TO authenticated
  USING (auth.uid() = user_id);

-- Post likes policies
CREATE POLICY "Users can read all post likes"
  ON post_likes
  FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Users can insert own post likes"
  ON post_likes
  FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own post likes"
  ON post_likes
  FOR DELETE
  TO authenticated
  USING (auth.uid() = user_id);

-- Post comments policies
CREATE POLICY "Users can read all post comments"
  ON post_comments
  FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Users can insert own post comments"
  ON post_comments
  FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own post comments"
  ON post_comments
  FOR UPDATE
  TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own post comments"
  ON post_comments
  FOR DELETE
  TO authenticated
  USING (auth.uid() = user_id);

-- Post bookmarks policies
CREATE POLICY "Users can read own post bookmarks"
  ON post_bookmarks
  FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own post bookmarks"
  ON post_bookmarks
  FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own post bookmarks"
  ON post_bookmarks
  FOR DELETE
  TO authenticated
  USING (auth.uid() = user_id);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_waste_items_user_id ON waste_items(user_id);
CREATE INDEX IF NOT EXISTS idx_waste_items_category ON waste_items(category);
CREATE INDEX IF NOT EXISTS idx_suggestions_waste_id ON suggestions(waste_id);
CREATE INDEX IF NOT EXISTS idx_products_user_id ON products(user_id);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_type ON products(type);
CREATE INDEX IF NOT EXISTS idx_community_posts_user_id ON community_posts(user_id);
CREATE INDEX IF NOT EXISTS idx_community_posts_category ON community_posts(category);
CREATE INDEX IF NOT EXISTS idx_post_likes_post_id ON post_likes(post_id);
CREATE INDEX IF NOT EXISTS idx_post_likes_user_id ON post_likes(user_id);
CREATE INDEX IF NOT EXISTS idx_post_comments_post_id ON post_comments(post_id);
CREATE INDEX IF NOT EXISTS idx_post_bookmarks_post_id ON post_bookmarks(post_id);
CREATE INDEX IF NOT EXISTS idx_post_bookmarks_user_id ON post_bookmarks(user_id);

-- Create function to handle user profile creation
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS trigger AS $$
BEGIN
  INSERT INTO profiles (id, email, name, avatar)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'name', split_part(NEW.email, '@', 1)),
    COALESCE(NEW.raw_user_meta_data->>'avatar', 'https://api.dicebear.com/7.x/avataaars/svg?seed=' || NEW.email)
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create trigger for new user profile creation
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION handle_new_user();