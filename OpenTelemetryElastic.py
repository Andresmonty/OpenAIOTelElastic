import openai
from flask import Flask
import monitor  # Import the module
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
import urllib
import argparse
import requests
import os

from opentelemetry import trace
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.requests import RequestsInstrumentor


# Service name is required for most backends
resource = Resource(attributes={
    SERVICE_NAME: "OpenAIOpenTelemetryElastic"
})

provider = TracerProvider(resource=resource)
processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT'),
        headers="Authorization=Bearer%20"+os.getenv('OTEL_EXPORTER_OTLP_AUTH_HEADER')))

provider.add_span_processor(processor)
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)
RequestsInstrumentor().instrument()



# Initialize Flask app and instrument it
app = Flask(__name__)

# Set OpenAI API key
openai.api_key = os.getenv('OPEN_AI_KEY')

@app.route("/")
@tracer.start_as_current_span("do_work")
def completion():
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=f"Act as a DevOps Engineer and Write a python script to automate the provisioning of an EC2 instance using terraform on AWS. Provide only code, no text",
        max_tokens=75,
        temperature=0
    )

    return response.choices[0].text.strip()
    return response.json()["choices"][0]["text"]
    
if __name__ == "__main__":
    app.run(host="localhost", port=8888, debug=False)