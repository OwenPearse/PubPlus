import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { OwnerVenueMealSpecialsPage } from "@/owner/pages/OwnerVenueMealSpecialsPage";

const ownerVenueMealSpecials = vi.fn();
const ownerCreateMealSpecial = vi.fn();
const ownerPatchMealSpecial = vi.fn();
const ownerDeactivateMealSpecial = vi.fn();

vi.mock("@/shared/lib/api", () => ({
  ownerVenueMealSpecials: (id: string) => ownerVenueMealSpecials(id),
  ownerCreateMealSpecial: (id: string, body: unknown) =>
    ownerCreateMealSpecial(id, body),
  ownerPatchMealSpecial: (id: string, specialId: string, body: unknown) =>
    ownerPatchMealSpecial(id, specialId, body),
  ownerDeactivateMealSpecial: (id: string, specialId: string) =>
    ownerDeactivateMealSpecial(id, specialId),
  formatApiError: (err: unknown) =>
    err && typeof err === "object" && "message" in err
      ? String((err as { message: string }).message)
      : String(err),
  isApiRequestError: (err: unknown) =>
    Boolean(err && typeof err === "object" && "code" in err),
}));

function sampleSpecial() {
  return {
    id: "sp-1",
    title: "Thursday Parma Night",
    description: "$20 parmas every Thursday.",
    days_available: [4],
    start_time: "17:00",
    end_time: "21:00",
    price_text: "$20",
    conditions: "Dine-in only",
    active: true,
    sort_order: 0,
  };
}

function renderPage() {
  render(
    <MemoryRouter initialEntries={["/owner/venues/v-1/meal-specials"]}>
      <Routes>
        <Route
          path="/owner/venues/:venueId/meal-specials"
          element={<OwnerVenueMealSpecialsPage />}
        />
      </Routes>
    </MemoryRouter>,
  );
}

describe("OwnerVenueMealSpecialsPage", () => {
  beforeEach(() => {
    ownerVenueMealSpecials.mockReset();
    ownerCreateMealSpecial.mockReset();
    ownerPatchMealSpecial.mockReset();
    ownerDeactivateMealSpecial.mockReset();
  });

  it("loads existing specials", async () => {
    ownerVenueMealSpecials.mockResolvedValue({
      data: { venue_id: "v-1", meal_specials: [sampleSpecial()] },
    });
    renderPage();
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Meal specials" })).toBeInTheDocument();
    });
    expect(screen.getByText("Thursday Parma Night")).toBeInTheDocument();
  });

  it("renders empty state", async () => {
    ownerVenueMealSpecials.mockResolvedValue({
      data: { venue_id: "v-1", meal_specials: [] },
    });
    renderPage();
    await waitFor(() => {
      expect(screen.getByText(/No meal specials yet/i)).toBeInTheDocument();
    });
  });

  it("validates title before create", async () => {
    ownerVenueMealSpecials.mockResolvedValue({
      data: { venue_id: "v-1", meal_specials: [] },
    });
    renderPage();
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Add special" })).toBeInTheDocument();
    });
    await userEvent.click(screen.getByRole("button", { name: "Add special" }));
    await userEvent.click(screen.getByRole("button", { name: "Save special" }));
    expect(
      await screen.findByText(/Special name must be at least 2 characters/i),
    ).toBeInTheDocument();
    expect(ownerCreateMealSpecial).not.toHaveBeenCalled();
  });

  it("validates time pair", async () => {
    ownerVenueMealSpecials.mockResolvedValue({
      data: { venue_id: "v-1", meal_specials: [] },
    });
    renderPage();
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Add special" })).toBeInTheDocument();
    });
    await userEvent.click(screen.getByRole("button", { name: "Add special" }));
    await userEvent.type(screen.getByLabelText("Special name"), "Steak night");
    await userEvent.type(screen.getByLabelText("Start time"), "17:00");
    await userEvent.click(screen.getByRole("button", { name: "Save special" }));
    expect(
      await screen.findByText(/Start and end time must both be set/i),
    ).toBeInTheDocument();
  });

  it("sends POST payload on create", async () => {
    ownerVenueMealSpecials.mockResolvedValue({
      data: { venue_id: "v-1", meal_specials: [] },
    });
    ownerCreateMealSpecial.mockResolvedValue({
      data: {
        venue_id: "v-1",
        meal_special: sampleSpecial(),
        message: "Special saved. These updates are now reflected on your listing.",
      },
    });
    renderPage();
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Add special" })).toBeInTheDocument();
    });
    await userEvent.click(screen.getByRole("button", { name: "Add special" }));
    await userEvent.type(screen.getByLabelText("Special name"), "Thursday Parma Night");
    await userEvent.type(screen.getByLabelText("Start time"), "17:00");
    await userEvent.type(screen.getByLabelText("End time"), "21:00");
    await userEvent.click(screen.getByLabelText("Thu"));
    await userEvent.click(screen.getByRole("button", { name: "Save special" }));
    await waitFor(() => {
      expect(ownerCreateMealSpecial).toHaveBeenCalledWith(
        "v-1",
        expect.objectContaining({
          title: "Thursday Parma Night",
          days_available: [4],
          start_time: "17:00",
          end_time: "21:00",
        }),
      );
    });
    expect(
      screen.getByText(/Special saved. These updates are now reflected on your listing./i),
    ).toBeInTheDocument();
  });

  it("sends PATCH payload on edit", async () => {
    ownerVenueMealSpecials.mockResolvedValue({
      data: { venue_id: "v-1", meal_specials: [sampleSpecial()] },
    });
    ownerPatchMealSpecial.mockResolvedValue({
      data: {
        venue_id: "v-1",
        meal_special: { ...sampleSpecial(), price_text: "$22" },
        message: "Special saved. These updates are now reflected on your listing.",
      },
    });
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("Thursday Parma Night")).toBeInTheDocument();
    });
    await userEvent.click(screen.getByRole("button", { name: "Edit" }));
    const priceField = screen.getByLabelText("Price");
    await userEvent.clear(priceField);
    await userEvent.type(priceField, "$22");
    await userEvent.click(screen.getByRole("button", { name: "Save special" }));
    await waitFor(() => {
      expect(ownerPatchMealSpecial).toHaveBeenCalledWith(
        "v-1",
        "sp-1",
        expect.objectContaining({ price_text: "$22" }),
      );
    });
  });

  it("deactivates a special", async () => {
    ownerVenueMealSpecials.mockResolvedValue({
      data: { venue_id: "v-1", meal_specials: [sampleSpecial()] },
    });
    ownerDeactivateMealSpecial.mockResolvedValue({
      data: {
        venue_id: "v-1",
        meal_special: { ...sampleSpecial(), active: false },
        message: "Special saved. These updates are now reflected on your listing.",
      },
    });
    renderPage();
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Deactivate" })).toBeInTheDocument();
    });
    await userEvent.click(screen.getByRole("button", { name: "Deactivate" }));
    await waitFor(() => {
      expect(ownerDeactivateMealSpecial).toHaveBeenCalledWith("v-1", "sp-1");
    });
  });

  it("shows missing capability error copy", async () => {
    ownerVenueMealSpecials.mockRejectedValue({
      code: "forbidden",
      message:
        "Direct listing edits are not enabled for your account. Contact support if you manage this venue.",
      status: 403,
    });
    renderPage();
    expect(
      await screen.findByText(/Direct listing edits are not enabled for your account/i),
    ).toBeInTheDocument();
  });
});
