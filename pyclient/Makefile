default:
	make getswagger
	make genclient

getswagger:
	python3 getswagger.py

genclient: getswagger
	sh gen.sh