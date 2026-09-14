import os
import sys
import time
import requests
import json

GATEWAY_URL = "http://localhost:8000/task"

EVAL_TASKS = [
    {
        "id": "task_1",
        "description": "Crea una función para verificar si una palabra es un palíndromo.",
    },
    {
        "id": "task_2",
        "description": "Crea una función que reciba una lista de números y devuelva solo los números pares.",
    },
    {
        "id": "task_3",
        "description": "Escribe una función que calcule el factorial de un número entero positivo.",
    }
]


def run_evaluation():
    print("==================================================")
    print("INICIANDO EVALUACIÓN AUTOMATIZADA DE AGENTES")
    print("==================================================\n")

    results = []
    total_start_time = time.time()

    for item in EVAL_TASKS:
        print(f"Executing [{item['id']}]: {item['description']}...")
        start_time = time.time()

        try:
            response = requests.post(
                GATEWAY_URL,
                json={"task": item["description"]},
                headers={"Content-Type": "application/json"},
                timeout=240  # Aumentado a 4 minutos para LLM local
            )
            elapsed = round(time.time() - start_time, 2)

            if response.status_code == 200:
                data = response.json()
                is_approved = data.get("is_approved", False)
                iterations = data.get("iterations", 0)

                results.append({
                    "id": item["id"],
                    "success": is_approved,
                    "iterations": iterations,
                    "latency": elapsed
                })
                print(
                    f"  └─ status: {'APPROVED ✅' if is_approved else 'FAILED ❌'} | iterations: {iterations} | time: {elapsed}s\n")
            else:
                print(f"  └─ Error HTTP {response.status_code}\n")
                results.append({"id": item["id"], "success": False, "iterations": 0, "latency": elapsed})

        except requests.exceptions.Timeout:
            elapsed = round(time.time() - start_time, 2)
            print(f"  └─ Error: Timeout (Superó los 240s)\n")
            results.append({"id": item["id"], "success": False, "iterations": 0, "latency": elapsed})
        except Exception as e:
            elapsed = round(time.time() - start_time, 2)
            print(f"  └─ Error de conexión: {e}\n")
            results.append({"id": item["id"], "success": False, "iterations": 0, "latency": elapsed})

    # Cálculo de métricas agregadas
    total_tasks = len(results)
    passed_tasks = sum(1 for r in results if r["success"])
    success_rate = (passed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
    avg_iterations = sum(r["iterations"] for r in results) / total_tasks if total_tasks > 0 else 0
    avg_latency = sum(r["latency"] for r in results) / total_tasks if total_tasks > 0 else 0

    print("==================================================")
    print("RESUMEN DE EVALUACIÓN")
    print("==================================================")
    print(f" Tareas Totales:        {total_tasks}")
    print(f" Tareas Exitosas:       {passed_tasks} / {total_tasks}")
    print(f" Task Success Rate:     {success_rate:.1f}%")
    print(f" Promedio Iteraciones:  {avg_iterations:.2f}")
    print(f" Latencia Promedio:     {avg_latency:.2f}s")
    print(f" Tiempo Total Suite:    {round(time.time() - total_start_time, 2)}s")
    print("==================================================\n")

    os.makedirs("evals", exist_ok=True)
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "summary": {
            "total_tasks": total_tasks,
            "passed_tasks": passed_tasks,
            "success_rate_pct": success_rate,
            "avg_iterations": avg_iterations,
            "avg_latency_sec": avg_latency
        },
        "details": results
    }

    with open("evals/results.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)

    print("Reporte de evaluación guardado en evals/results.json")


if __name__ == "__main__":
    run_evaluation()