import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { OwnerVenueTapListPage } from "@/owner/pages/OwnerVenueTapListPage";

const ownerVenueTapList = vi.fn();
const ownerCreateTapListItem = vi.fn();
const ownerPatchTapListItem = vi.fn();
const ownerDeactivateTapListItem = vi.fn();

vi.mock("@/shared/lib/api", () => ({
  ownerVenueTapList: (id: string) => ownerVenueTapList(id),
  ownerCreateTapListItem: (id: string, body: unknown) =>
    ownerCreateTapListItem(id, body),
  ownerPatchTapListItem: (id: string, itemId: string, body: unknown) =>
    ownerPatchTapListItem(id, itemId, body),
  ownerDeactivateTapListItem: (id: string, itemId: string) =>
    ownerDeactivateTapListItem(id, itemId),
  formatApiError: (err: unknown) =>
    err && typeof err === "object" && "message" in err
      ? String((err as { message: string }).message)
      : String(err),
  isApiRequestError: (err: unknown) =>
    Boolean(err && typeof err === "object" && "code" in err),
}));

function sampleItem() {
  return {
    id: "tap-1",
    drink_name: "Stone & Wood Pacific Ale",
    brewery_or_brand: "Stone & Wood",
    drink_type: "Pale ale",
    abv: "4.4%",
    price_text: "$12 schooner",
    availability: "permanent" as const,
    notes: null,
    active: true,
    sort_order: 0,
  };
}

function renderPage() {
  render(
    <MemoryRouter initialEntries={["/owner/venues/v-1/tap-list"]}>
      <Routes>
        <Route
          path="/owner/venues/:venueId/tap-list"
          element={<OwnerVenueTapListPage />}
        />
      </Routes>
    </MemoryRouter>,
  );
}

describe("OwnerVenueTapListPage", () => {
  beforeEach(() => {
    ownerVenueTapList.mockReset();
    ownerCreateTapListItem.mockReset();
    ownerPatchTapListItem.mockReset();
    ownerDeactivateTapListItem.mockReset();
  });

  it("loads existing drink items", async () => {
    ownerVenueTapList.mockResolvedValue({
      data: { venue_id: "v-1", tap_list: [sampleItem()] },
    });
    renderPage();
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Tap list & drinks" })).toBeInTheDocument();
    });
    expect(screen.getByText("Stone & Wood Pacific Ale")).toBeInTheDocument();
  });

  it("renders empty state", async () => {
    ownerVenueTapList.mockResolvedValue({
      data: { venue_id: "v-1", tap_list: [] },
    });
    renderPage();
    await waitFor(() => {
      expect(screen.getByText(/No drinks listed yet/i)).toBeInTheDocument();
    });
  });

  it("validates drink name before create", async () => {
    ownerVenueTapList.mockResolvedValue({
      data: { venue_id: "v-1", tap_list: [] },
    });
    renderPage();
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Add drink" })).toBeInTheDocument();
    });
    await userEvent.click(screen.getByRole("button", { name: "Add drink" }));
    await userEvent.click(screen.getByRole("button", { name: "Save drink" }));
    expect(
      await screen.findByText(/Drink name must be at least 2 characters/i),
    ).toBeInTheDocument();
    expect(ownerCreateTapListItem).not.toHaveBeenCalled();
  });

  it("sends POST payload on create", async () => {
    ownerVenueTapList.mockResolvedValue({
      data: { venue_id: "v-1", tap_list: [] },
    });
    ownerCreateTapListItem.mockResolvedValue({
      data: {
        venue_id: "v-1",
        tap_item: sampleItem(),
        message: "Drink list saved. These updates are now reflected on your listing.",
      },
    });
    renderPage();
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Add drink" })).toBeInTheDocument();
    });
    await userEvent.click(screen.getByRole("button", { name: "Add drink" }));
    await userEvent.type(screen.getByLabelText("Drink name"), "Guinness");
    await userEvent.click(screen.getByRole("button", { name: "Save drink" }));
    await waitFor(() => {
      expect(ownerCreateTapListItem).toHaveBeenCalledWith(
        "v-1",
        expect.objectContaining({ drink_name: "Guinness" }),
      );
    });
    expect(
      screen.getByText(/Drink list saved. These updates are now reflected on your listing./i),
    ).toBeInTheDocument();
  });

  it("sends PATCH payload on edit", async () => {
    ownerVenueTapList.mockResolvedValue({
      data: { venue_id: "v-1", tap_list: [sampleItem()] },
    });
    ownerPatchTapListItem.mockResolvedValue({
      data: {
        venue_id: "v-1",
        tap_item: { ...sampleItem(), price_text: "$14 pint" },
        message: "Drink list saved. These updates are now reflected on your listing.",
      },
    });
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("Stone & Wood Pacific Ale")).toBeInTheDocument();
    });
    await userEvent.click(screen.getByRole("button", { name: "Edit" }));
    const priceField = screen.getByLabelText("Price");
    await userEvent.clear(priceField);
    await userEvent.type(priceField, "$14 pint");
    await userEvent.click(screen.getByRole("button", { name: "Save drink" }));
    await waitFor(() => {
      expect(ownerPatchTapListItem).toHaveBeenCalledWith(
        "v-1",
        "tap-1",
        expect.objectContaining({ price_text: "$14 pint" }),
      );
    });
  });

  it("deactivates a drink item", async () => {
    ownerVenueTapList.mockResolvedValue({
      data: { venue_id: "v-1", tap_list: [sampleItem()] },
    });
    ownerDeactivateTapListItem.mockResolvedValue({
      data: {
        venue_id: "v-1",
        tap_item: { ...sampleItem(), active: false },
        message: "Drink list saved. These updates are now reflected on your listing.",
      },
    });
    renderPage();
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Deactivate" })).toBeInTheDocument();
    });
    await userEvent.click(screen.getByRole("button", { name: "Deactivate" }));
    expect(ownerDeactivateTapListItem).toHaveBeenCalledWith("v-1", "tap-1");
  });

  it("shows missing capability error copy", async () => {
    ownerVenueTapList.mockRejectedValue({
      code: "forbidden",
      message: "Direct listing edits are not enabled for your account.",
    });
    renderPage();
    expect(
      await screen.findByText(/Direct listing edits are not enabled for your account/i),
    ).toBeInTheDocument();
  });
});
