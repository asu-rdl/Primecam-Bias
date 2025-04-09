all:
	@echo "-----------------------------------------------------------"
	@echo "First time run should be 'make dockerimage'"
	@echo "followed by 'make deploy'"
	@echo ""
	@echo "Commands"
	@echo "========"
	@echo "dockerimage - build a docker image for cross compilation"
	@echo "docker      - launch built docker image, make"
	@echo "              dockerimage should be built first"
	@echo "deploy      - starts docker container, builds target, "
	@echo "              uploads to the raspberry pi and runs it"
	@echo "app         - builds target normally"
	@echo "clean       - cleans up built artifacts"
	@echo "-----------------------------------------------------------"

dockerimage:
	docker build . -t local/rustypi
	docker run -v .:/workspace -it --name rustypi local/rustypi:latest

docker:
	docker start -i rustypi	

PREREQ=target/aarch64-unknown-linux-gnu/release/sparkybiasd
deploy:
	docker container start rustypi
	docker container exec -it rustypi \
			/bin/bash -c "source ~/.bashrc && cargo build --release --target aarch64-unknown-linux-gnu"
	@echo "Check if file exists"
		scp ${PREREQ} asu@primecambias.local:~/
		ssh asu@primecambias.local '/bin/bash -c /home/asu/sparkybiasd'

app:
	cargo build

clean:
	cargo clean
