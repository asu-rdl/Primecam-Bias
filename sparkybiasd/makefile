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
	@echo "stop        - Stop the docker container"
	@echo "deploy      - starts docker container, builds target, "
	@echo "              uploads to the raspberry pi and runs it"
	@echo "app         - builds target normally"
	@echo "clean       - cleans up build artifacts"
	@echo "superclean  - This deletes the build artifacts as well as "
	@echo "              the docker *CONTAINER* AND *IMAGE*"
	@echo "-----------------------------------------------------------"

dockerimage:
	docker build . -t local/rustypi
	docker container create -i -t -v .:/workspace --name rustypi local/rustypi:latest

docker:
	docker start -i rustypi	

PREREQ=target/aarch64-unknown-linux-gnu/release/sparkybiasd
deploy:
	docker container start rustypi
	docker container exec -it rustypi \
			/bin/bash -c "source ~/.bashrc && cargo build --release --target aarch64-unknown-linux-gnu"
	@echo "Scp and run the binary from the raspberry pi"
	@echo ""
	scp ${PREREQ} asu@primecambias.local:~/
	ssh asu@primecambias.local '/bin/bash -c "/home/asu/sparkybiasd --help"'
	@echo " "
	@echo "The container was left running, use make stop to close it"
	@echo " "

stop:
	@echo " "
	@echo "Stopping container, this may take a moment..."
	@echo " "
	docker container stop rustypi

app:
	cargo build

clean:
	cargo clean

superclean: clean
	docker container rm rustypi
	docker image rm local/rustypi
	rm -f ./Cargo.lock
