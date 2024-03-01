from datetime import datetime

#  User Schema
user_schema = {
    "name": "String, required",
    "email": "String, required, unique",
    "password": "String, required"
}

# Task Schema
task_schema = {
    "title": "String, required",
    "description": "String",
    "priority": "Integer, default: 1",  # Assuming 1 is the lowest priority
    "deadline": "DateTime",
    "status": "String, default: 'pending'",  # e.g., 'pending', 'completed'
    "completed": "Boolean, default: False",
    "user_id": "ObjectId, required"  # To associate the task with a user
}
