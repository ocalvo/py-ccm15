param($repo = "testpypi")

git clean -dfx .
python setup.py sdist bdist_wheel
python -m twine upload --repository $repo dist/*
