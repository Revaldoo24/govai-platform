import { NextRequest, NextResponse } from "next/server";

export async function GET(req: NextRequest, { params }: { params: { id: string } }) {
  const baseUrl = process.env.GOVAI_GOV_URL;
  if (!baseUrl) {
    return NextResponse.json({ detail: "Missing GOVAI_GOV_URL" }, { status: 500 });
  }
  const resp = await fetch(`${baseUrl}/decisions/${params.id}/detail`, { cache: "no-store" });
  const data = await resp.json();
  return NextResponse.json(data, { status: resp.status });
}

export async function POST(req: NextRequest, { params }: { params: { id: string } }) {
  const baseUrl = process.env.GOVAI_GOV_URL;
  if (!baseUrl) {
    return NextResponse.json({ detail: "Missing GOVAI_GOV_URL" }, { status: 500 });
  }
  const body = await req.json();
  const resp = await fetch(`${baseUrl}/decisions/${params.id}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await resp.json();
  return NextResponse.json(data, { status: resp.status });
}
