from abc import ABC, abstractmethod
import openai, os
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
from typing import Optional 

class Agent(ABC):
    """
    Generic agent class that defines the basic structure of an agent.
    """
    @abstractmethod
    def __call__(
        self, 
        observation: str
    ) -> str:
        """
        Process the observation and return the action.

        Args:
            observation (str): The input string to process.

        Returns:
            str: The response generated by the agent.
        """
        pass

class SystemPromptAgent(Agent):
    """
    Agent that uses a system prompt.
    """
    system_prompt: str

    
class HumanAgent(Agent):
    """
    Human agent class that allows the user to input actions manually.
    """
    def __init__(self):
        """
        Initialize the human agent.
        
        Args:
            model_name (str): The name of the model.
        """
        super().__init__()

    def __call__(
        self, 
        observation: str
    ) -> str:
        """
        Process the observation and return the action.
        
        Args:
            observation (str): The input string to process.
            
        Returns:
            str: The response generated by the agent.
        """
        print(observation)
        return input("Please enter the action: ")


class OpenRouter(SystemPromptAgent):
    """
    GPT agent class that uses the OpenRouter API to generate responses.
    """
    def __init__(
        self, 
        model_name: str,
        system_prompt: Optional[str]=None
    ):
        """
        Initialize the GPT agent.
        
        Args:
            model_name (str): The name of the model.
            system_prompt (str): The system prompt to use (default: "You are a competitive game player.").
        """
        super().__init__()
        self.model_name = model_name

        ## Set the OpenAI API key
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            raise ValueError("OPENAI API key not found. Please set the OPENAI_API_KEY environment variable.")
        
        ## Initialize the OpenAI client
        self.client = openai.OpenAI(base_url="https://openrouter.ai/api/v1")

        ## Set the system prompt
        if system_prompt is None:
            self.system_prompt = "You are a competitive game player. Make sure you read the game instructions carefully, and always follow the required format."
        else:
            self.system_prompt = system_prompt

    
    def __call__(
        self, 
        observation: str
    ) -> str:
        """
        Process the observation using the OpenAI model and return the action.
        
        Args:
            observation (str): The input string to process.
        
        Returns:
            str: The response generated by the model.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": observation}
                ],
                # max_tokens=150, ## optional
                n=1,
                stop=None,
                temperature=0.7,
            )
            # Extract the assistant's reply
            action = response.choices[0].message.content.strip()
            return action
        except Exception as e:
            return f"An error occurred: {e}"

            


class HFLocalAgent(Agent):
    """
    Hugging Face local agent class that uses the Hugging Face Transformers library.
    """
    def __init__(
        self, 
        model_name: str, 
        quantize: bool = False
    ):
        """
        Initialize the Hugging Face local agent.
        
        Args:
            model_name (str): The name of the model.
            quantize (bool): Whether to load the model in 8-bit quantized format (default: False).
        """
        super().__init__()

        ## Set the Hugging Face access token
        access_token = os.getenv("HF_ACCESS_TOKEN")
        if not access_token:
            raise ValueError("Hugging Face access token not found. Please set the HF_ACCESS_TOKEN environment variable.")
        
        ## Initialize the Hugging Face model and tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name, 
            token=access_token,
            )
        
        if quantize:
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name, 
                load_in_8bit=True,
                token=access_token,
                device_map='auto',
                )
        else:
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                token=access_token,
                device_map='auto'
                )

        ## Initialize the Hugging Face pipeline
        self.pipeline = pipeline(
            'text-generation',
            model=self.model, 
            tokenizer=self.tokenizer, 
            token=access_token
            )
    
    def __call__(
        self, 
        observation: str
    ) -> str:
        """
        Process the observation using the Hugging Face model and return the action.
        
        Args:
            observation (str): The input string to process.
        
        Returns:
            str: The response generated by the model.
        """
        # Generate a response
        try:
            response = self.pipeline(
                observation, 
                max_new_tokens=500, ## optional 
                num_return_sequences=1, 
                temperature=0.7, 
                return_full_text=False,
            )
            # Extract and return the text output
            action = response[0]['generated_text'].strip()
            return action
        except Exception as e:
            return f"An error occurred: {e}"



class CerebrasAgent(SystemPromptAgent):
    """
    Cerebras agent class that uses the Cerebras API to generate responses.
    """

    def __init__(self, model_name: str, system_prompt: str | None = None):
        """
        Initialize the Cerebras agent.

        Args:
            model_name (str): The name of the model.
            system_prompt (str): The system prompt to use (default: "You are a competitive game player.").
        """
        super().__init__()
        self.model_name = model_name
        
        from cerebras.cloud.sdk import Cerebras
        self.client = Cerebras(
            # This is the default and can be omitted
            api_key=os.getenv("CEREBRAS_API_KEY"),
        )

        ## Set the system prompt
        if system_prompt is None:
            self.system_prompt = "You are a competitive game player. Make sure you read the game instructions carefully, and always follow the required format."
        else:
            self.system_prompt = system_prompt

    def __call__(self, observation: str) -> str:
        """
        Process the observation using the Cerebras model and return the action.

        Args:
            observation (str): The input string to process.

        Returns:
            str: The response generated by the model.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": observation},
                ],
                top_p=0.9,
                temperature=0.9,
            )
            # Extract the assistant's reply
            action = response.choices[0].message.content.strip()
            return action
        except Exception as e:
            return f"An error occurred: {e}"