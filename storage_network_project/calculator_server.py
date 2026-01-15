import grpc
from concurrent import futures
import calculator_pb2
import calculator_pb2_grpc

class CalculatorServiceServicer(calculator_pb2_grpc.CalculatorServiceServicer):

    def Add(self, request, context):
        result = request.num1 + request.num2
        return calculator_pb2.CalculatorResponse(
            result=result,
            operation="addition",
            success=True
        )

    def Subtract(self, request, context):
        result = request.num1 - request.num2
        return calculator_pb2.CalculatorResponse(
            result=result,
            operation="subtraction",
            success=True
        )

    def Multiply(self, request, context):
        result = request.num1 * request.num2
        return calculator_pb2.CalculatorResponse(
            result=result,
            operation="multiplication",
            success=True
        )

    def Divide(self, request, context):
        if request.num2 == 0:
            return calculator_pb2.CalculatorResponse(
                result=0,
                operation="division",
                success=False,
                error="Cannot divide by zero"
            )
        result = request.num1 / request.num2
        return calculator_pb2.CalculatorResponse(
            result=result,
            operation="division",
            success=True
        )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    calculator_pb2_grpc.add_CalculatorServiceServicer_to_server(
        CalculatorServiceServicer(), server
    )
    server.add_insecure_port('[::]:9000')

    print("🧮 Calculator gRPC Server running on port 9000...")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()