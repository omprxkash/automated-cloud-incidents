.PHONY: test lint run-mock examples check clean

test:
	pytest tests/ -v

lint:
	python -m py_compile src/config.py src/clients/*.py src/mock/mock_cloud.py src/cli.py

run-mock:
	OPENSTACK_MOCK=1 python -m src.cli server list

examples:
	OPENSTACK_MOCK=1 python examples/launch_vm.py
	OPENSTACK_MOCK=1 python examples/create_network.py
	OPENSTACK_MOCK=1 python examples/attach_volume.py
	OPENSTACK_MOCK=1 python examples/upload_object.py

check: test lint

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache
