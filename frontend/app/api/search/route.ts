export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const q = searchParams.get('query') ?? '';
  const u = `http://vendor0919-alb-new-619968933.ap-northeast-1.elb.amazonaws.com/search?query=${encodeURIComponent(q)}`;
  const r = await fetch(u);
  return new Response(await r.text(), { status: r.status, headers: { 'content-type': r.headers.get('content-type') || 'application/json' }});
}
export async function POST(req: Request) {
  const body = await req.text();
  const r = await fetch('http://vendor0919-alb-new-619968933.ap-northeast-1.elb.amazonaws.com/search', {
    method: 'POST', headers: { 'content-type': 'application/json' }, body
  });
  return new Response(await r.text(), { status: r.status, headers: { 'content-type': r.headers.get('content-type') || 'application/json' }});
}
