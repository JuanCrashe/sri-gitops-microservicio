import urllib.request
import concurrent.futures
import subprocess
import time
import json

results = []
stop = False

def probe():
    while not stop:
        try:
            t0 = time.time()
            with urllib.request.urlopen("http://localhost:5000/api/v1/version", timeout=1.5) as resp:
                lat = (time.time() - t0) * 1000
                content = json.loads(resp.read().decode("utf-8"))
                results.append(("OK", resp.status, content.get("hostname"), lat))
        except Exception as e:
            results.append(("FAIL", 0, str(e), 0))
        time.sleep(0.1)

# Obtener nombre de un pod activo
pods_raw = subprocess.check_output(["kubectl", "get", "pods", "-l", "app=sri-backend", "-n", "sri-facturacion", "-o", "jsonpath={.items[*].metadata.name}"]).decode("utf-8").strip()
pods = pods_raw.split()
target_pod = pods[0]
print(f"Pod seleccionado para eliminacion abrupta: {target_pod}")

with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
    future = ex.submit(probe)
    
    time.sleep(1.0)
    print(f"Eliminando forzadamente el pod {target_pod} con --now...")
    del_res = subprocess.run(["kubectl", "delete", "pod", target_pod, "-n", "sri-facturacion", "--now"], capture_output=True, text=True)
    print(del_res.stdout.strip())
    
    time.sleep(4.0)
    stop = True

total = len(results)
ok = sum(1 for r in results if r[0] == "OK")
fail = sum(1 for r in results if r[0] == "FAIL")

print(f"\n--- RESUMEN DE DISPONIBILIDAD (ZERO-DOWNTIME) ---")
print(f"Total peticiones enviadas: {total}")
print(f"Peticiones exitosas (HTTP 200 OK): {ok} ({(ok/total)*100:.1f}%)")
print(f"Peticiones fallidas: {fail} ({(fail/total)*100:.1f}%)")

hosts = {}
for r in results:
    if r[0] == "OK":
        h = r[2]
        hosts[h] = hosts.get(h, 0) + 1
print("\nDistribucion de trafico atendido por pods:")
for h, count in hosts.items():
    print(f"  - {h}: {count} peticiones")
