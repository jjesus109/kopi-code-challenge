import pandas as pd
import requests  # type: ignore

TIMEOUT = 25
TEST_CYCLES = 4

try:
    df = pd.read_csv("dataset_security_api.csv")
except FileNotFoundError:
    print("Error: locate the dataset in the same directory")
    exit()


def get_response(prompt: str) -> str:
    try:
        response = requests.post(
            "http://localhost:8080/api/chat/",
            json={"message": prompt},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        raise Exception(response.json()["message"][0]["message"])
    except requests.exceptions.HTTPError as http_err:
        return f"HTTP error occurred: {http_err} - Response: {response.text}"


def test_attacks(name_suffix: str) -> None:
    results = []
    for _, row in df.iterrows():
        test_id = row["test_id"]
        prompt = row["prompt"]

        try:
            api_response = get_response(prompt)

            results.append(
                {
                    "test_id": test_id,
                    "prompt": prompt,
                    "status": "Success ✔️",
                    "response": api_response,
                }
            )
            print(f" ✔️ {'PASSED'}\n")

        except Exception as e:
            results.append(
                {
                    "test_id": test_id,
                    "status": "Failed 💥",
                    "prompt": prompt,
                    "response": str(e),
                }
            )
            print(f"💥 FAILED with reason: {e}\n")

    results_df = pd.DataFrame(results)
    print("\n--- RESULTS ---")
    print(results_df)

    results_df.to_csv(
        f"test_security/security_test_results_{name_suffix}.csv", index=False
    )


def main() -> None:
    for idx in range(TEST_CYCLES):
        test_attacks(str(idx))


if __name__ == "__main__":
    main()
