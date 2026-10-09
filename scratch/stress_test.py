import urllib.request
import concurrent.futures
import time

URL = "http://localhost:5000/api/v1/version"
DURATION_SECONDS = 75
WORKERS = 40

print(f"Iniciando prueba de carga contra {URL} con {WORKERS} hilos durante {DURATION_SECONDS}s...")
end_time = time.time() + DURATION_SECONDS
total_requests = 0
successes = 0

def worker_loop():
    global total_requests, successes
    count = 0
    ok = 0
    while time.time() < end_time:
        try:
            req = urllib.request.Request(URL)
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status == 200:
                    ok += 1
        except Exception:
            pass
        count += 1
    return count, ok

start = time.time()
with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as executor:
    futures = [executor.submit(worker_loop) for _ in range(WORKERS)]
    for f in concurrent.futures.as_completed(futures):
        c, o = f.result()
        total_requests += c
        successes += o

elapsed = time.time() - start
print(f"Prueba completada: {total_requests} peticiones ({successes} exitosas) en {elapsed:.2f}s ({total_requests/elapsed:.1f} req/s).")
