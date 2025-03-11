# InferenceProfile.py
import os
import openai
from transformers import AutoTokenizer
import json
from dotenv import load_dotenv


def file_sanity_check(full_file_path):
    """
    Checks if the specified file exists, is readable, and is not empty.

    Args:
        file_path (str): The path to the file to be checked.

    Raises:
        FileNotFoundError: If the file does not exist at the specified location.
        PermissionError: If there aren't sufficient permissions to read the file.
        ValueError: If the file is empty.
    """
    if not os.path.isfile(full_file_path):
        raise FileNotFoundError(f"The file {full_file_path} could not be found.")

    elif not os.access(full_file_path, os.R_OK):
        raise PermissionError(f"Permission denied to read the file {full_file_path}")

    # Check if the file is empty
    if os.path.getsize(full_file_path) == 0:
        raise ValueError(f"The file {full_file_path} is empty")


def get_full_resource_path(env_variable: str, resource_name: str) -> str:
    """
    Constructs the full path to a resource by joining the value of an environment variable with a resource name.

    Args:
        env_variable (str): The name of the environment variable that provides the base directory.
        resource_name (str): The name of the resource file or folder.

    Returns:
        str: The full path to the resource.

    Raises:
        EnvironmentError: If the specified environment variable does not exist.
        FileNotFoundError: If the resource does not exist at the specified location.
    """
    # Retrieve the environment variable's value which should be a valid path
    env_value = os.getenv(env_variable)

    if env_value is None:
        raise EnvironmentError(
            f"Environment variable '{env_variable}' is not set, please set it."
        )

    resource_path = os.path.join(env_value, resource_name)

    # Perform the file sanity check
    file_sanity_check(resource_path)

    return resource_path


