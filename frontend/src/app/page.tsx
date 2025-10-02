// サーバーコンポーネントで即リダイレクト
import { redirect } from "next/navigation";

export default function Page() {
  redirect("/dashboard/search");
}