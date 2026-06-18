# <<<./ Import Libraries
from abc import ABC, abstractmethod
from PIL import Image
from src.schemas import Receipt

# <<<./ Error Message for Extraction Fails
class ExtractionError(Exception):
    pass

# <<<./ Enforce extract() by Abstraction
class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, image: Image.Image):
        pass

