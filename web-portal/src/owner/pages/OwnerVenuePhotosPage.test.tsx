import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { OwnerVenuePhotosPage } from "@/owner/pages/OwnerVenuePhotosPage";
import { PHOTOS_PAGE_TITLE, PHOTOS_SUCCESS_MESSAGE } from "@/owner/lib/ownerVenuePhotosUi";

const ownerVenueMedia = vi.fn();
const ownerMediaUploadIntent = vi.fn();
const ownerCreateMedia = vi.fn();
const ownerPatchMedia = vi.fn();
const ownerDeactivateMedia = vi.fn();
const uploadFileToSignedUrl = vi.fn();

vi.mock("@/shared/lib/api", () => ({
  ownerVenueMedia: (venueId: string) => ownerVenueMedia(venueId),
  ownerMediaUploadIntent: (venueId: string, body: unknown) =>
    ownerMediaUploadIntent(venueId, body),
  ownerCreateMedia: (venueId: string, body: unknown) => ownerCreateMedia(venueId, body),
  ownerPatchMedia: (venueId: string, mediaId: string, body: unknown) =>
    ownerPatchMedia(venueId, mediaId, body),
  ownerDeactivateMedia: (venueId: string, mediaId: string) =>
    ownerDeactivateMedia(venueId, mediaId),
  uploadFileToSignedUrl: (...args: unknown[]) => uploadFileToSignedUrl(...args),
  formatApiError: (err: unknown) => String(err),
  isApiRequestError: (err: unknown) =>
    Boolean(err && typeof err === "object" && "code" in err),
}));

describe("OwnerVenuePhotosPage", () => {
  beforeEach(() => {
    ownerVenueMedia.mockReset();
    ownerMediaUploadIntent.mockReset();
    ownerCreateMedia.mockReset();
    ownerPatchMedia.mockReset();
    ownerDeactivateMedia.mockReset();
    uploadFileToSignedUrl.mockReset();
  });

  it("renders photos page and loads existing media", async () => {
    ownerVenueMedia.mockResolvedValue({
      data: {
        venue_id: "v-1",
        media: [
          {
            id: "m-1",
            purpose: "profile",
            media_kind: "image",
            url: "https://example.com/profile.jpg",
            storage_bucket: "venue-media",
            storage_path: "venues/v-1/profile/m-1.jpg",
            caption: null,
            alt_text: "Front bar",
            sort_order: 0,
            active: true,
          },
        ],
      },
    });

    render(
      <MemoryRouter initialEntries={["/owner/venues/v-1/photos"]}>
        <Routes>
          <Route path="/owner/venues/:venueId/photos" element={<OwnerVenuePhotosPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: PHOTOS_PAGE_TITLE })).toBeInTheDocument();
    });
    expect(screen.getAllByText("Profile photo").length).toBeGreaterThan(0);
    expect(screen.getByDisplayValue("Front bar")).toBeInTheDocument();
  });

  it("shows empty state when no media", async () => {
    ownerVenueMedia.mockResolvedValue({ data: { venue_id: "v-1", media: [] } });
    render(
      <MemoryRouter initialEntries={["/owner/venues/v-1/photos"]}>
        <Routes>
          <Route path="/owner/venues/:venueId/photos" element={<OwnerVenuePhotosPage />} />
        </Routes>
      </MemoryRouter>,
    );
    await waitFor(() => {
      expect(screen.getByText(/No photos yet/i)).toBeInTheDocument();
    });
  });

  it("validates file type client-side", async () => {
    ownerVenueMedia.mockResolvedValue({ data: { venue_id: "v-1", media: [] } });
    render(
      <MemoryRouter initialEntries={["/owner/venues/v-1/photos"]}>
        <Routes>
          <Route path="/owner/venues/:venueId/photos" element={<OwnerVenuePhotosPage />} />
        </Routes>
      </MemoryRouter>,
    );
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Profile photo" })).toBeInTheDocument();
    });

    const input = document.querySelector(
      'section input[type="file"]',
    ) as HTMLInputElement;
    const badFile = new File(["x"], "bad.gif", { type: "image/gif" });
    fireEvent.change(input, { target: { files: [badFile] } });

    await waitFor(() => {
      expect(screen.getByText(/Please choose a JPEG/i)).toBeInTheDocument();
    });
    expect(ownerMediaUploadIntent).not.toHaveBeenCalled();
  });

  it("runs upload intent, signed upload, and metadata create", async () => {
    ownerVenueMedia.mockResolvedValue({ data: { venue_id: "v-1", media: [] } });
    ownerMediaUploadIntent.mockResolvedValue({
      data: {
        media_id: "m-new",
        storage_bucket: "venue-media",
        storage_path: "venues/v-1/gallery/m-new.jpg",
        signed_upload_url: "https://signed.example/upload",
        expires_in_seconds: 600,
      },
    });
    ownerCreateMedia.mockResolvedValue({
      data: {
        venue_id: "v-1",
        media_item: {
          id: "m-new",
          purpose: "gallery",
          media_kind: "image",
          url: "https://example.com/m-new.jpg",
          storage_bucket: "venue-media",
          storage_path: "venues/v-1/gallery/m-new.jpg",
          caption: null,
          alt_text: null,
          sort_order: 0,
          active: true,
        },
        message: PHOTOS_SUCCESS_MESSAGE,
      },
    });
    uploadFileToSignedUrl.mockResolvedValue(undefined);

    render(
      <MemoryRouter initialEntries={["/owner/venues/v-1/photos"]}>
        <Routes>
          <Route path="/owner/venues/:venueId/photos" element={<OwnerVenuePhotosPage />} />
        </Routes>
      </MemoryRouter>,
    );
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Gallery photos" })).toBeInTheDocument();
    });

    const inputs = document.querySelectorAll('section input[type="file"]');
    const galleryInput = inputs[1] as HTMLInputElement;
    const file = new File(["bytes"], "pub.jpg", { type: "image/jpeg" });
    Object.defineProperty(file, "size", { value: 5000 });
    await userEvent.upload(galleryInput, file);

    await waitFor(() => {
      expect(ownerMediaUploadIntent).toHaveBeenCalled();
      expect(uploadFileToSignedUrl).toHaveBeenCalledWith(
        "https://signed.example/upload",
        file,
        "image/jpeg",
      );
      expect(ownerCreateMedia).toHaveBeenCalled();
    });
  });

  it("shows missing capability copy", async () => {
    ownerVenueMedia.mockRejectedValue({
      code: "forbidden",
      message: "Direct listing edits are not enabled for your account.",
      status: 403,
    });
    render(
      <MemoryRouter initialEntries={["/owner/venues/v-1/photos"]}>
        <Routes>
          <Route path="/owner/venues/:venueId/photos" element={<OwnerVenuePhotosPage />} />
        </Routes>
      </MemoryRouter>,
    );
    await waitFor(() => {
      expect(screen.getByText(/Direct listing edits are not enabled/i)).toBeInTheDocument();
    });
  });
});
