from abc import ABC, abstractmethod
from PIL import Image

class ImageEditor(ABC):
    """
    Process the given PIL image and return the modified image.

    :param image: PIL.Image.Image object
    :param options: dynamic keyword args for operation-specific parameters
    :return: new PIL.Image.Image object
    """
    @abstractmethod
    def edit(self, image: Image.Image, **options) -> Image.Image:
        pass
