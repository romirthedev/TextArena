from textarena.envs.two_player.dont_say_it import DontSayItEnv
import time, os, openai

from textarena.wrappers import (
    PrettyRenderWrapper,
    LLMObservationWrapper,
    ClipWordsActionWrapper
)


import textarena

textarena.pprint_registry()
class GPTAgent:
    def __init__(self, model_name: str):
        """
        Initialize the GPTAgent with the specified OpenAI model.
        
        Args:
            model_name (str): The name of the OpenAI model to use (e.g., "gpt-4").
        """
        self.model_name = model_name
        self.agent_identifier = model_name
        # Load the OpenAI API key from environment variable
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
    
    def __call__(self, observation: str) -> str:
        """
        Process the observation using the OpenAI model and return the action.
        
        Args:
            observation (str): The input string to process.
        
        Returns:
            str: The response generated by the model.
        """
        # try:
        response = openai.ChatCompletion.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": observation}
            ],
            max_tokens=150,
            n=1,
            stop=None,
            temperature=0.7,
        )
        # Extract the assistant's reply
        action = response.choices[0].message['content'].strip()
        return action
        # except Exception as e:
        #     return f"An error occurred: {e}"


# build agents
agent_0 = GPTAgent(
    model_name="gpt-4o"
)

agent_1 = GPTAgent(
    model_name="gpt-4o-mini"
)

# env = DontSayItEnv(hardcore=True)
env = textarena.make("TruthAndDeception-v0")

# wrap for LLM use
env = LLMObservationWrapper(env=env)

# env = ClipWordsActionWrapper(env, max_num_words=150)

# wrap env
env = PrettyRenderWrapper(
    env=env,
    agent_identifiers={
        0: agent_0.agent_identifier,
        1: agent_1.agent_identifier
    }
)


observations, info = env.reset()
# input(env.game_state)

done=False
while not done:
    for player_id, agent in enumerate([agent_0, agent_1]):
        # get the agent prompt
        action = agent(
            observations[player_id]
        )
        # print(observations[player_id])
        # input(action)

        observations, reward, truncated, terminated, info = env.step(player_id, action)
        env.render()
        time.sleep(1)

        done = truncated or terminated

        if done:
            break

for l in env.state.logs:
    print(l, end="\n\n") 
# time.sleep(1)
# _, _, truncated, terminated, _ =env.step(1, "Another test, just to see.")
# env.render()
# time.sleep(1)   
# done = truncated or terminated


# while True:
#     # Player 0's turn
#     #print(f"\n{agent_identifiers.get(0, 'Player 0')}'s turn.")
#     #print(obs0)
#     action0 = input("Enter your message: ")
#     obs1, reward, truncated, terminated, info = env.step(player_id=0, action=action0)
#     env.render()
#     if terminated or truncated:
#         break

#     # Player 1's turn
#     #print(f"\n{agent_identifiers.get(1, 'Player 1')}'s turn.")
#     #print(obs1)
#     action1 = input("Enter your message: ")
#     obs0, reward, truncated, terminated, info = env.step(player_id=1, action=action1)
#     env.render()
#     if terminated or truncated:
#         break