import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
  formatPhotoPurpose,
  PHOTOS_ALLOWED_TYPES,
  PHOTOS_MAX_BYTES,
  PHOTOS_MISSING_CAPABILITY_MESSAGE,
  PHOTOS_PAGE_HELPER,
  PHOTOS_PAGE_TITLE,
  PHOTOS_SUCCESS_MESSAGE,
  PHOTOS_UPLOAD_LABEL,
} from "@/owner/lib/ownerVenuePhotosUi";
import { ErrorBanner } from "@/shared/components/ErrorBanner";
import {
  formatApiError,
  isApiRequestError,
  ownerCreateMedia,
  ownerDeactivateMedia,
  ownerMediaUploadIntent,
  ownerPatchMedia,
  ownerVenueMedia,
  uploadFileToSignedUrl,
  type OwnerMediaItem,
  type OwnerMediaPurpose,
} from "@/shared/lib/api";

function SuccessBanner({ children }: { children: string }) {
  return (
    <div className="rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-900">
      {children}
    </div>
  );
}

function ownerPhotosCapabilityMessage(err: unknown): string | null {
  if (!isApiRequestError(err) || err.code !== "forbidden") return null;
  const msg = err.message.toLowerCase();
  if (msg.includes("direct listing edits")) {
    return PHOTOS_MISSING_CAPABILITY_MESSAGE;
  }
  return null;
}

function validatePhotoFile(file: File): string | null {
  if (!PHOTOS_ALLOWED_TYPES.includes(file.type as (typeof PHOTOS_ALLOWED_TYPES)[number])) {
    return "Please choose a JPEG, PNG, or WebP image.";
  }
  if (file.size > PHOTOS_MAX_BYTES) {
    return "Image must be 5 MB or smaller.";
  }
  return null;
}

