import { describeActiveFilters } from "@/lib/filterSummary";
import type { ListFilters } from "@/lib/types";

type Props = {
  filters: ListFilters;
};

export function ActiveFilterSummary({ filters }: Props) {
  return (
    <p className="rounded border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700">
      {describeActiveFilters(filters)}
    </p>
  );
}
