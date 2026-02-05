import { NextRequest, NextResponse } from "next/server";

export async function GET(req: NextRequest) {
  const baseUrl = process.env.GOVAI_GOV_URL;
  if (!baseUrl) {
    return NextResponse.json({ detail: "Missing GOVAI_GOV_URL" }, { status: 500 });
  }
  const { searchParams } = new URL(req.url);
  const tenantId = searchParams.get("tenant_id");
  const status = searchParams.get("status") || "";
  if (!tenantId) {
    return NextResponse.json({ detail: "Missing tenant_id" }, { status: 400 });
  }
  const qs = new URLSearchParams({ tenant_id: tenantId });
  if (status) qs.set("status", status);
  const resp = await fetch(`${baseUrl}/decisions?${qs.toString()}`, { cache: "no-store" });
  const data = await resp.json();
  return NextResponse.json(data, { status: resp.status });
}
