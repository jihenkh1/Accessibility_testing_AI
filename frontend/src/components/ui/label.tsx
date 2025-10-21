import * as React from "react";
import { cn } from "./utils";

function Label({ className, ...props }: React.ComponentProps<"label">) {
  return (
    <label data-slot="label" className={cn("text-sm text-foreground", className)} {...props} />
  );
}

export { Label };