function MediaCard({
  item,
  venueId,
  onUpdated,
  onRemoved,
}: {
  item: OwnerMediaItem;
  venueId: string;
  onUpdated: () => void;
  onRemoved: () => void;
}) {
  const [caption, setCaption] = useState(item.caption ?? "");
  const [altText, setAltText] = useState(item.alt_text ?? "");
  const [sortOrder, setSortOrder] = useState(String(item.sort_order));
  const [saving, setSaving] = useState(false);
  const [removing, setRemoving] = useState(false);
  const [error, setError] = useState("");

  const saveMetadata = async () => {
    setSaving(true);
    setError("");
    try {
      const parsedSort = Number.parseInt(sortOrder, 10);
      await ownerPatchMedia(venueId, item.id, {
        caption: caption.trim() || null,
        alt_text: altText.trim() || null,
        sort_order: Number.isFinite(parsedSort) ? parsedSort : item.sort_order,
      });
      onUpdated();
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setSaving(false);
    }
  };

  const removePhoto = async () => {
    setRemoving(true);
    setError("");
    try {
      await ownerDeactivateMedia(venueId, item.id);
      onRemoved();
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setRemoving(false);
    }
  };

  return (
    <li className="rounded-lg border border-slate-200 bg-white p-4">
      <div className="flex flex-col gap-4 sm:flex-row">
        <img
          src={item.url}
          alt={item.alt_text ?? formatPhotoPurpose(item.purpose)}
          className="h-32 w-full shrink-0 rounded object-cover sm:h-28 sm:w-40"
        />
        <div className="min-w-0 flex-1 space-y-3">
          <p className="text-sm font-medium text-slate-900">
            {formatPhotoPurpose(item.purpose)}
          </p>
          <div>
            <label className="block text-xs font-medium text-slate-700">Caption</label>
            <input
              type="text"
              maxLength={200}
              className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm"
              value={caption}
              onChange={(e) => setCaption(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-700">Alt text</label>
            <input
              type="text"
              maxLength={200}
              className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm"
              value={altText}
              onChange={(e) => setAltText(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-700">Sort order</label>
            <input
              type="number"
              min={0}
              max={999}
              className="mt-1 w-24 rounded border border-slate-300 px-3 py-2 text-sm"
              value={sortOrder}
              onChange={(e) => setSortOrder(e.target.value)}
            />
          </div>
          {error ? <p className="text-sm text-red-700">{error}</p> : null}
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              className="rounded bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
              disabled={saving}
              onClick={() => void saveMetadata()}
            >
              {saving ? "Saving…" : "Save details"}
            </button>
            <button
              type="button"
              className="rounded border border-red-200 px-3 py-2 text-sm text-red-700 hover:bg-red-50 disabled:opacity-50"
              disabled={removing}
              onClick={() => void removePhoto()}
            >
              {removing ? "Removing…" : "Remove"}
            </button>
          </div>
        </div>
      </div>
    </li>
  );
}

export function OwnerVenuePhotosPage() {
  const { venueId } = useParams<{ venueId: string }>();
  const [media, setMedia] = useState<OwnerMediaItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [uploadingPurpose, setUploadingPurpose] = useState<OwnerMediaPurpose | null>(null);
  const profileInputRef = useRef<HTMLInputElement>(null);
  const galleryInputRef = useRef<HTMLInputElement>(null);

  const loadMedia = useCallback(async () => {
    if (!venueId) return;
    setLoading(true);
    setError("");
    try {
      const { data } = await ownerVenueMedia(venueId);
      setMedia(data.media);
    } catch (err) {
      const cap = ownerPhotosCapabilityMessage(err);
      setError(cap ?? formatApiError(err));
      setMedia([]);
    } finally {
      setLoading(false);
    }
  }, [venueId]);

  useEffect(() => {
    void loadMedia();
  }, [loadMedia]);

  const handleFileSelected = async (purpose: OwnerMediaPurpose, file: File) => {
    if (!venueId) return;
    const validationError = validatePhotoFile(file);
    if (validationError) {
      setError(validationError);
      return;
    }

    setUploadingPurpose(purpose);
    setError("");
    setSuccess("");
    try {
      const contentType = file.type as "image/jpeg" | "image/png" | "image/webp";
      const { data: intent } = await ownerMediaUploadIntent(venueId, {
        purpose,
        file_name: file.name,
        content_type: contentType,
        file_size_bytes: file.size,
      });

      await uploadFileToSignedUrl(intent.signed_upload_url, file, contentType);

      await ownerCreateMedia(venueId, {
        media_id: intent.media_id,
        purpose,
        storage_bucket: intent.storage_bucket,
        storage_path: intent.storage_path,
        alt_text: null,
        caption: null,
      });

      setSuccess(PHOTOS_SUCCESS_MESSAGE);
      await loadMedia();
    } catch (err) {
      const cap = ownerPhotosCapabilityMessage(err);
      setError(cap ?? formatApiError(err));
    } finally {
      setUploadingPurpose(null);
    }
  };

  if (!venueId) {
    return (
      <div className="max-w-lg">
        <ErrorBanner message="Venue ID is missing." />
      </div>
    );
  }

  const profilePhoto = media.find((m) => m.purpose === "profile");
  const galleryPhotos = media.filter((m) => m.purpose === "gallery");

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <Link
          to={`/owner/venues/${venueId}`}
          className="text-sm font-medium text-slate-600 underline"
        >
          Back to venue hub
        </Link>
        <h1 className="mt-2 text-2xl font-bold text-slate-900">{PHOTOS_PAGE_TITLE}</h1>
        <p className="mt-2 text-sm text-slate-600">{PHOTOS_PAGE_HELPER}</p>
      </div>

      {error ? <ErrorBanner message={error} /> : null}
      {success ? <SuccessBanner>{success}</SuccessBanner> : null}

      <section className="space-y-3 rounded-lg border border-slate-200 bg-white p-4">
        <h2 className="font-medium text-slate-900">Profile photo</h2>
        <p className="text-sm text-slate-600">
          {profilePhoto
            ? "Replace your profile photo — the previous one will be deactivated."
            : "Add a main photo for your listing."}
        </p>
        <input
          ref={profileInputRef}
          type="file"
          accept={PHOTOS_ALLOWED_TYPES.join(",")}
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) void handleFileSelected("profile", file);
            e.target.value = "";
          }}
        />
        <button
          type="button"
          className="rounded bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
          disabled={uploadingPurpose !== null}
          onClick={() => profileInputRef.current?.click()}
        >
          {uploadingPurpose === "profile" ? "Uploading…" : PHOTOS_UPLOAD_LABEL}
        </button>
      </section>

      <section className="space-y-3 rounded-lg border border-slate-200 bg-white p-4">
        <h2 className="font-medium text-slate-900">Gallery photos</h2>
        <input
          ref={galleryInputRef}
          type="file"
          accept={PHOTOS_ALLOWED_TYPES.join(",")}
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) void handleFileSelected("gallery", file);
            e.target.value = "";
          }}
        />
        <button
          type="button"
          className="rounded bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
          disabled={uploadingPurpose !== null}
          onClick={() => galleryInputRef.current?.click()}
        >
          {uploadingPurpose === "gallery" ? "Uploading…" : PHOTOS_UPLOAD_LABEL}
        </button>
      </section>

      {loading ? (
        <p className="text-sm text-slate-600">Loading photos…</p>
      ) : media.length === 0 ? (
        <p className="text-sm text-slate-600">No photos yet. Upload a profile or gallery photo.</p>
      ) : (
        <ul className="space-y-4">
          {profilePhoto ? (
            <MediaCard
              key={profilePhoto.id}
              item={profilePhoto}
              venueId={venueId}
              onUpdated={() => {
                setSuccess(PHOTOS_SUCCESS_MESSAGE);
                void loadMedia();
              }}
              onRemoved={() => {
                setSuccess(PHOTOS_SUCCESS_MESSAGE);
                void loadMedia();
              }}
            />
          ) : null}
          {galleryPhotos.map((item) => (
            <MediaCard
              key={item.id}
              item={item}
              venueId={venueId}
              onUpdated={() => {
                setSuccess(PHOTOS_SUCCESS_MESSAGE);
                void loadMedia();
              }}
              onRemoved={() => {
                setSuccess(PHOTOS_SUCCESS_MESSAGE);
                void loadMedia();
              }}
            />
          ))}
        </ul>
      )}
    </div>
  );
}
