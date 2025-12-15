import * as React from "react";
import { cn } from "@/lib/utils";

const badgeVariants = {
  default: "bg-ink-900 text-white",
  secondary: "bg-ink-100 text-ink-900",
  outline: "border border-ink-100 text-ink-900",
};

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: keyof typeof badgeVariants;
}

function Badge({ className, variant = "default", ...props }: BadgeProps) {
  return <div className={cn("inline-flex items-center rounded-full px-3 py-1 text-xs font-medium", badgeVariants[variant], className)} {...props} />;
}

export { Badge };
