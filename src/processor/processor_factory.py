from processor import BaseProcessor
from processor import simpleTransformerProcessor

class ProcessorFactory:
    _processors = {
        "transformer": simpleTransformerProcessor,
        # "openai": 
        # "anthropic":
        # "llama":
    }

    @classmethod
    def get_processor(cls, processor_type: str, **kwargs) -> BaseProcessor:
        processor_class = cls._processors.get(processor_type.lower())
        if not processor_class:
            raise ValueError(f"Unknown processor type: {processor_type}")
        return processor_class(**kwargs)