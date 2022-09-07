Run unit tests from the 'sources' directory, so that all modules can be found.
Also, pytest only adds to sys.path directories where test files are, so you need to add the sources directory with:

export PYTHONPATH=.
pytest ./tests/unit_tests

Also, you can run, from the sources directory ./tests/unit_tests/run.sh
