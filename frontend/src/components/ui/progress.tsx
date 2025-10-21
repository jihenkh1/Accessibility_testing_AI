import * as React from "react";
import { cn } from "./utils";

type Props = React.ComponentProps<"div"> & { value?: number }

function Progress({ className, value = 0, ...props }: Props) {
  return (
    <div data-slot="progress" className={cn("w-full h-2 bg-muted rounded", className)} {...props}>
      <div className="h-2 bg-primary rounded" style={{ width: `${Math.max(0, Math.min(100, value))}%` }} />
    </div>
  )
}

export { Progress }

