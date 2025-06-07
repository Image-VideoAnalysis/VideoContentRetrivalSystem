


export async function search(query) {
  const res = await fetch(`http://localhost:8000/search?query=${encodeURIComponent(query)}`);
  if (!res.ok) throw new Error("Search failed");
  return await res.json();
}
