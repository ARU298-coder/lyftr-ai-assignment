import time
import hashlib
import json

from litellm import completion

from app.config import LLM_API_KEYS, LLM_MODEL


# Temporary in-memory cache.
# We will switch this to LiteLLM built-in caching before submission.
response_cache = {}


def make_cache_key(messages):
    """
    Cache key = model + complete message list.
    """

    payload = {
        "model": LLM_MODEL,
        "messages": messages
    }

    raw = json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False
    )

    return hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()


def call_llm(messages, simulated_failures=None):

    simulated_failures = simulated_failures or {}

    # ---------------------------------------
    # 1. CHECK CACHE
    # ---------------------------------------

    cache_key = make_cache_key(messages)

    if cache_key in response_cache:

        cached = response_cache[cache_key]

        return {
            "reply": cached["reply"],
            "resolution_source": "LLM_CACHE",
            "model": cached["model"],
            "latency_ms": 1,
            "input_tokens": cached["input_tokens"],
            "output_tokens": cached["output_tokens"],
            "key_id": None,
            "fallback_attempts": 0
        }

    # ---------------------------------------
    # 2. LIVE LLM CALL
    # ---------------------------------------

    fallback_attempts = 0

    start_time = time.perf_counter()

    for index, api_key in enumerate(LLM_API_KEYS):

        key_id = f"key_{index + 1}"

        # -----------------------------------
        # FAILURE SIMULATION
        # -----------------------------------

        if "*" in simulated_failures:

            print(
                f"SIMULATED FAILURE: "
                f"{key_id} -> "
                f"{simulated_failures['*']}"
            )

            fallback_attempts += 1

            continue

        if key_id in simulated_failures:

            print(
                f"SIMULATED FAILURE: "
                f"{key_id} -> "
                f"{simulated_failures[key_id]}"
            )

            fallback_attempts += 1

            continue

        # -----------------------------------
        # REAL GEMINI CALL THROUGH LITELLM
        # -----------------------------------

        try:

            print(
                f"Trying {key_id} "
                f"with model {LLM_MODEL}"
            )

            response = completion(
                model=LLM_MODEL,
                messages=messages,
                api_key=api_key,
                timeout=30
            )

            latency_ms = int(
                (time.perf_counter() - start_time)
                * 1000
            )

            # --------------------------------
            # GET RESPONSE TEXT
            # --------------------------------

            reply = response.choices[0].message.content

            if not reply:
                raise RuntimeError(
                    "Provider returned an empty response"
                )

            # --------------------------------
            # TOKEN USAGE
            # --------------------------------

            usage = getattr(
                response,
                "usage",
                None
            )

            input_tokens = 0
            output_tokens = 0

            if usage is not None:

                input_tokens = (
                    getattr(
                        usage,
                        "prompt_tokens",
                        0
                    )
                    or 0
                )

                output_tokens = (
                    getattr(
                        usage,
                        "completion_tokens",
                        0
                    )
                    or 0
                )

            # --------------------------------
            # SUCCESS
            # --------------------------------

            result = {
                "reply": reply,
                "resolution_source":
                    "LIVE_INFERENCE",
                "model": LLM_MODEL,
                "latency_ms": latency_ms,
                "input_tokens": int(
                    input_tokens
                ),
                "output_tokens": int(
                    output_tokens
                ),
                "key_id": key_id,
                "fallback_attempts":
                    fallback_attempts
            }

            # Save successful response
            response_cache[cache_key] = {
                "reply": reply,
                "model": LLM_MODEL,
                "input_tokens": int(
                    input_tokens
                ),
                "output_tokens": int(
                    output_tokens
                )
            }

            print(
                f"SUCCESS: {key_id} "
                f"answered in {latency_ms} ms"
            )

            return result

        # -----------------------------------
        # PROVIDER FAILED
        # -----------------------------------

        except Exception as error:

            print("")
            print("=" * 60)
            print(
                f"ERROR WITH {key_id}"
            )
            print(
                f"ERROR TYPE: "
                f"{type(error).__name__}"
            )
            print(
                f"ERROR MESSAGE: {error}"
            )
            print("=" * 60)
            print("")

            fallback_attempts += 1

            # Automatically move to next key
            continue

    # ---------------------------------------
    # 3. EVERY KEY FAILED
    # ---------------------------------------

    print(
        "ALL CONFIGURED LLM KEYS FAILED"
    )

    raise RuntimeError(
        "all providers unavailable"
    )