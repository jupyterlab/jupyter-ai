import openai
import anthropic


class LLMErrorUtilBase:
    @staticmethod
    def is_api_key_exc(e: Exception):
        """
        Determine if the exception is an API key error. Should be implemented by subclasses.
        """
        raise NotImplementedError("Should be implemented by subclasses.")


class OpenAIErrorUtil(LLMErrorUtilBase):
    @staticmethod
    def is_api_key_exc(e: Exception):
        """
        Determine if the exception is an OpenAI API key error.
        """
        if isinstance(e, openai.error.AuthenticationError):
            error_details = e.json_body.get("error", {})
            return error_details.get("code") == "invalid_api_key"
        return False


class AI21ErrorUtility(LLMErrorUtilBase):
    @staticmethod
    def is_api_key_exc(e: Exception):
        """
        Determine if the exception is an AI21 API key error.
        """
        if isinstance(e, ValueError):
            # Check if the exception message contains "status code 401"
            return "status code 401" in str(e)
        return False


class AnthropicErrorUtility(LLMErrorUtilBase):
    @staticmethod
    def is_api_key_exc(e):
        """
        Determine if the exception is an Anthropic API key error.
        """
        if isinstance(e, anthropic.AuthenticationError):
            return e.status_code == 401 and "Invalid API Key" in str(e)
        return False
