import os
import time

import aiohttp
import asyncio
import backoff
import dotenv

import textarena
from textarena.envs.two_player.iterated_prisoners_dilemma import (
    IteratedPrisonersDilemma,
)
from textarena.wrappers import (
    ClipWordsActionWrapper,
    LLMObservationWrapper,
    PrettyRenderWrapper,
)

RETRY_EXCEPTIONS = (aiohttp.ClientError, asyncio.TimeoutError, AssertionError)

dotenv.load_dotenv()
OPEN_ROUTER_TOKEN = os.getenv("OPEN_ROUTER_TOKEN")

textarena.pprint_registry_detailed()


@backoff.on_exception(backoff.expo, RETRY_EXCEPTIONS, max_tries=5, jitter=None)
# @utils.file_cache(verbose=True) # not implemented yet but can it is really cool...
async def open_router_generate(
    text: str, model_string: str, message_history: list[dict] | None, **gen_kwargs
) -> str:
    try:
        async with aiohttp.ClientSession(raise_for_status=True) as session:
            if not message_history:
                message_history = []
            response = await session.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPEN_ROUTER_TOKEN}",
                },
                json={
                    "model": model_string,  # Optional
                    "messages": message_history
                    + [
                        {"role": "user", "content": text},
                    ],
                    **gen_kwargs,  # https://openrouter.ai/docs/parameters
                },
                timeout=100,
            )
            response_json = await response.json()
            if (
                not response_json or "choices" not in response_json
            ):  # check if response is valid
                raise AssertionError("Invalid response")
            return response_json["choices"][0]["message"]["content"]
    except Exception as e:
        return f"An error occurred: {e}"


DEFAULT_GEN_KWARGS = {
    "max_tokens": 150,
    "n": 1,
    "stop": None,
    "temperature": 0.7,
}


class GPTAgent:
    def __init__(self, model_name: str):
        """
        Initialize the GPTAgent with the specified OpenAI model.

        Args:
            model_name (str): The name of the OpenAI model to use (e.g., "gpt-4").
        """
        self.model_name = model_name
        self.agent_identifier = model_name
        self.auth_token = os.getenv("OPEN_ROUTER_TOKEN")

    def __call__(
        self, observations: list[str], gen_kwargs=DEFAULT_GEN_KWARGS
    ) -> list[str]:
        """
        Process the observation using the OpenAI model and return the action.

        Args:
            observation (str): The input string to process.

        Returns:
            str: The response generated by the model.
        """
        loop = asyncio.get_event_loop()
        responses = loop.run_until_complete(
            asyncio.gather(
                *[
                    open_router_generate(
                        prompt, f"openai/{self.model_name}", None, **gen_kwargs
                    )
                    for prompt in observations
                ]
            )
        )
        return responses


# build agents
agent_0 = GPTAgent(model_name="gpt-4o-mini")

agent_1 = GPTAgent(model_name="gpt-3.5-turbo")

# env = DontSayItEnv(hardcore=True)
# env = textarena.make("DontSayIt-v0-hardcore")
textarena.register(
    "IteratedPrisonersDilemma-v0",
    lambda: IteratedPrisonersDilemma(chat_turns_per_round=1, max_turns=30),
)
env = textarena.make("IteratedPrisonersDilemma-v0")

# wrap for LLM use
env = LLMObservationWrapper(env=env)

# env = ClipWordsActionWrapper(env, max_num_words=150)

# # wrap env
# env = PrettyRenderWrapper(
#     env=env,
#     agent_identifiers={0: agent_0.agent_identifier, 1: agent_1.agent_identifier},
# )


observations, info = env.reset()
# input(env.game_state)

done = False
while not done:
    for player_id, agent in enumerate([agent_0, agent_1]):

        # get the agent prompt
        action = agent([observations[player_id]])[0]
        print(action)

        observations, reward, truncated, terminated, info = env.step(player_id, action)
        env.render()
        print(info)
        time.sleep(1)

        done = truncated or terminated

        if done:
            break

for l in env.game_state["logs"]:
    print(l, end="\n\n")
