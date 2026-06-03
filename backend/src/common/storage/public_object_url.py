def public_storage_object_url(
    supabase_project_url: str, bucket: str, object_path: str
) -> str:
    """
    Public (anon) Supabase Storage URL for a bucket object.

    Pattern:
      {SUPABASE_URL}/storage/v1/object/public/{bucket}/{path}

    `object_path` is the key within the bucket (may include / segments).
    """
    base = supabase_project_url.rstrip("/")
    key = object_path.lstrip("/")
    b = bucket.strip().strip("/")
    return f"{base}/storage/v1/object/public/{b}/{key}"
