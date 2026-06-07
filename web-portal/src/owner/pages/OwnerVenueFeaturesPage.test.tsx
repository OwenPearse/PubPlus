import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { OwnerVenueFeaturesPage } from "@/owner/pages/OwnerVenueFeaturesPage";

const ownerVenueFeatures = vi.fn();
const ownerPatchVenueFeatures = vi.fn();

vi.mock("@/shared/lib/api", () => ({
  ownerVenueFeatures: (id: string) => ownerVenueFeatures(id),
  ownerPatchVenueFeatures: (id: string, body: unknown) =>
    ownerPatchVenueFeatures(id, body),
  formatApiError: (err: unknown) =>
    err && typeof err === "object" && "message" in err
      ? String((err as { message: string }).message)
      : String(err),
  isApiRequestError: (err: unknown) =>
    Boolean(err && typeof err === "object" && "code" in err),
}));

function sampleFeatures() {
  return [
    {
      attribute_definition_id: "attr-beer",
      stable_key: "beer_garden",
      label: "Beer garden",
      value_shape: "boolean" as const,
      group: "spaces",
      value: false,
    },
    {
      attribute_definition_id: "attr-dog",
      stable_key: "dog_friendly",
      label: "Dog friendly",
      value_shape: "boolean" as const,
      group: "pets",
      value: false,
    },
    {
      attribute_definition_id: "attr-vegan",
      stable_key: "vegan_options",
      label: "Vegan options",
      value_shape: "boolean" as const,
      group: "food",
      value: true,
    },
  ];
}

function renderPage() {
  render(
    <MemoryRouter initialEntries={["/owner/venues/v-1/features"]}>
      <Routes>
        <Route path="/owner/venues/:venueId/features" element={<OwnerVenueFeaturesPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("OwnerVenueFeaturesPage", () => {
  beforeEach(() => {
    ownerVenueFeatures.mockReset();
    ownerPatchVenueFeatures.mockReset();
  });

  it("loads feature definitions and current values", async () => {
    ownerVenueFeatures.mockResolvedValue({ data: { venue_id: "v-1", features: sampleFeatures() } });
    renderPage();
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Venue features" })).toBeInTheDocument();
    });
    expect(screen.getByLabelText("Beer garden")).not.toBeChecked();
    expect(screen.getByLabelText("Vegan options")).toBeChecked();
  });

  it("toggles values and saves PATCH payload", async () => {
    ownerVenueFeatures.mockResolvedValue({ data: { venue_id: "v-1", features: sampleFeatures() } });
    ownerPatchVenueFeatures.mockResolvedValue({
      data: {
        venue_id: "v-1",
        features: sampleFeatures().map((f) =>
          f.stable_key === "beer_garden" ? { ...f, value: true } : f,
        ),
        message: "Features saved. These updates are now reflected on your listing.",
      },
    });
    renderPage();
    await waitFor(() => {
      expect(screen.getByLabelText("Beer garden")).toBeInTheDocument();
    });
    await userEvent.click(screen.getByLabelText("Beer garden"));
    await userEvent.click(screen.getByRole("button", { name: "Save features" }));
    await waitFor(() => {
      expect(ownerPatchVenueFeatures).toHaveBeenCalledWith("v-1", {
        features: expect.arrayContaining([
          { attribute_definition_id: "attr-beer", value_boolean: true },
        ]),
      });
    });
    expect(
      screen.getByText(/Features saved. These updates are now reflected on your listing./i),
    ).toBeInTheDocument();
  });

  it("handles missing capability", async () => {
    ownerVenueFeatures.mockRejectedValue({
      code: "forbidden",
      message: "Direct listing edits are not enabled for your account.",
      status: 403,
    });
    renderPage();
    await waitFor(() => {
      expect(
        screen.getByText("Your account is not set up to edit this listing yet."),
      ).toBeInTheDocument();
    });
  });

  it("shows load error state", async () => {
    ownerVenueFeatures.mockRejectedValue(new Error("Failed to load features"));
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("Failed to load features")).toBeInTheDocument();
    });
  });
});
