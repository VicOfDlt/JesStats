from motor import motor_tornado
import os

client = motor_tornado.MotorClient(
    os.environ["mongodb"]
)
db = client["jesbot"]

token = os.environ['token']
