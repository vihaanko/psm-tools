default:
	make getswagger
	make genclient

getswagger:
	python3 getswagger.py

genclient: getswagger
	./gen.sh

set-python-path:
	export PYTHONPATH="$(pwd)"