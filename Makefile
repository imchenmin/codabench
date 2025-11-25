IMAGE_WEB?=codabench-web:latest
IMAGE_WORKER?=codabench-compute-worker:latest

.PHONY: build-web build-worker build-all up down logs

build-web:
	docker build --platform linux/amd64 -f Dockerfile.web -t $(IMAGE_WEB) .

build-worker:
	docker build --platform linux/amd64 -f Dockerfile.compute_worker -t $(IMAGE_WORKER) .

build-all: build-web build-worker

up:
	docker compose up -d

down:
	docker compose down --volumes

logs:
	docker compose logs -f --tail=200

# 传输调度赛题打包与本地验证
.PHONY: transport-sched-build transport-sched-test transport-sched-validate
 .PHONY: transport-sched-test-python transport-sched-test-c transport-sched-test-cpp transport-sched-test-java transport-sched-test-all-sdks

transport-sched-build:
	./bin/package_transport_sched.sh

transport-sched-test:
	python3 competition/transport_sched/ingestion_program/run.py /Users/chenmin/Develop/codabench/competition/transport_sched/datasets/public /Users/chenmin/Develop/codabench/competition/transport_sched/out/baseline /Users/chenmin/Develop/codabench/competition/transport_sched/baseline_submission && \
	python3 competition/transport_sched/scoring_program/score.py /Users/chenmin/Develop/codabench/competition/transport_sched/datasets/public /Users/chenmin/Develop/codabench/competition/transport_sched/out/baseline

transport-sched-test-python:
	python3 competition/transport_sched/ingestion_program/run.py /Users/chenmin/Develop/codabench/competition/transport_sched/datasets/public /Users/chenmin/Develop/codabench/competition/transport_sched/out/python /Users/chenmin/Develop/codabench/competition/transport_sched/sdks/python && \
	python3 competition/transport_sched/scoring_program/score.py /Users/chenmin/Develop/codabench/competition/transport_sched/datasets/public /Users/chenmin/Develop/codabench/competition/transport_sched/out/python

transport-sched-test-c:
	python3 competition/transport_sched/ingestion_program/run.py /Users/chenmin/Develop/codabench/competition/transport_sched/datasets/public /Users/chenmin/Develop/codabench/competition/transport_sched/out/c /Users/chenmin/Develop/codabench/competition/transport_sched/sdks/c && \
	python3 competition/transport_sched/scoring_program/score.py /Users/chenmin/Develop/codabench/competition/transport_sched/datasets/public /Users/chenmin/Develop/codabench/competition/transport_sched/out/c

transport-sched-test-cpp:
	python3 competition/transport_sched/ingestion_program/run.py /Users/chenmin/Develop/codabench/competition/transport_sched/datasets/public /Users/chenmin/Develop/codabench/competition/transport_sched/out/cpp /Users/chenmin/Develop/codabench/competition/transport_sched/sdks/cpp && \
	python3 competition/transport_sched/scoring_program/score.py /Users/chenmin/Develop/codabench/competition/transport_sched/datasets/public /Users/chenmin/Develop/codabench/competition/transport_sched/out/cpp

transport-sched-test-java:
	python3 competition/transport_sched/ingestion_program/run.py /Users/chenmin/Develop/codabench/competition/transport_sched/datasets/public /Users/chenmin/Develop/codabench/competition/transport_sched/out/java /Users/chenmin/Develop/codabench/competition/transport_sched/sdks/java && \
	python3 competition/transport_sched/scoring_program/score.py /Users/chenmin/Develop/codabench/competition/transport_sched/datasets/public /Users/chenmin/Develop/codabench/competition/transport_sched/out/java

transport-sched-test-all-sdks: transport-sched-test-python transport-sched-test-c transport-sched-test-cpp transport-sched-test-java

transport-sched-validate:
	python3 -m json.tool competition/transport_sched/datasets/public/cases/case_01/machine.json >/dev/null && \
	python3 -m json.tool competition/transport_sched/datasets/public/cases/case_01/job.json >/dev/null && \
	python3 -m json.tool competition/transport_sched/datasets/public/cases/case_01/am.json >/dev/null

.PHONY: import-users
import-users:
	TEMP_SUBMISSION_STORAGE=$(PWD)/.tmp ./manage.py import_users_to_competition $(CSV) $(OPTS)
