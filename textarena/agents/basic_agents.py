from abc import ABC, abstractmethod
import os, time
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
from typing import Optional 

from textarena.core import Agent
import textarena as ta 

# API provider imports
import google.generativeai as genai
from openai import OpenAI



__all__ = [
    "HumanAgent",
    "OpenRouterAgent",
    "GeminiAgent",
    "OpenAIAgent",
    "HFLocalAgent",
    "CerebrasAgent",
]


STANDARD_GAME_PROMPT = "You are a competitive game player. Make sure you read the game instructions carefully, and always follow the required format. The first action returned in squared brackets will be used."
    
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


class OpenRouterAgent(Agent):
    """ Agent class using the OpenRouter API to generate responses. """
    def __init__(self, model_name: str, system_prompt: Optional[str] = STANDARD_GAME_PROMPT, verbose: bool = False, **kwargs):
        """
        Initialize the OpenRouter agent.

        Args:
            model_name (str): The name of the model.
            system_prompt (Optional[str]): The system prompt to use (default: STANDARD_GAME_PROMPT)
            verbose (bool): If True, additional debug info will be printed.
            **kwargs: Additional keyword arguments to pass to the OpenAI API call.
        """
        super().__init__()
        self.model_name = model_name 
        self.verbose = verbose 
        self.system_prompt = system_prompt
        self.kwargs = kwargs

        # Set the open router api key from an environment variable
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OpenRouter API key not found. Please set the OPENROUTER_API_KEY environment variable.")
        
        self.client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
        

    def _make_request(self, observation: str) -> str:
        """ Make a single API request to OpenRouter and return the generated message. """
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": observation}
        ]
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            n=1,
            stop=None,
            **self.kwargs
        )

        return response.choices[0].message.content.strip()

    def _retry_request(self, observation: str, retries: int = 3, delay: int = 5) -> str:
        """
        Attempt to make an API request with retries.

        Args:
            observation (str): The input to process.
            retries (int): The number of attempts to try.
            delay (int): Seconds to wait between attempts.

        Raises:
            Exception: The last exception caught if all retries fail.
        """
        last_exception = None
        for attempt in range(1, retries + 1):
            try:
                response = self._make_request(observation)
                if self.verbose:
                    print(f"\nObservation: {observation}\nResponse: {response}")
                return response

            except Exception as e:
                last_exception = e
                print(f"Attempt {attempt} failed with error: {e}")
                if attempt < retries:
                    time.sleep(delay)
        raise last_exception

    def __call__(self, observation: str) -> str:
        """
        Process the observation using the OpenRouter API and return the action.

        Args:
            observation (str): The input string to process.

        Returns:
            str: The generated response.
        """
        if not isinstance(observation, str):
            raise ValueError(f"Observation must be a string. Received type: {type(observation)}")
        return self._retry_request(observation)


class GeminiAgent(Agent):
    """Agent class using the Google Gemini API to generate responses."""
    
    def __init__(
        self, 
        model_name: str, 
        system_prompt: Optional[str] = STANDARD_GAME_PROMPT,
        verbose: bool = False,
        generation_config: Optional[dict] = None
    ):
        """
        Initialize the Gemini agent.
        
        Args:
            model_name (str): The name of the model.
            system_prompt (Optional[str]): The system prompt to use (default: STANDARD_GAME_PROMPT).
            verbose (bool): If True, additional debug info will be printed.
            generation_config (Optional[dict]): The configuration for text generation.
        """
        super().__init__()
        self.model_name = model_name
        self.system_prompt = system_prompt
        self.verbose = verbose

        # Set the Gemini API key from an environment variable
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Gemini API key not found. Please set the GEMINI_API_KEY environment variable.")
        
        # Configure the Gemini client
        genai.configure(api_key=api_key)
        
        # Use default generation config if none is provided
        if generation_config is None:
            generation_config = {
                "temperature": 1,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
                "response_mime_type": "text/plain",
            }
        self.generation_config = generation_config
        
        # Create the Gemini model
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=self.generation_config
        )
    
    def _make_request(self, observation: str) -> str:
        """
        Make a single API request to Gemini and return the generated message.
        
        Args:
            observation (str): The input string to process.
        
        Returns:
            str: The generated response text.
        """
        response = self.model.generate_content(
            f"Instructions: {self.system_prompt}\n\n{observation}"
        )
        
        if self.verbose:
            print(f"\nObservation: {observation}\nResponse: {response.text}")
        
        return response.text.strip()
    
    def _retry_request(self, observation: str, retries: int = 3, delay: int = 5) -> str:
        """
        Attempt to make an API request with retries.
        
        Args:
            observation (str): The input to process.
            retries (int): The number of attempts to try.
            delay (int): Seconds to wait between attempts.
        
        Raises:
            Exception: The last exception caught if all retries fail.
        """
        last_exception = None
        for attempt in range(1, retries + 1):
            try:
                return self._make_request(observation)
            except Exception as e:
                last_exception = e
                print(f"Attempt {attempt} failed with error: {e}")
                if attempt < retries:
                    time.sleep(delay)
        raise last_exception
    
    def __call__(self, observation: str) -> str:
        """
        Process the observation using the Gemini API and return the generated response.
        
        Args:
            observation (str): The input string to process.
        
        Returns:
            str: The generated response.
        """
        if not isinstance(observation, str):
            raise ValueError(f"Observation must be a string. Received type: {type(observation)}")
        return self._retry_request(observation)



