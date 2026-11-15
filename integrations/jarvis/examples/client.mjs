// Call the APL API from JavaScript (Node 18+ or a browser: fetch is built in).
//   node integrations/jarvis/examples/client.mjs [http://localhost:8080]
const URL = process.argv[2] ?? "http://localhost:8080";

async function apl(endpoint, payload) {
  const res = await fetch(`${URL}/${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return { status: res.status, body: await res.json() };
}

const primes = await apl("Primes", 50);
console.log("Primes up to 50:", primes.body);

const stats = await apl("Stats", [3, 1, 4, 1, 5, 9, 2, 6]);
console.log("Stats:", stats.body);

const words = await apl("WordCount", { text: "to be or not to be", top: 2 });
console.log("Top words:", words.body);
