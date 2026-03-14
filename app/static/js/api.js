async function apiGet(path) {
  const res = await fetch(`/api/${path}`);
  if (!res.ok) throw new Error(`GET /api/${path} failed: ${res.status}`);
  return res.json();
}

async function apiPost(path, data) {
  const res = await fetch(`/api/${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`POST /api/${path} failed: ${res.status}`);
  return res.json();
}

async function apiPut(path, data) {
  const res = await fetch(`/api/${path}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`PUT /api/${path} failed: ${res.status}`);
  return res.json();
}

async function apiDelete(path) {
  const res = await fetch(`/api/${path}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`DELETE /api/${path} failed: ${res.status}`);
  return res.json();
}

window.API = { get: apiGet, post: apiPost, put: apiPut, delete: apiDelete };
