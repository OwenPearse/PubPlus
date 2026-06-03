import type { ReactNode } from "react";

type Props = {
  href: string;
  children: ReactNode;
  className?: string;
};

export function ExternalLink({ href, children, className }: Props) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className={className ?? "text-blue-700 underline"}
    >
      {children}
    </a>
  );
}
