import { Loader2 } from "lucide-react";

interface LoadingStateProps {
  label?: string;
}

export function LoadingState({ label = "Working..." }: LoadingStateProps) {
  return (
    <div className="flex items-center gap-3 text-sm text-slate-300">
      <Loader2 className="h-4 w-4 animate-spin text-cyan-300" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}
