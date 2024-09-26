import tiktoken


def num_tokens_for_llm(string: str, llm: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.encoding_for_model(llm)
    num_tokens = len(encoding.encode(string))
    return num_tokens


def trim_document_content(documents: list[dict], max_tokens: int, text_key: str) -> list[dict]:
    # calculate what to trim each document to achieve max_tokens across all documents
    total_document_text = " ".join([context[text_key] for context in documents])
    total_document_tokens = num_tokens_for_llm(total_document_text, "gpt-3.5-turbo")
    if total_document_tokens > max_tokens:
        max_tokens_per_document = max_tokens // len(documents)
        for context in documents:
            context[text_key] = context[text_key][:max_tokens_per_document] + "..."
    return documents