class OpenAIAgent(Agent):
    """Agent class using the OpenAI API to generate responses."""
    
    def __init__(
        self, 
        model_name: str, 
        system_prompt: Optional[str] = STANDARD_GAME_PROMPT,
        verbose: bool = False,
        **kwargs
    ):
        """
        Initialize the OpenAI agent.
        
        Args:
            model_name (str): The name of the model.
            system_prompt (Optional[str]): The system prompt to use (default: STANDARD_GAME_PROMPT).
            verbose (bool): If True, additional debug info will be printed.
            **kwargs: Additional keyword arguments to pass to the OpenAI API call.
        """
        super().__init__()
        self.model_name = model_name
        self.system_prompt = system_prompt
        self.verbose = verbose
        self.kwargs = kwargs

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
        
        self.client = OpenAI(api_key=api_key)
        
    
    def _make_request(self, observation: str) -> str:
        """
        Make a single API request to OpenAI and return the generated message.
        
        Args:
            observation (str): The input string to process.
        
        Returns:
            str: The generated response text.
        """
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": observation}
        ]
        
        # Make the API call using the provided model and messages.
        completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            n=1,
            stop=None,
            **self.kwargs
        )
        
        return completion.choices[0].message.content.strip()
    
    def _retry_request(self, observation: str, retries: int = 3, delay: int = 5) -> str:
        """
        Attempt to make an API request with retries.
        
        Args:
            observation (str): The input to process.
            retries (int): The number of attempts to try.
            delay (int): Seconds to wait between attempts.
        
        Raises:
            Exception: The last exception caught if all retries fail.
        """
        last_exception = None
        for attempt in range(1, retries + 1):
            try:
                response = self._make_request(observation)
                if self.verbose:
                    print(f"\nObservation: {observation}\nResponse: {response}")
                return response
            except Exception as e:
                last_exception = e
                print(f"Attempt {attempt} failed with error: {e}")
                if attempt < retries:
                    time.sleep(delay)
        raise last_exception
    
    def __call__(self, observation: str) -> str:
        """
        Process the observation using the OpenAI API and return the generated response.
        
        Args:
            observation (str): The input string to process.
        
        Returns:
            str: The generated response.
        """
        if not isinstance(observation, str):
            raise ValueError(f"Observation must be a string. Received type: {type(observation)}")
        return self._retry_request(observation)


class HFLocalAgent(Agent):
    """
    Hugging Face local agent class that uses the Hugging Face Transformers library.
    """
    def __init__(
        self, 
        model_name: str, 
        device: str = "auto",
        quantize: bool = False
    ):
        """
        Initialize the Hugging Face local agent.
        
        Args:
            model_name (str): The name of the model.
            quantize (bool): Whether to load the model in 8-bit quantized format (default: False).
        """
        super().__init__()
        ## Initialize the Hugging Face model and tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name, 
            )
        
        if quantize:
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name, 
                load_in_8bit=True,
                device_map=device,
                )
        else:
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map=device,
                )

        ## Initialize the Hugging Face pipeline
        self.pipeline = pipeline(
            'text-generation',
            max_new_tokens=500,
            model=self.model, 
            tokenizer=self.tokenizer, 
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
                STANDARD_GAME_PROMPT+"\n"+observation, 
                num_return_sequences=1, 
                return_full_text=False,
            )
            # Extract and return the text output
            action = response[0]['generated_text'].strip()
            return action
        except Exception as e:
            return f"An error occurred: {e}"



class CerebrasAgent(Agent):
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