def pytest_addoption(parser):
    parser.addoption("--record", action="store_true")

def pytest_addoption(parser):
    parser.addoption("--retain", action="store_true")

# def pytest_generate_tests(metafunc):
#     # This is called for every test. Only get/set command line arguments
#     # if the argument is specified in the list of test "fixturerecords".
#     option_value = metafunc.config.option.record
#     if 'record' in metafunc.fixturerecords and option_value is not None:
#         metafunc.parametrize("record", [option_value])
