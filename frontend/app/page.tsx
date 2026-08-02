import { redirect } from "next/navigation";

import { getToken } from "@/lib/fastapi";

export default async function Home() {
  const token = await getToken();
  redirect(token ? "/chat" : "/login");
}
