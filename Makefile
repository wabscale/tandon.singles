# Python
MAIN_NAME=dev.py
ENV_NAME=venv
PYTHON_VERSION=`which python3`

# Docker
DOCKER_IMAGE_NAME=flasq

DOCKER_OPTIONS=--rm -it -p 5000:5000
DOCKER_DEPLOY_OPTIONS=

.PHONY: db

all: debug
buildall: buildbase build

############################################################
#      _            _                   _          __  __  #
#   __| | ___   ___| | _____ _ __   ___| |_ _   _ / _|/ _| #
#  / _` |/ _ \ / __| |/ / _ \ '__| / __| __| | | | |_| |_  #
# | (_| | (_) | (__|   <  __/ |    \__ \ |_| |_| |  _|  _| #
#  \__,_|\___/ \___|_|\_\___|_|    |___/\__|\__,_|_| |_|   #
#                                                          #
############################################################

deploy:
	if [ -n "`docker image list -q | nice grep jmc1283/flasq-base`" ]; then \
		docker pull jmc1283/flasq-base; \
	fi
	if ! docker network ls | grep "traefik-proxy"; then \
		docker network create traefik-proxy; \
	fi
	git submodule update
	docker-compose kill
	docker-compose rm -f
	docker-compose up --build -d --force-recreate ${DOCKER_DEPLOY_OPTIONS}

build:
	if [ -n "`docker image list -q | nice grep jmc1283/flasq-base`" ]; then \
		docker pull jmc1283/flasq-base; \
	fi
	docker build -t ${DOCKER_IMAGE_NAME} .

buildbase:
	docker build -t jmc1283/flasq-base base

drun: dkill
	docker run ${DOCKER_OPTIONS} --name ${DOCKER_IMAGE_NAME} ${DOCKER_IMAGE_NAME}

dclean: killd
	docker system prune -f
	if [ -n "`docker image list -q | grep ${DOCKER_IMAGE_NAME}`" ]; then \
		docker rmi ${DOCKER_IMAGE_NAME}; \
		docker rmi jmc1283/flasq-base; \
	fi

dkill:
	if [ -z "$(docker ps -q) | grep ${DOCKER_IMAGE_NAME}" ]; then \
		docker kill ${DOCKER_IMAGE_NAME}; \
	fi

db:
	docker-compose kill
	docker-compose rm -f
	docker-compose up -d --force-recreate db

backup:
	mkdir -p .data
	docker-compose exec db mysqldump -h 127.0.0.1 -u root --password=password TS > .data/dump.sql

restore:
	docker-compose exec -T db mysql -h 127.0.0.1 -u root --password=password TS < .data/dump.sql

##########################################################
#      _      _                       _          __  __  #
#   __| | ___| |__  _   _  __ _   ___| |_ _   _ / _|/ _| #
#  / _` |/ _ \ '_ \| | | |/ _` | / __| __| | | | |_| |_  #
# | (_| |  __/ |_) | |_| | (_| | \__ \ |_| |_| |  _|  _| #
#  \__,_|\___|_.__/ \__,_|\__, | |___/\__|\__,_|_| |_|   #
#                         |___/                          #
#																												 #
##########################################################

setup:
	if [ -d ${ENV_NAME} ]; then \
		rm -rf ${ENV_NAME}; \
	fi
	if [ -a base/requirements.txt ]; then \
		touch base/requirements.txt; \
	fi
	if [ ! -e web/.data ]; then \
		mkdir -p web/.data/uploads; \
	fi
	which virtualenv && pip install virtualenv || true
	virtualenv -p ${PYTHON_VERSION} ${ENV_NAME}
	./${ENV_NAME}/bin/pip install -r base/requirements.txt
	./${ENV_NAME}/bin/pip install -r requirements.txt
	./${ENV_NAME}/bin/pip install -r bigsql/requirements.txt

debug:
	if [ ! -d ${ENV_NAME} ]; then \
		make setup; \
	fi
	if [ ! -e web/.data ]; then \
		mkdir -p web/.data/uploads; \
	fi
	./${ENV_NAME}/bin/python ${MAIN_NAME}

pyclean:
	if [ -d ${ENV_NAME} ]; then \
		rm -rf ${ENV_NAME}; \
	fi
	if [ -n "`find . -name __pycache__`" ]; then \
		rm -rf `find . -name __pycache__`; \
	fi

clean: pyclean
	if [ -d .data ]; then \
		rm -rf .data; \
	fi
