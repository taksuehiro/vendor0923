import { type ClassValue } from "clsx";
import clsx from "clsx";
import { twMerge } from "tailwind-merge";

/** shadcn/ui 用ユーティリティ: className を賢く結合 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(...inputs));
}