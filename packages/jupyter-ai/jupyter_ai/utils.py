import openai


class LLMErrorUtilBase:
    @staticmethod
    def is_api_key_exc(e: Exception):
        raise NotImplementedError("Should be implemented by subclasses.")


class OpenAIErrorUtil(LLMErrorUtilBase):
    @staticmethod
    def is_api_key_exc(e: Exception):
        if isinstance(e, openai.error.AuthenticationError):
            error_details = e.json_body.get("error", {})
            return error_details.get("code") == "invalid_api_key"
        return False


class AI21ErrorUtility:
    @staticmethod
    def is_api_key_exc(e: Exception):
        if isinstance(e, ValueError):
            # Check if the exception message contains "status code 401"
            return "status code 401" in str(e)
        return False
