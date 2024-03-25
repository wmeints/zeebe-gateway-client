import logging
import zeebe_gateway_client as gwc

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)


def complete_task(client, task):
    client.complete_job(task, {})


client = gwc.GatewayClient(worker_name="test", host="localhost", port=26500)
client.subscribe("io.camunda.zeebe:userTask", complete_task)
