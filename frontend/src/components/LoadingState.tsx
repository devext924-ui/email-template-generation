import { Loader2 } from "lucide-react";

interface LoadingStateProps {
  label?: string;
  className?: string;
}

export function LoadingState({ label = "Working...", className = "" }: LoadingStateProps) {
  return (
    <div
      className={`flex items-center justify-center gap-2.5 text-sm text-slate-200 ${className}`}
      role="status"
      aria-live="polite"
    >
      <Loader2 className="h-4 w-4 animate-spin text-cyan-300" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}
