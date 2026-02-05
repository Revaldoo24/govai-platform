import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const baseUrl = process.env.GOVAI_GATEWAY_URL;
    const apiKey = process.env.GOVAI_API_KEY;

    if (!baseUrl) {
      return NextResponse.json({ detail: "Missing GOVAI_GATEWAY_URL" }, { status: 500 });
    }

    const resp = await fetch(`${baseUrl}/generate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": apiKey || "",
        "X-Tenant-Id": body.tenant_id || "",
      },
      body: JSON.stringify(body),
      cache: "no-store",
    });

    const data = await resp.json();
    return NextResponse.json(data, { status: resp.status });
  } catch (err) {
    return NextResponse.json({ detail: "Proxy error" }, { status: 500 });
  }
}
