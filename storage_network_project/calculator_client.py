import grpc
import sys
import calculator_pb2
import calculator_pb2_grpc

def run_calculator(operation, num1, num2):
    with grpc.insecure_channel('localhost:9000') as channel:
        stub = calculator_pb2_grpc.CalculatorServiceStub(channel)
        request = calculator_pb2.CalculatorRequest(num1=num1, num2=num2)

        if operation == 'add':
            response = stub.Add(request)
        elif operation == 'subtract':
            response = stub.Subtract(request)
        elif operation == 'multiply':
            response = stub.Multiply(request)
        elif operation == 'divide':
            response = stub.Divide(request)
        else:
            print("Invalid operation")
            return

        if response.success:
            print(f"Result of {operation}: {response.result}")
        else:
            print(f"Error: {response.error}")

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Usage: python calculator_client.py <operation> <num1> <num2>")
        print("Operations: add, subtract, multiply, divide")
        print("Example: python calculator_client.py add 5 3")
        sys.exit(1)

    operation = sys.argv[1]
    num1 = float(sys.argv[2])
    num2 = float(sys.argv[3])

    run_calculator(operation, num1, num2)