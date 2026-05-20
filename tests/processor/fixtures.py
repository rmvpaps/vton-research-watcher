import pytest
from processor import ProcessorUtils

@pytest.fixture
def processutil():
    util = ProcessorUtils()
    return util