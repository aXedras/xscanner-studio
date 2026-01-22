-- Storage bucket for extraction images
-- This migration creates a bucket for storing uploaded barcode/bullion images

-- Create storage bucket for extraction images
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'extractions',
    'extractions',
    false,  -- Private bucket, requires authentication
    52428800,  -- 50MB max file size
    ARRAY['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
);

-- Allow authenticated users to read extraction images from private bucket.
CREATE POLICY "authenticated_read_extraction_images"
ON storage.objects
FOR SELECT
TO authenticated
USING (bucket_id = 'extractions');
