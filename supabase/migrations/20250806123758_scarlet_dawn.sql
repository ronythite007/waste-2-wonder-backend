/*
  # Fix User Profile Creation Trigger

  1. Database Function
    - Creates `handle_new_user()` function to automatically create profiles
    - Extracts user metadata (name, role) from signup data
    - Handles profile creation with proper error handling

  2. Trigger Setup
    - Creates trigger on `auth.users` table
    - Fires after new user insertion
    - Automatically creates corresponding profile entry

  3. Security
    - Function runs with security definer privileges
    - Maintains existing RLS policies
    - Ensures data consistency between auth and profiles tables
*/

-- Drop existing trigger and function if they exist
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
DROP FUNCTION IF EXISTS public.handle_new_user();

-- Create function to handle new user profile creation
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
BEGIN
  INSERT INTO public.profiles (id, email, name, role)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'name', ''),
    COALESCE(NEW.raw_user_meta_data->>'role', 'user')
  );
  RETURN NEW;
EXCEPTION
  WHEN OTHERS THEN
    -- Log the error but don't fail the user creation
    RAISE WARNING 'Failed to create profile for user %: %', NEW.id, SQLERRM;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create trigger that fires after user creation
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();