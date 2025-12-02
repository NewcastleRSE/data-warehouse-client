sudo docker run -it --network=docker-suite_default \
	-v "../../../..:/data_warehouse_client" \
	-v "./test-override:/client/test-override" \
	-v "../../outputs:/client/outputs" \
	docker-suite-client /bin/bash