class InferenceProfile:

    @classmethod
    def load_profile(cls, profile_name: str) -> None:
        """
        Loads an inference profile from a JSON file located in the PROFILES_DIR.

        Args:
            profile_name (str): The name of the profile to load, without the file extension.

        Raises:
            EnvironmentError: If the environment variable 'PROFILES_DIR' is not set, indicating the directory where profiles are stored.
            FileNotFoundError: If the specified profile file does not exist within the PROFILES_DIR.
            PermissionError: If there are insufficient permissions to read the profile file.
            ValueError: If the profile file is empty.

        Notes:
            This class method constructs the full path to the profile using the `get_full_resource_path` function.
            The method reads the profile parameters from the JSON file, initializes an `InferenceProfile` instance with these parameters, and assigns it to the class instance variable `self`.
        """
        full_profile_path = get_full_resource_path(
            "PROFILES_DIR", f"{profile_name}.json"
        )
        with open(full_profile_path, "r") as json_file:
            profile_params = json.load(json_file)

        return cls(**profile_params)

    def __init__(
        self,
        engine_name: str,  # Not used in code but exists for easy identification of the engine running on the endpoint
        base_url: str,  # Should be an OpenAI API compatible endpoint (e.g., https://api.openai.com/v1 or https://localhost:8000/api/v1)
        model_id: str,  # Engine-specific, generally human readable
        config_folder_name: str,  # Name of the folder containing the model's configuration files
        api_key: str = "CHANGE_ME",  # The API key for authentication to the OpenAI API endpoint. Defaults to "CHANGE_ME".
        system_prompt_file: str = "",
        tools: list[str] = [],
        optional_hyper_parameters: dict = {},
        load_tokenizer_flag=False,
    ) -> None:
        """
        Initializes an InferenceProfile.

        Required Parameters:
            engine_name (str): Not used in code but exists for human readability.
            base_url (str): The OpenAI API compatible endpoint. Typically ends with `/v1` (e.g., https://api.openai.com/v1 or https://localhost:8000/api/v1).
            model_id (str): Engine-specific, generally human readable.
            config_folder_name (str): The name of the folder containing the model's configuration files.

        Optional Parameters:
            api_key (str, optional): The API key for authentication to the OpenAI API endpoint. Defaults to "CHANGE_ME".
            system_prompt_file (str, optional): The filename of a system prompt located within the SYSTEM_PROMPTS_DIR directory. If left blank, the system prompt will be loaded from the configuration file.
            tools (list[str], optional): A list of tool names available in the tools directory defined in the .env file. Defaults to an empty list.
            optional_hyper_parameters (dict, optional): Optional keyword arguments for inference such as temperature, seed, topk, top-p, etc. Defaults to an empty dictionary.
            load_tokenizer_flag (bool, optional): Bool value that determines if the profile should load the tokenizer. Only enable this if you need to calculate the model specific token count of a string.
        Notes:
            - `engine_name` is not used in code but exists for human readability.
            - `base_url` should be an OpenAI API compatible endpoint that typically ends with `/v1`.
            - `model_id` is engine-specific and generally human readable.
            - `load_tokenizer_flag` should only be used when pre-inference token count is needed as the inference engine will return the token count.
        """

        self._engine_name = engine_name
        self._base_url = base_url
        self._model_id = model_id
        self._config_folder_name = config_folder_name
        self._system_prompt_file = system_prompt_file
        self._tools = tools
        self._optional_hyper_parameters = optional_hyper_parameters
        self._api_key = api_key
        self._load_tokenizer_flag = load_tokenizer_flag

        self._load_files()

    def get_client(self) -> openai.Client:
        """
        Builds and returns an OpenAI API client using the class variables like base_address and API.

        Returns:
            openai.Client: An initialized OpenAI API client.
        """

        client = openai.OpenAI(
            base_url=self._base_url,
            api_key=self._api_key,  # required but often unused
        )

        return client

    def get_async_client(self) -> openai.AsyncClient:
        """
        Builds and returns an OpenAI API async client using the class variables like base_address and API.

        Returns:
            openai.AsyncClient: An initialized OpenAI API client.
        """

        client = openai.AsyncOpenAI(
            base_url=self._base_url,
            api_key=self._api_key,  # required but often unused
        )

        return client

    def _to_dict(self):
        return {
            "engine_name": self._engine_name,
            "base_url": self._base_url,
            "model_id": self._model_id,
            "config_folder_name": self._config_folder_name,
            "api_key": self._api_key,
            "system_prompt_file": self._system_prompt_file,
            "tools": self._tools,
            "optional_hyper_parameters": self._optional_hyper_parameters,
            "load_tokenizer_flag": self._load_tokenizer_flag,
        }

    def save_profile(self, profile_name: str) -> None:
        """
        Saves the current profile parameters to the PROFILES_DIR path with a unique name.

        Args:
            profile_name (str): The desired name for the profile. If it already exists, a unique name will be generated by appending a number until a unique name is found.

        Raises:
            EnvironmentError: If environment variable 'PROFILES_DIR' is not set.
            ValueError: If a unique profile name cannot be created.
        """
        profiles_dir = os.getenv("PROFILES_DIR")

        if not profiles_dir:
            raise EnvironmentError(
                f"Environment variable 'PROFILES_DIR' is not set, please set it."
            )

        # Ensure the profiles directory exists
        os.makedirs(profiles_dir, exist_ok=True)

        # Create the file path ensuring number uniqueness
        unique_profile_name = profile_name
        file_path = os.path.join(profiles_dir, f"{unique_profile_name}.json")
        counter = 1

        # TODO Fix naming scheme if file exists. This works but is not elegant
        while os.path.exists(file_path):
            unique_profile_name = f"{profile_name}_{counter}"
            file_path = os.path.join(profiles_dir, f"{unique_profile_name}.json")
            counter += 1

        # Save the profile parameters to the file
        with open(file_path, "w") as json_file:
            json.dump(self._to_dict(), json_file, indent=4)

        print(f"Profile '{unique_profile_name}' saved to {file_path}")

    def __str__(self) -> str:
        return json.dumps(self._to_dict(), indent=4)

    def _load_files(self):
        tokenizer_config_path = get_full_resource_path(
            "MODEL_CONFIG_DIR",
            os.path.join(self._config_folder_name, "tokenizer_config.json"),
        )
        tokenizer_path = get_full_resource_path(
            "MODEL_CONFIG_DIR", os.path.join(self._config_folder_name, "tokenizer.json")
        )
        system_prompt_path = (
            get_full_resource_path(
                "SYSTEM_PROMPTS_DIR", f"{self._system_prompt_file}.txt"
            )
            if self._system_prompt_file
            else None
        )
        tool_definitions_dir = (
            [
                get_full_resource_path("TOOL_DEFINITIONS_DIR", f"{tool}.json")
                for tool in self._tools
            ]
            if self._tools
            else None
        )

        # Load tokenizer.json if the file is set
        if os.path.exists(tokenizer_path) and self._load_tokenizer_flag:
            self._tokenizer = AutoTokenizer.from_pretrained(
                os.path.dirname(tokenizer_path), local_files_only=True
            )

        # Load tokenizer_config.json if the file is set
        if os.path.exists(tokenizer_config_path):
            with open(tokenizer_config_path, "r") as f:
                self._tokenizer_config = json.load(f)

        # Load system prompt if present and the file is set
        if system_prompt_path:
            with open(system_prompt_path, "r") as f:
                self._system_prompt = f.read()

        # Load tools if the list is non-empty
        if tool_definitions_dir:
            self._tools = [
                json.load(open(tool_path)) for tool_path in tool_definitions_dir
            ]

    def format_inference_params(self) -> dict:
        """
        Formats the model ID, tools, and optional hyperparameters into a dictionary suitable for use as keyword arguments in API calls to an OpenAI API endpoint for chat completion.

        Returns:
            dict: A dictionary containing the necessary parameters for an inference request, ready to be used as `kwargs` in API calls.
        """
        inference_request = {"model": self._model_id}

        # Edited here to have the reasoning correctly return, was getting stuck in a tool call loop.
        # Just let the model produce a normal completion.

        inference_request.update(self._optional_hyper_parameters)
        return inference_request

    def get_token_count(self, text: str) -> int:
        """
        Returns the number of tokens in the given text for this profiles model.

        Parameters:
        text (str): The input text to tokenize.

        Returns:
        int: The number of tokens in the text.
        """
        if not self._load_tokenizer_flag:
            raise ValueError(
                "load_tokenizer_flag is False and tokenizer is not loaded. Set load_tokenizer_flag to True in the Profile's json and reload the profile."
            )

        return len(self._tokenizer(text)["input_ids"])

    def set_optional_param(self, params: dict) -> None:
        """
        Update the optional hyperparameters for the inference profile.

        Args:
            params: A dictionary representing the optional parameters to update.
        """
        self._optional_hyper_parameters.update(params)

    def set_api_key(self, api_key: str) -> None:
        """Set the API key for the inference profile.

        Args:
            api_key (str): The API key to be set.
        """
        self._api_key = api_key

    def format_messages_chat(self, messages: list[dict]) -> list[dict]:
        """
        Ensures that the messages list starts with a system message if the first message is not a system message and a system prompt is available.

        Args:
            messages (list[dict]): A list of message dictionaries, each containing a "role" and "content" key.

        Returns:
            list[dict]: The formatted list of messages, ensuring the first message is a system message if needed.

        Notes:
            - If the first message in the list is not a system message and a system prompt is available, a system message will be inserted at the beginning of the list.
            - This method is particularly useful for chat-based interactions where the system message provides context for the conversation.
        """

        # TODO add role matching using the loaded chat_template
        if messages[0]["role"] != "system" and hasattr(self, "_system_prompt"):
            if self._system_prompt is not None:
                messages.insert(0, {"role": "system", "content": self._system_prompt})
        return messages
