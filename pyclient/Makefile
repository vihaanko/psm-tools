default:
	make getswagger
	make genclient

getswagger:
	python3 getswagger.py

genclient: getswagger
	bash gen.sh

setpythonpath:
	export PYTHONPATH=$(PWD)