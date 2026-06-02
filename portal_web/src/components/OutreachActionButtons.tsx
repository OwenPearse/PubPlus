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
  actions: Action[];
};

export function OutreachActionButtons({
  layout = "column",
  size = "xs",
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
          className={`text-left underline disabled:opacity-40 ${textSize} ${
            action.className ?? "text-slate-700"
          }`}
          onClick={action.onClick}
        >
          {action.label}
        </button>
      ))}
    </div>
  );
}
