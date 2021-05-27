default:
	make getswagger
	make genclient

getswagger:
	python3 getswagger.py

genclient:
	bash gen.sh

build-generator:
	cd openapi-generator
	mvn clean install -U -DskipTests
	cd ..