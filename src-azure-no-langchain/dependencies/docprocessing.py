# Yan Pan, 2023
import re
from tiktoken import encoding_for_model

from dependencies.logger import logger


class DocProcessing:
    """
    A set of functions to better pre-process documents
    It is part of dependencies
    """

    @staticmethod
    def count_tokens(text, return_tokenized=False):
        encoder = encoding_for_model("text-embedding-ada-002")
        tokenized = encoder.encode(text)
        if return_tokenized:
            return tokenized
        return len(tokenized)

    @staticmethod
    def split_to_sentences(text: str):
        """
        Split a long sting into a list of sentences
        https://stackoverflow.com/questions/4576077/how-can-i-split-a-text-into-sentences
        """
        alphabets = "([A-Za-z])"
        prefixes = "(Mr|St|Mrs|Ms|Dr)[.]"
        suffixes = "(Inc|Ltd|Jr|Sr|Co)"
        starters = r"(Mr|Mrs|Ms|Dr|Prof|Capt|Cpt|Lt|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"   # noqa: E501
        acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
        websites = "[.](com|net|org|io|gov|edu|me)"
        digits = "([0-9])"
        multiple_dots = r'\.{2,}'

        text = " " + text + "  "
        text = text.replace("\n", " ")
        text = re.sub(prefixes, "\\1<prd>", text)
        text = re.sub(websites, "<prd>\\1", text)
        text = re.sub(digits + "[.]" + digits, "\\1<prd>\\2", text)
        text = re.sub(multiple_dots, lambda match: "<prd>" * len(match.group(0)) + "<stop>", text)   # noqa: E501
        if "Ph.D" in text:
            text = text.replace("Ph.D.", "Ph<prd>D<prd>")
        text = re.sub(r"\s" + alphabets + "[.] ", " \\1<prd> ", text)
        text = re.sub(acronyms+" " + starters, "\\1<stop> \\2", text)
        text = re.sub(alphabets + "[.]" + alphabets + "[.]" + alphabets + "[.]", "\\1<prd>\\2<prd>\\3<prd>", text)   # noqa: E501
        text = re.sub(alphabets + "[.]" + alphabets + "[.]", "\\1<prd>\\2<prd>", text)   # noqa: E501
        text = re.sub(" " + suffixes+"[.] " + starters, " \\1<stop> \\2", text)
        text = re.sub(" " + suffixes+"[.]", " \\1<prd>", text)
        text = re.sub(" " + alphabets + "[.]", " \\1<prd>", text)
        if "”" in text:
            text = text.replace(".”", "”.")
        if "\"" in text:
            text = text.replace(".\"", "\".")
        if "!" in text:
            text = text.replace("!\"", "\"!")
        if "?" in text:
            text = text.replace("?\"", "\"?")
        text = text.replace(".", ".<stop>")
        text = text.replace("?", "?<stop>")
        text = text.replace("!", "!<stop>")
        text = text.replace("<prd>", ".")
        sentences = text.split("<stop>")
        sentences = [s.strip() for s in sentences]
        if sentences and not sentences[-1]:
            sentences = sentences[:-1]
        return sentences

    @staticmethod
    def chunk_text_by_sentences(
        text: str,
        max_tokens: int = 2000,
        overlapping_sentences: int = 2,
    ):
        """
        C# SplitIntoMaxTokenChunks
        currently use RE to split (known to have issue like 'Mr.')
        max_tokens may exceed if value too small and long sentences in text
        """
        sentences = DocProcessing.split_to_sentences(text)
        chunks, the_chunk, tokens = [], "", []
        for i, s in enumerate(sentences):
            n_tokens = DocProcessing.count_tokens(the_chunk)
            n_tokens_s = DocProcessing.count_tokens(s)

            if n_tokens + n_tokens_s > max_tokens:
                chunks.append(the_chunk)
                tokens.append(n_tokens + n_tokens_s)
                # the_chunk starts with overlapping_sentences + 1
                the_chunk = " ".join(sentences[(i-overlapping_sentences):(i+1)])  # noqa: E501
            else:
                the_chunk += s + " "
        # final chunk
        chunks.append(the_chunk)
        tokens.append(n_tokens + n_tokens_s)
        logger.debug(f"input text {DocProcessing.count_tokens(text)} tokens, splitted to {len(chunks)} chunks of size {tokens} roughly")  # noqa: E501

        return chunks
