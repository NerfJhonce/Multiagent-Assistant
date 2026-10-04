import os
import sys
import time
import requests
import json

GATEWAY_URL = "http://localhost:8000/task"

EVAL_TASKS = [
    {
        "id": "task_1",
        "description": "Create a function to check if a word is a palindrome.",
    },
    {
        "id": "task_2",
        "description": "Create a function that receives a list of numbers and returns only even numbers.",
    },
    {
        "id": "task_3",
        "description": "Write a function that calculates the factorial of a positive integer.",
    }
]


def run_evaluation():
    print("INITIATING AUTOMATED ASSESSMENT OF AGENTS")

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
                timeout=240  # Increased to 4 minutes for local LLM
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
                    f"  └─ status: {'APPROVED' if is_approved else 'FAILED '} | iterations: {iterations} | time: {elapsed}s\n")
            else:
                print(f"  └─ Error HTTP {response.status_code}\n")
                results.append({"id": item["id"], "success": False, "iterations": 0, "latency": elapsed})

        except requests.exceptions.Timeout:
            elapsed = round(time.time() - start_time, 2)
            print(f"  └─ Error: Timeout (Exceeded the 240s)\n")
            results.append({"id": item["id"], "success": False, "iterations": 0, "latency": elapsed})
        except Exception as e:
            elapsed = round(time.time() - start_time, 2)
            print(f"  └─ Connection Error: {e}\n")
            results.append({"id": item["id"], "success": False, "iterations": 0, "latency": elapsed})

    # Aggregate Metric Calculation
    total_tasks = len(results)
    passed_tasks = sum(1 for r in results if r["success"])
    success_rate = (passed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
    avg_iterations = sum(r["iterations"] for r in results) / total_tasks if total_tasks > 0 else 0
    avg_latency = sum(r["latency"] for r in results) / total_tasks if total_tasks > 0 else 0

    print("Evaluation summary")
    print(f" Total tasks:        {total_tasks}")
    print(f" Successful Tasks:       {passed_tasks} / {total_tasks}")
    print(f" Task Success Rate:     {success_rate:.1f}%")
    print(f" Average Iterations:  {avg_iterations:.2f}")
    print(f" Average latency:     {avg_latency:.2f}s")
    print(f" Total Suite Time:    {round(time.time() - total_start_time, 2)}s")


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

    print("Evaluation report saved in evals/results.json")


if __name__ == "__main__":
    run_evaluation()