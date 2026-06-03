type Action = {
  id: string;
  label: string;
  className?: string;
  onClick: () => void;
  disabled?: boolean;
};

type Props = {
  layout?: "row" | "column";
  size?: "xs" | "sm";
  variant?: "link" | "button";
  actions: Action[];
};

export function OutreachActionButtons({
  layout = "column",
  size = "xs",
  variant = "link",
  actions,
}: Props) {
  const textSize = size === "sm" ? "text-sm" : "text-xs";
  const flexClass = layout === "row" ? "flex flex-wrap gap-1" : "flex flex-col gap-1";

  return (
    <div className={flexClass}>
      {actions.map((action) => (
        <button
          key={action.id}
          type="button"
          disabled={action.disabled}
          className={
            variant === "button"
              ? `rounded border border-slate-300 bg-white px-2 py-0.5 font-medium hover:bg-slate-50 disabled:opacity-40 ${textSize} ${
                  action.className ?? "text-slate-800"
                }`
              : `text-left underline disabled:opacity-40 ${textSize} ${
                  action.className ?? "text-slate-700"
                }`
          }
          onClick={action.onClick}
        >
          {action.label}
        </button>
      ))}
    </div>
  );
}
