# Zeebe gateway client package

The Zeebe gateway client package provides access to the Zeebe gateway that's part of the Camunda platform.
The goal is primarily to provide access to the activated job stream so we can dispatch these as tasks in our own
software.

## Getting started

To listen for activated jobs in Camunda you'll need the following code:

```python
from zeebe_gateway_client import GatewayClient

client = GatewayClient(worker_name="test_worker", host="localhost", port=26500)
client.subscribe("io.camunda.zeebe:userTask", lambda x: print(x))
```

This code will connect to your locally running Zeebe gateway. It will then listen for user tasks and print the task
instance information on the terminal.

**Note:** If you need to run multiple subscriptions, you should run each of them on their own thread!

The task instance information provided contains the following properties:

| Property        | Description                                                                                      |
| --------------- | ------------------------------------------------------------------------------------------------ |
| key: int        | The unique identifier of the job                                                                 |
| task_type: str  | The type of job that was activated.                                                              |
| task_id: str    | The identifier of the task. This is set in the ID field of the property inspector in the modeler |
| process_id: str | The ID of the process that hosts the job                                                         |
| retries: int    | The number of remaining retries for the job                                                      |
| variables: dict | A dictionary containing variables provided from the workflow                                     |

You can complete jobs with the following code:

```python
client.complete_job(task_instance, variables)
```

You provide a task instance you received through the callback in the subscribe call.
The `complete_job` method accepts a dictionary containing output variables of the job that need to flow back to the workflow.

When a job fails, you can use this code:

```python
client.fail_job(task_instance, error_message, remaining_retries)
```

You provide a task instance you received through the callback in the subscribe call in this method. The method also accepts
an error message and the remaining number of retries for the job. When the job reaches zero retries, the process is stopped.

## Development

### Generating the gRPC protocol stubs

This package is based off [the official protobuf file](https://github.com/camunda/zeebe/blob/main/zeebe/gateway-protocol/src/main/proto/gateway.proto) published by Camunda.
Use the following command to generate the necessary protocol stubs in Python:

```bash
python -m grpcio_tools.protoc -I ./protos/ --python_out=./src/zeebe_gateway_client/ --grpc_python_out=./src/zeebe_gateway_client/ ./protos/zeebe-gateway.proto
```

After generating the python files, make sure to update `src/zeebe_gateway_client/zeebe_gateway_pb2_grpc.py` file to change the import to `zeebe_gateway_pb2` module
so it's relative to the root of the package. In short, it should look like this:

```python
import zeebe_gateway_client.zeebe_gateway_pb2 as zeebe__gateway__pb2
```
