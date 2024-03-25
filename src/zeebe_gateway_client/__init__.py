from typing import Callable
from zeebe_gateway_client.zeebe_gateway_pb2_grpc import GatewayStub
import zeebe_gateway_client.zeebe_gateway_pb2 as protocol
import grpc
from dataclasses import dataclass
import json


@dataclass
class TaskInstance:
    """
    A task instance is used to represent a task that is available to be completed or failed. The task instance contains
    the key of the task, the type of task, the ID of the task, the ID of the process instance, the number of retries.

    Attributes:
    -----------
    key: int
        The key of the task.
    task_type: str
        The type of task.
    task_id: str
        The ID of the task.
    process_id: str
        The ID of the process instance.
    retries: int
        The number of retries remaining for the task.
    variables: dict
        The variables associated with the task.
    """

    key: int
    task_type: str
    task_id: str
    process_id: str
    retries: int
    variables: dict


class GatewayClient:
    """
    Provides access to the Zeebe gateway. The gateway client can be used to subscribe to job streams, complete jobs,
    and fail jobs.
    """

    _stub: GatewayStub
    _channel: grpc.Channel
    _worker_name: str
    host: str
    port: int

    def __init__(self, worker_name: str, host: str, port: int):
        self.host = host
        self.port = port
        self._worker_name = worker_name

        self._channel = grpc.insecure_channel(f"{host}:{port}")
        self._stub = GatewayStub(self._channel)

    def subscribe(self, job_type: str, callback: Callable):
        """
        Subscribes to a job stream for a configured job type. When a new job of the specified type is available, the
        callback function is called with the job data. The callback function should accept two arguments, the first
        argument will contain the GatewayClient instance that is subscribed to the job stream, and the second argument
        will contain the job data.

        Parameters:
        -----------
        task_type: str
            The type of task to subscribe to.
        callback: Callable
            The function to call when a new task of the specified type is available.
        """
        request = protocol.StreamActivatedJobsRequest(
            type=job_type, worker=self._worker_name, timeout=300
        )

        for job_data in iter(self._stub.StreamActivatedJobs(request)):
            task_instance = TaskInstance(
                job_data.key,
                job_data.type,
                job_data.elementId,
                job_data.processInstanceKey,
                job_data.retries,
                json.loads(job_data.variables),
            )

            callback(self, task_instance)

    def disconnect(self):
        """
        Disconnects the client from the gateway.
        """
        if self._channel is not None:
            self._channel.close()

    def complete_job(self, task_instance: TaskInstance, variables: dict):
        """
        Completes a job on the gateway. The job will be marked as completed and the workflow will continue. The variables
        parameter should be a dictionary containing the variables to update in the workflow.

        Parameters:
        -----------
        task_instance: TaskInstance
            The task instance to complete.
        variables: dict
            The variables to update in the workflow.
        """
        request_data = protocol.CompleteJobRequest(
            jobKey=task_instance.key, variables=json.dumps(variables)
        )

        self._stub.CompleteJob(request_data)

    def fail_job(
        self, task_instance: TaskInstance, error_message: str, remaining_retries: int
    ):
        """
        Marks a job as failed on the gateway. The job will be retried according to the retry settings configured in the
        workflow. If the job has no retries remaining, the job will be marked as failed and the workflow will continue
        according to the error handling configuration.

        Parameters:
        -----------
        task_instance: TaskInstance
            The task instance to mark as failed.
        error_message: str
            The error message to include with the failed job.
        remaining_retries: int
            The number of retries remaining for the job.
        """
        request_data = protocol.FailJobRequest(
            jobKey=task_instance.key,
            errorMessage=error_message,
            retries=remaining_retries,
        )

        self._stub.FailJob(request_data)
