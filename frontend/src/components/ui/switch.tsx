import * as React from "react";
import { cn } from "./utils";

type SwitchProps = {
  id?: string;
  checked?: boolean;
  defaultChecked?: boolean;
  disabled?: boolean;
  className?: string;
  onCheckedChange?: (checked: boolean) => void;
  "aria-label"?: string;
};

export function Switch({
  id,
  checked,
  defaultChecked,
  disabled,
  className,
  onCheckedChange,
  ...rest
}: SwitchProps) {
  const isControlled = checked !== undefined;
  const [internal, setInternal] = React.useState<boolean>(defaultChecked ?? false);
  const isOn = isControlled ? !!checked : internal;

  function toggle() {
    if (disabled) return;
    const next = !isOn;
    if (!isControlled) setInternal(next);
    onCheckedChange?.(next);
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLButtonElement>) {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      toggle();
    }
  }

  return (
    <button
      type="button"
      role="switch"
      aria-checked={isOn}
      aria-disabled={disabled || undefined}
      id={id}
      disabled={disabled}
      onClick={toggle}
      onKeyDown={onKeyDown}
      data-slot="switch"
      className={cn(
        "inline-flex h-6 w-10 items-center rounded-full border transition-colors outline-none",
        "focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]",
        disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer",
        isOn ? "bg-primary border-primary" : "bg-secondary border-input",
        className,
      )}
      {...rest}
    >
      <span
        aria-hidden
        className={cn(
          "inline-block size-5 translate-x-0 rounded-full bg-card shadow transition-transform",
          isOn ? "translate-x-4" : "translate-x-0.5",
        )}
      />
    </button>
  );
}

