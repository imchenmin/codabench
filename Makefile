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

transport-sched-build:
	cd competition/transport_sched && \
	zip -r ingestion_program.zip ingestion_program && \
	zip -r scoring_program.zip scoring_program && \
	zip -r baseline_submission.zip baseline_submission && \
	zip -r datasets_public.zip datasets/public

transport-sched-test:
	python3 competition/transport_sched/ingestion_program/run.py /Users/chenmin/Develop/codabench/competition/transport_sched/datasets/public /Users/chenmin/Develop/codabench/competition/transport_sched/out/baseline /Users/chenmin/Develop/codabench/competition/transport_sched/baseline_submission && \
	python3 competition/transport_sched/scoring_program/score.py /Users/chenmin/Develop/codabench/competition/transport_sched/datasets/public /Users/chenmin/Develop/codabench/competition/transport_sched/out/baseline

transport-sched-validate:
	python3 -m json.tool competition/transport_sched/datasets/public/cases/case_01/machine.json >/dev/null && \
	python3 -m json.tool competition/transport_sched/datasets/public/cases/case_01/job.json >/dev/null && \
	python3 -m json.tool competition/transport_sched/datasets/public/cases/case_01/am.json >/dev/null
